import { Link } from 'react-router-dom'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DashboardPage() {
  return (
    <Shell title="Command center">
      <Heading
        eyebrow="NETWORK OVERVIEW"
        title="One connected logistics journey"
        description="Follow an order from picking priority through dispatch, delivery risk, customer availability, and final outcome."
        action={<Badge tone="green">● SYSTEM READY</Badge>}
      />

      <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '2rem' }}>
        <Panel>
          <span className="metric-label">WAREHOUSE</span>
          <b className="metric-value">Picking → ready</b>
          <span className="metric-note">Open operational workflow</span>
        </Panel>
        <Panel>
          <span className="metric-label">DISPATCH</span>
          <b className="metric-value">Unit DU-03</b>
          <span className="metric-note">Route R-00143 · 118 stops</span>
        </Panel>
        <Panel>
          <span className="metric-label">DELIVERY RISK</span>
          <b className="metric-value">Live model lookup</b>
          <span className="metric-note">Risk values come from backend</span>
        </Panel>
        <Panel>
          <span className="metric-label">CUSTOMER</span>
          <b className="metric-value">Availability pending</b>
          <span className="metric-note">WhatsApp workflow</span>
        </Panel>
      </div>

      <div className="dashboard-grid" style={{ marginTop: '3rem' }}>
        <Panel>
          <div className="panel-head">
            <div>
              <p className="eyebrow">LAYER 1 · WAREHOUSE</p>
              <h2>Goods to dispatch</h2>
            </div>
            <Link to="/warehouse" className="text-link">Open warehouse →</Link>
          </div>
          <p className="panel-copy">
            Upload and validate warehouse data, run the picking simulation, or request ranked tasks.
          </p>
        </Panel>

        <Panel>
          <div className="panel-head">
            <div>
              <p className="eyebrow">LAYER 2 · LAST MILE</p>
              <h2>Route to delivery outcome</h2>
            </div>
            <Link to="/delivery" className="text-link">Open routes →</Link>
          </div>
          <p className="panel-copy">
            Check a stop against the trained risk model, then coordinate customer availability and delivery options.
          </p>
        </Panel>
      </div>

      <Panel className="notice" style={{ marginTop: '2rem' }}>
        <span className="notice-mark">i</span>
        <p>
          <b>Data integrity:</b> shipment identifiers above are a walkthrough example. Network totals and customer outcomes appear only when supplied by connected services.
        </p>
      </Panel>
    </Shell>
  )
}
