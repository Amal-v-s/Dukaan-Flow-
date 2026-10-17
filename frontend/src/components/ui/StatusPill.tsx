import React from 'react'

export type PillVariant = 'safe' | 'warning' | 'alert' | 'neutral' | 'info'

interface StatusPillProps {
  label: string
  variant?: PillVariant
  className?: string
}

export const StatusPill: React.FC<StatusPillProps> = ({
  label,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles: Record<PillVariant, string> = {
    safe: 'bg-[#E8F7EF] text-[#16A36A] border-[#A7F3D0]',
    warning: 'bg-[#FEF6EB] text-[#E9A23B] border-[#FDE68A]',
    alert: 'bg-[#FDF0F0] text-[#DC5555] border-[#FECACA]',
    info: 'bg-[#EDF2FD] text-[#6D8FE8] border-[#BFDBFE]',
    neutral: 'bg-[#F0F2F5] text-[#737780] border-[#E5E7EB]',
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase border ${variantStyles[variant]} ${className}`}
    >
      {label}
    </span>
  )
}
