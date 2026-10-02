export const stages = [
  ['Order created', 'ORD-1042', 'done'],
  ['Picking wave', 'W-43175', 'done'],
  ['AI priority', 'Critical', 'done'],
  ['Picking complete', '3 locations', 'done'],
  ['Dispatch unit', 'DU-03', 'done'],
  ['Route & stop', 'R-00143 · B-24.2C', 'done'],
  ['Delivery risk', 'Check live model', 'current'],
  ['WhatsApp', 'Awaiting availability', 'pending'],
  ['Re-rank & deliver', 'Outcome pending', 'pending'],
]

export function Heading({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  )
}

export function Panel({ children, className = '' }) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function Result({ value }) {
  return value && (
    <Panel className="result-wrap">
      <h3>Backend response</h3>
      <pre className="result-box">{JSON.stringify(value, null, 2)}</pre>
    </Panel>
  )
}

export function Badge({ children, tone = 'blue' }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

export function Journey({ compact = false }) {
  return (
    <Panel className={`journey-panel ${compact ? 'compact' : ''}`}>
      <div className="panel-head">
        <div>
          <p className="eyebrow">CONNECTED SHIPMENT</p>
          <h2>
            ORD-1042 <span className="muted">· Customer #1042</span>
          </h2>
        </div>
        <Badge tone="orange">IN DELIVERY PLANNING</Badge>
      </div>
      <div className="journey-track">
        {stages.map(([name, detail, state], i) => (
          <div className={`journey-stage ${state}`} key={name}>
            <div className="stage-marker">
              {state === 'done' ? '✓' : String(i + 1).padStart(2, '0')}
            </div>
            <div className="stage-copy">
              <b>{name}</b>
              <span>{detail}</span>
            </div>
            {i < stages.length - 1 && <div className="stage-connector" />}
          </div>
        ))}
      </div>
      <div className="journey-foot">
        <span>
          Warehouse handoff <b>DU-03 → R-00143</b>
        </span>
        <a href="/journey">Open complete shipment journey →</a>
      </div>
    </Panel>
  )
}
