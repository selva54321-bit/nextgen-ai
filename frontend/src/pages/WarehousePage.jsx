import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { Badge, Heading, Panel, Result } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function WarehousePage() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  const run = async (action) => {
    setBusy(true)
    setResult(null)

    try {
      if (action === 'upload') {
        if (!file) throw new Error('Choose a CSV or Excel file first.')
        setResult(await api.warehouseUpload(file))
      } else if (action === 'simulation') {
        setResult(await api.warehouseSimulation())
      } else {
        setResult(await api.taskRanking())
      }
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell title="Warehouse & priority">
      <Heading
        eyebrow="LAYER 1 · WAREHOUSE"
        title="Goods, picking and priority"
        description="Prepare warehouse data, inspect picking operations, and move ready orders toward dispatch."
      />

      <div className="warehouse-banner">
        <div>
          <p className="eyebrow">ACTIVE PICKING WAVE</p>
          <h2>
            W-43175 <Badge tone="red">CRITICAL PRIORITY</Badge>
          </h2>
          <p>Example shipment ORD-1042 · 3 warehouse locations · dispatch handoff DU-03</p>
        </div>
        <Link className="button secondary" to="/journey">View order journey</Link>
      </div>

      <div className="work-grid">
        <Panel>
          <div className="section-title">
            <span className="step-num">01</span>
            <h2>Upload warehouse dataset</h2>
          </div>
          <p className="panel-copy">Validate the customer orders, product, storage location, strategy, and navigation inputs.</p>
          <label className="file-picker">
            Choose CSV or Excel dataset
            <input type="file" accept=".csv,.xls,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          {file && <p className="file-name">Selected: {file.name}</p>}
          <button className="button primary" disabled={busy} type="button" onClick={() => run('upload')}>
            {busy ? 'Working…' : 'Upload and validate'}
          </button>
        </Panel>

        <Panel>
          <div className="section-title">
            <span className="step-num">02</span>
            <h2>Picking operations</h2>
          </div>
          <p className="panel-copy">Run the warehouse simulation or ask the service for its current task ranking.</p>
          <div className="button-stack">
            <button className="button primary" disabled={busy} type="button" onClick={() => run('simulation')}>
              Run warehouse simulation
            </button>
            <button className="button secondary" disabled={busy} type="button" onClick={() => run('ranking')}>
              Retrieve task ranking
            </button>
          </div>
        </Panel>
      </div>

      <div className="warehouse-lower">
        <Panel>
          <p className="eyebrow">WAREHOUSE MAP · SCHEMATIC</p>
          <h2>Picking locations</h2>
          <p className="panel-copy">Location occupancy and picker paths populate from warehouse service data.</p>
          <div className="warehouse-map">
            {['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'].map((x, i) => (
              <div className={i === 1 || i === 6 || i === 9 ? 'map-cell selected' : ''} key={x}>
                {x}
                <small>{i === 1 ? 'A-1.2D' : i === 6 ? 'P-13.2A' : i === 9 ? 'P-12.3C' : 'Storage'}</small>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <p className="eyebrow">PRIORITY QUEUE</p>
          <h2>Next picking tasks</h2>
          <p className="panel-copy">The live task ranking is returned by the warehouse model.</p>
          <div className="queue-item">
            <Badge tone="red">CRITICAL</Badge>
            <span>
              <b>ORD-1042</b>
              <small>3 locations · sample</small>
            </span>
            <Link to="/journey">↗</Link>
          </div>
          <div className="queue-item">
            <Badge tone="orange">URGENT</Badge>
            <span>
              <b>Awaiting live ranking</b>
              <small>Run task ranking to populate</small>
            </span>
          </div>
          <div className="tag-list">
            <span>Orders</span>
            <span>Waves</span>
            <span>Storage locations</span>
            <span>Navigation points</span>
          </div>
        </Panel>
      </div>

      <Result value={result} />
    </Shell>
  )
}
