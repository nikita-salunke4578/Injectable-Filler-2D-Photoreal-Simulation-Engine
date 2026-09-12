export function formatMl(value: number): string {
  return `${value.toFixed(1)}mL`
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`
}

export function formatCurrencyRange(range: [number, number]): string {
  const fmt = (n: number) =>
    n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  return `${fmt(range[0])} – ${fmt(range[1])}`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}
