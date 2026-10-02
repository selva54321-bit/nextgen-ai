import { Link } from 'react-router-dom'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function OrderJourneyPage() {
  return (
    <Shell title="Order 360 journey">
      <Heading
        eyebrow="END-TO-END TRACKING"
        title="One shipment, both operational layers"
        description="A single view connects warehouse priority, dispatch, delivery risk, customer WhatsApp, re-ranking, and outcome."
        action={<Badge tone="orange">DEMO WALKTHROUGH</Badge>}
      />

      <div className="journey-hero">
        <div>
          <p className="eyebrow">SHIPMENT</p>
          <h2>ORD-1042</h2>
          <p>Customer #1042 · 4 items · Picking wave W-43175</p>
        </div>
        <div className="hero-status">
          <Badge tone="red">CRITICAL PICK PRIORITY</Badge>
          <span>Current stage: delivery planning</span>
        </div>
      </div>

      <Panel className="timeline-panel">
        <h2>Shipment event timeline</h2>
        <div className="event-timeline">
          {[
            ['10:02', 'Order created', 'Order received by warehouse'],
            ['10:08', 'Picking wave assigned', 'W-43175 · 3 locations'],
            ['10:19', 'AI priority assigned', 'Critical · warehouse model'],
            ['10:37', 'Picking completed', 'Ready for dispatch'],
            ['10:42', 'Dispatch unit assigned', 'DU-03'],
            ['11:05', 'Route generated', 'R-00143 · stop B-24.2C'],
            ['11:06', 'Delivery risk assessment', 'Retrieve current risk from live model'],
            ['11:07', 'Customer contacted', 'WhatsApp availability pending'],
            ['—', 'Re-rank & delivery', 'Waiting for customer and backend outcome'],
          ].map(([time, title, detail], i) => (
            <div className={`event ${i < 6 ? 'complete' : ''}`} key={title}>
              <time>{time}</time>
              <i />
              <div>
                <b>{title}</b>
                <span>{detail}</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="journey-actions">
        <Link className="button secondary" to="/warehouse">Warehouse & priority</Link>
        <Link className="button secondary" to="/dispatch">Dispatch unit</Link>
        <Link className="button secondary" to="/delivery">Route & live risk</Link>
        <Link className="button primary" to="/whatsapp">Customer WhatsApp</Link>
      </div>

      <Panel className="notice">
        <span className="notice-mark">i</span>
        <p>Timeline identifiers and timestamps are illustrative demo content. Replace with persisted shipment events when the order tracking endpoint is available.</p>
      </Panel>
    </Shell>
  )
}
