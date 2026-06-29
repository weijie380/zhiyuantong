import { useState } from 'react'

export default function SchoolTable({ rows, columns, onRowClick, emptyText = '无数据' }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const sorted = sortKey
    ? [...rows].sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey]
        if (av == null) return 1
        if (bv == null) return -1
        const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv), 'zh')
        return sortDir === 'asc' ? cmp : -cmp
      })
    : rows

  const onSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  if (rows.length === 0) {
    return <div style={{ padding: 'var(--sp-6)', textAlign: 'center', color: 'var(--color-muted-foreground)' }}>{emptyText}</div>
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-14)' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
            {columns.map(c => (
              <th key={c.key} onClick={() => c.sortable && onSort(c.key)}
                style={{
                  textAlign: 'left', padding: 'var(--sp-2) var(--sp-3)',
                  cursor: c.sortable ? 'pointer' : 'default', color: 'var(--color-muted-foreground)',
                  fontWeight: 500, whiteSpace: 'nowrap',
                }}>
                {c.label}
                {c.sortable && sortKey === c.key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={r.id || i} onClick={() => onRowClick && onRowClick(r)}
              style={{
                borderBottom: '1px solid var(--color-border)', cursor: onRowClick ? 'pointer' : 'default',
                transition: `background var(--dur-fast) var(--ease)`,
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--color-muted)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              {columns.map(c => (
                <td key={c.key} style={{ padding: 'var(--sp-2) var(--sp-3)', whiteSpace: 'nowrap',
                  fontVariantNumeric: c.numeric ? 'tabular-nums' : 'normal' }}>
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
