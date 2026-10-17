import React from 'react'
import { formatPaiseToINR } from '../../lib/formatters'

export type MetricAccent = 'emerald' | 'blue' | 'amber' | 'red' | 'neutral'

interface MetricCardProps {
  label: string
  amountPaise: number
  icon: React.ElementType
  accent?: MetricAccent
  statusText?: string
  subtext?: string
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  amountPaise,
  icon: Icon,
  accent = 'neutral',
  statusText,
  subtext,
}) => {
  const accentStyles: Record<MetricAccent, { iconBg: string; iconColor: string; borderColor?: string }> = {
    emerald: { iconBg: 'bg-[#E8F7EF]', iconColor: 'text-[#16A36A]' },
    blue: { iconBg: 'bg-[#EDF2FD]', iconColor: 'text-[#6D8FE8]' },
    amber: { iconBg: 'bg-[#FEF6EB]', iconColor: 'text-[#E9A23B]' },
    red: { iconBg: 'bg-[#FDF0F0]', iconColor: 'text-[#DC5555]' },
    neutral: { iconBg: 'bg-[#F0F2F5]', iconColor: 'text-[#737780]' },
  }

  const { iconBg, iconColor } = accentStyles[accent]

  return (
    <div className="bg-white rounded-xl border border-[#E8EAED] p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)] flex flex-col justify-between hover:border-[#D1D5DB] transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-[#737780] tracking-tight">{label}</span>
        <div className={`w-8 h-8 rounded-lg ${iconBg} ${iconColor} flex items-center justify-center shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl lg:text-[28px] font-bold text-[#17191C] tabular-nums tracking-tight">
          {formatPaiseToINR(amountPaise)}
        </span>
      </div>

      <div className="mt-3 pt-3 border-t border-[#F0F2F5] flex items-center justify-between text-xs">
        {statusText && <span className="font-semibold text-[#17191C]">{statusText}</span>}
        {subtext && <span className="text-[#737780]">{subtext}</span>}
      </div>
    </div>
  )
}
