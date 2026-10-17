import React, { useState } from 'react'
import { CheckCircle2, FileUp, Download, AlertTriangle } from 'lucide-react'

type Preview = { batch_id: string; status: string; row_count: number; valid_row_count: number; invalid_row_count: number; file_name: string; created_record_ids?: string[]; preview: Array<{ row_number: number; valid: boolean; errors: string[]; normalized: Record<string, unknown> }> }

export const ImportWizardPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Preview | null>(null)
  const [confirmedReview, setConfirmedReview] = useState(false)
  const [result, setResult] = useState<Preview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState<'choose' | 'preview' | 'result'>('choose')
  const input = 'w-full rounded-lg border border-[#D8DCE2] px-3 py-2 text-sm focus:outline-none focus:border-[#16A36A]'
  const card = 'rounded-xl border border-[#E8EAED] bg-white p-5 shadow-sm'

  const chooseFile = (selected: File | null) => {
    setError(''); setPreview(null); setResult(null); setConfirmedReview(false)
    if (!selected) { setFile(null); return }
    if (!selected.name.toLowerCase().endsWith('.csv')) { setError('Choose a .csv file.'); setFile(null); return }
    if (selected.size > 1_000_000) { setError('The file must be smaller than one megabyte.'); setFile(null); return }
    setFile(selected)
  }
  const makePreview = async () => {
    if (!file) { setError('Select an expense CSV first.'); return }
    setBusy(true); setError('')
    try {
      const csv_text = await file.text()
      const res = await fetch('/api/v1/imports/preview', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ import_type: 'expenses', file_name: file.name, csv_text }) })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.error?.message || data?.detail || 'Could not validate CSV')
      setPreview(data); setStep('preview')
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not read or validate the file') }
    finally { setBusy(false) }
  }
  const confirmImport = async () => {
    if (!preview || !confirmedReview || preview.invalid_row_count) return
    if (!window.confirm(`Import ${preview.valid_row_count} expense rows into the ledger?`)) return
    setBusy(true); setError('')
    try {
      const res = await fetch(`/api/v1/imports/${preview.batch_id}/confirm`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.error?.message || data?.detail || 'Import failed')
      setResult(data); setStep('result')
    } catch (e) { setError(e instanceof Error ? e.message : 'Import failed') }
    finally { setBusy(false) }
  }
  const downloadErrors = () => {
    if (!preview) return
    const lines = ['row_number,errors', ...preview.preview.filter((r) => !r.valid).map((r) => `${r.row_number},"${r.errors.join('; ').replaceAll('"', '""')}"`)]
    const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'dukaanflow-import-errors.csv'; anchor.click(); URL.revokeObjectURL(url)
  }

  return <div className="mx-auto max-w-4xl space-y-5">
    <div><div className="flex items-center gap-2 text-sm font-semibold"><span className={step === 'choose' ? 'text-[#16A36A]' : 'text-[#737780]'}>1. Choose file</span><span>→</span><span className={step === 'preview' ? 'text-[#16A36A]' : 'text-[#737780]'}>2. Validate & preview</span><span>→</span><span className={step === 'result' ? 'text-[#16A36A]' : 'text-[#737780]'}>3. Confirm & result</span></div></div>
    {error && <div role="alert" className="rounded-lg border border-[#FECACA] bg-[#FDF0F0] p-3 text-sm text-[#B91C1C]">{error}</div>}
    {step === 'choose' && <section className={`${card} space-y-4`}><h2 className="text-lg font-bold">Import expense records</h2><p className="text-sm text-[#737780]">CSV import is limited to expenses. Preview and validate every row before confirming; no ledger changes happen during preview.</p><a className="inline-flex items-center gap-2 text-sm font-semibold text-[#496BC3] underline" href="/api/v1/imports/templates/expenses"><Download className="h-4 w-4" />Download CSV template</a><label className="block text-sm font-semibold">Choose CSV file<input className={`${input} mt-2`} type="file" accept=".csv,text/csv" onChange={(e) => chooseFile(e.target.files?.[0] || null)} /></label>{file && <p className="text-xs text-[#737780]">Selected: {file.name} · {file.size.toLocaleString()} bytes · limit one megabyte / 400 rows</p>}<div className="rounded-lg bg-[#F7F8FA] p-3 text-xs text-[#737780]"><strong>Required columns:</strong> title, category, amount_inr, expense_date. Optional: payment_method, notes. Dates must use YYYY-MM-DD; amounts may have up to two decimals.</div><button disabled={!file || busy} onClick={() => void makePreview()} className="rounded-lg bg-[#16A36A] px-4 py-2 text-sm font-bold text-white disabled:opacity-50"><FileUp className="mr-1 inline h-4 w-4" />{busy ? 'Validating…' : 'Validate and preview'}</button></section>}
    {step === 'preview' && preview && <section className={`${card} space-y-4`}><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-bold">Review import preview</h2><p className="text-sm text-[#737780]">{preview.file_name} · {preview.valid_row_count} valid · {preview.invalid_row_count} invalid</p></div>{preview.invalid_row_count > 0 && <button onClick={downloadErrors} className="rounded-md border px-3 py-2 text-xs font-semibold">Download error report</button>}</div>{preview.invalid_row_count > 0 && <div className="flex gap-2 rounded-lg bg-[#FEF6EB] p-3 text-sm text-[#915B08]"><AlertTriangle className="h-4 w-4 shrink-0" /><p>Correct invalid rows in the source CSV and upload a new preview. This batch cannot be confirmed while rows are invalid.</p></div>}<div className="max-h-[430px] overflow-auto rounded-lg border"><table className="w-full min-w-[560px] text-left text-xs"><thead className="sticky top-0 bg-[#F7F8FA]"><tr><th className="p-2">Row</th><th className="p-2">Title</th><th className="p-2">Category</th><th className="p-2">Amount</th><th className="p-2">Status / issues</th></tr></thead><tbody>{preview.preview.map((r) => <tr className="border-t" key={r.row_number}><td className="p-2">{r.row_number}</td><td className="p-2">{String(r.normalized.title || '')}</td><td className="p-2">{String(r.normalized.category || '')}</td><td className="p-2">{String(r.normalized.amount_paise || 0)} paise</td><td className={`p-2 ${r.valid ? 'text-[#16A36A]' : 'text-[#B91C1C]'}`}>{r.valid ? 'Valid' : r.errors.join('; ')}</td></tr>)}</tbody></table></div><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={confirmedReview} onChange={(e) => setConfirmedReview(e.target.checked)} disabled={preview.invalid_row_count > 0} /><span>I reviewed the preview and confirm these validated expenses should be added to the cashbook.</span></label><div className="flex gap-2"><button disabled={busy || preview.invalid_row_count > 0 || !confirmedReview} onClick={() => void confirmImport()} className="rounded-lg bg-[#16A36A] px-4 py-2 text-sm font-bold text-white disabled:opacity-50">{busy ? 'Importing…' : 'Confirm import'}</button><button onClick={() => { setStep('choose'); setPreview(null); setConfirmedReview(false) }} className="rounded-lg border px-4 py-2 text-sm">Choose another file</button></div></section>}
    {step === 'result' && result && <section className={`${card} space-y-3`}><CheckCircle2 className="h-8 w-8 text-[#16A36A]" /><h2 className="text-lg font-bold">Import complete</h2><p className="text-sm text-[#737780]">Imported {result.created_record_ids?.length ?? result.valid_row_count} expense rows. Batch ID: {result.batch_id}</p><button onClick={() => { setStep('choose'); setFile(null); setPreview(null); setResult(null); setConfirmedReview(false) }} className="rounded-lg bg-[#16A36A] px-4 py-2 text-sm font-bold text-white">Start another import</button></section>}
  </div>
}
