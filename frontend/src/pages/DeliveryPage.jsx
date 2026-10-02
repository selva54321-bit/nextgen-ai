import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { Badge, Heading, Panel, Result } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DeliveryPage() {
  const [stopId, setStopId] = useState('B-24.2C')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  const check = async (e) => {
    e?.preventDefault()
    setBusy(true)
    setResult(null)

    try {
      setResult(await api.stopRisk(stopId))
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell title="Routes & risk">
      <Heading
        eyebrow="LAYER 2 · LAST MILE"
        title="Route and delivery risk"
        description="Inspect a route stop, retrieve its live failure probability, and connect the result to customer availability."
      />

      <div className="route-layout">
        <Panel className="route-map">
          <div className="panel-head">
            <div>
              <p className="eyebrow">ROUTE R-00143</p>
              <h2>Delivery sequence</h2>
            </div>
            <Badge tone="blue">IN TRANSIT · EXAMPLE</Badge>
          </div>

          <div className="route-line">
            {[
              ['1', 'Origin', 'done'],
              ['2', 'B-21.1A', 'done'],
              ['3', 'B-24.2C', 'risk'],
              ['4', 'P-12.3C', 'pending'],
              ['5', 'P-13.2A', 'pending'],
            ].map(([n, label, state]) => (
              <button className={`route-stop ${state}`} key={n} type="button" onClick={() => label.includes('-') && setStopId(label)}>
                <span>{n}</span>
                <b>{label}</b>
                <small>{state === 'risk' ? 'Selected stop' : state === 'done' ? 'Completed' : 'Upcoming'}</small>
              </button>
            ))}
          </div>

          <div className="legend">
            <span><i className="green-dot" />Complete</span>
            <span><i className="orange-dot" />Selected stop</span>
            <span><i className="gray-dot" />Upcoming</span>
          </div>
        </Panel>

        <Panel>
          <p className="eyebrow">STOP RISK MODEL</p>
          <h2>Assess failure probability</h2>
          <p className="panel-copy">Risk output is retrieved from the delivery service; no probability is fabricated in the interface.</p>
          <form onSubmit={check} className="inline-form">
            <label>
              Stop ID
              <input required value={stopId} onChange={(e) => setStopId(e.target.value)} />
            </label>
            <button className="button primary" disabled={busy} type="submit">
              {busy ? 'Checking…' : 'Check live risk'}
            </button>
          </form>
          <div className="risk-empty">
            <span>◎</span>
            <b>Risk result will appear below</b>
            <small>Uses configured delivery model endpoint</small>
          </div>
          <Link className="text-link" to="/whatsapp">Open customer interaction →</Link>
        </Panel>
      </div>

      <Panel className="model-note">
        <h2>Risk context</h2>
        <p>Route, station, capacity, zone, stop and package counts, service time, time window, and historical outcomes may contribute to the trained model result.</p>
      </Panel>

      <Result value={result} />
    </Shell>
  )
}
