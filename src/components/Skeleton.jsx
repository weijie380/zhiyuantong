export default function Skeleton({ height = 20, width = '100%', radius }) {
  return (
    <div style={{
      height, width, borderRadius: radius || 'var(--radius-sm)',
      background: 'linear-gradient(90deg, var(--color-muted) 25%, var(--color-border) 50%, var(--color-muted) 75%)',
      backgroundSize: '200% 100%', animation: 'zyt-shimmer 1.4s infinite',
    }} />
  )
}
