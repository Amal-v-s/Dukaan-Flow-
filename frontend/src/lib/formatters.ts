/**
 * Frontend formatters for DukaanFlow adhering to DESIGN.md and 06_ENGINEERING_RULES.md:
 * - Indian currency grouping (e.g., ₹84,500, ₹1,48,200).
 * - Exact integer paise calculations; no binary float conversions.
 */

export function formatPaiseToINR(paise: number, includeSymbol = true): string {
  if (typeof paise !== 'number' || isNaN(paise)) {
    return includeSymbol ? '₹0' : '0'
  }

  const isNegative = paise < 0
  const absPaise = Math.abs(Math.round(paise))

  const rupees = Math.floor(absPaise / 100)
  const remPaise = absPaise % 100

  const s = rupees.toString()
  let formattedRupees: string

  if (s.length <= 3) {
    formattedRupees = s
  } else {
    const lastThree = s.substring(s.length - 3)
    let remaining = s.substring(0, s.length - 3)
    const groups: string[] = []
    while (remaining.length > 2) {
      groups.unshift(remaining.substring(remaining.length - 2))
      remaining = remaining.substring(0, remaining.length - 2)
    }
    if (remaining.length > 0) {
      groups.unshift(remaining)
    }
    formattedRupees = groups.join(',') + ',' + lastThree
  }

  const fractionStr = remPaise > 0 ? `.${remPaise.toString().padStart(2, '0')}` : ''
  const prefix = isNegative ? '-' : ''
  const symbol = includeSymbol ? '₹' : ''

  return `${prefix}${symbol}${formattedRupees}${fractionStr}`
}

export function parseINRToPaise(inrStr: string): number {
  if (!inrStr || !inrStr.trim()) return 0
  const cleaned = inrStr.replace(/[^0-9.-]/g, '')
  if (!cleaned) return 0

  const parts = cleaned.split('.')
  const rupees = parseInt(parts[0] || '0', 10)
  let paise = 0

  if (parts.length > 1) {
    const dec = (parts[1] + '00').substring(0, 2)
    paise = parseInt(dec, 10)
  }

  const isNeg = cleaned.startsWith('-')
  const total = Math.abs(rupees) * 100 + paise
  return isNeg ? -total : total
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}
