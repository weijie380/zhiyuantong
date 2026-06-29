// Pagination — 分页栏组件
// total: 总条数, page: 当前页(1起), pageSize: 每页条数, onChange: 翻页回调
export default function Pagination({ total, page, pageSize, onChange }) {
  const totalPages = Math.ceil(total / pageSize)
  if (totalPages <= 1) return null

  // 生成页码列表，最多显示 7 个，超出用省略号
  const pages = []
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i)
  } else {
    pages.push(1)
    if (page > 3) pages.push('...')
    const start = Math.max(2, page - 1)
    const end = Math.min(totalPages - 1, page + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (page < totalPages - 2) pages.push('...')
    pages.push(totalPages)
  }

  const btnStyle = (active) => ({
    minWidth: 32, height: 32, padding: '0 var(--sp-2)',
    border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
    background: active ? 'var(--color-primary)' : 'var(--color-card)',
    color: active ? 'var(--color-on-primary)' : 'var(--color-foreground)',
    fontWeight: active ? 600 : 400, fontSize: 'var(--fs-14)',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', minHeight: 32,
  })

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: 'var(--sp-1)', padding: 'var(--sp-4)', flexWrap: 'wrap' }}>
      <button style={btnStyle(false)} onClick={() => onChange(page - 1)} disabled={page <= 1}
        aria-label="上一页">
        ‹
      </button>
      {pages.map((p, i) =>
        p === '...'
          ? <span key={`e${i}`} style={{ padding: '0 var(--sp-1)', color: 'var(--color-muted-foreground)' }}>…</span>
          : <button key={p} style={btnStyle(p === page)} onClick={() => onChange(p)}>{p}</button>
      )}
      <button style={btnStyle(false)} onClick={() => onChange(page + 1)} disabled={page >= totalPages}
        aria-label="下一页">
        ›
      </button>
      <span style={{ marginLeft: 'var(--sp-3)', fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>
        共 {total} 条 / {totalPages} 页
      </span>
    </div>
  )
}
