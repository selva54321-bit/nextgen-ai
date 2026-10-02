import { useState } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel, Result } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DispatchPage() {
  const [orderId, setOrderId] = useState('')
  const [unitId, setUnitId] = useState('')
  const [simulation, setSimulation] = useState(true)
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setResult(null)

    try {
      setResult(
        file
          ? await api.dispatchBatch(file)
          : await api.dispatchPlan({
              orderIds: [orderId],
              dispatchUnitId: unitId,
              simulationMode: simulation,
            }),
      )
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell title="Dispatch units">
      <Heading
        eyebrow="WAREHOUSE HANDOFF"
        title="Dispatch unit control"
        description="Connect ready goods to a dispatch unit and review the service's dispatch plan."
      />

      <div className="unit-grid">
        {[
          ['DU-01', 'AVAILABLE', '78%', '12'],
          ['DU-02', 'LOADING', '91%', '18'],
          ['DU-03', 'DISPATCHED', '84%', '21'],
        ].map(([id, status, capacity, packages]) => (
          <Panel key={id} className="unit-card">
            <div className="panel-head">
              <h2>{id}</h2>
              <Badge tone={status === 'AVAILABLE' ? 'green' : status === 'LOADING' ? 'orange' : 'blue'}>{status}</Badge>
            </div>
            <div className="capacity">
              <span style={{ width: capacity }} />
            </div>
            <div className="unit-meta">
              <span>
                Capacity <b>{capacity}</b>
              </span>
              <span>
                Packages <b>{packages}</b>
              </span>
            </div>
            <small className="demo-label">Example dispatch unit</small>
          </Panel>
        ))}
      </div>

      <Panel className="form-panel">
        <form onSubmit={submit}>
          <p className="eyebrow">BACKEND DISPATCH PLAN</p>
          <h2>Create or simulate a plan</h2>
          <p className="panel-copy">Use the connected dispatch endpoint. Batch plans accept a CSV or Excel route/stop file.</p>

          <div className="field-grid">
            <label>
              Order ID
              <input required={!file} value={orderId} onChange={(e) => setOrderId(e.target.value)} placeholder="ORD-1042" />
            </label>
            <label>
              Dispatch unit ID
              <input required={!file} value={unitId} onChange={(e) => setUnitId(e.target.value)} placeholder="DU-03" />
            </label>
          </div>

          <label className="check-row">
            <input type="checkbox" checked={simulation} onChange={(e) => setSimulation(e.target.checked)} />
            Simulation mode
          </label>

          <label className="file-picker">
            Optional batch dataset
            <input type="file" accept=".csv,.xls,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>

          <button className="button primary" disabled={busy} type="submit">
            {busy ? 'Creating plan…' : file ? 'Create batch plan' : 'Create dispatch plan'}
          </button>
        </form>
      </Panel>

      <Result value={result} />
    </Shell>
  )
}
