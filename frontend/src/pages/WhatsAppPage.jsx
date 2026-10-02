import { Link } from 'react-router-dom'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function WhatsAppPage() {
  return (
    <Shell title="Customer WhatsApp">
      <Heading
        eyebrow="CUSTOMER AVAILABILITY"
        title="WhatsApp coordination"
        description="See the customer response state alongside the delivery decision it informs."
        action={<Badge tone="purple">CONFIRMATION PENDING</Badge>}
      />

      <div className="chat-layout">
        <Panel className="chat-card">
          <div className="chat-head">
            <span className="avatar">1042</span>
            <div>
              <b>Customer #1042</b>
              <small>Shipment ORD-1042 · Stop B-24.2C</small>
            </div>
            <Badge tone="purple">PENDING</Badge>
          </div>

          <div className="chat-body">
            <div className="chat-date">TODAY · DELIVERY CONFIRMATION</div>
            <div className="bubble bot">
              Your delivery is planned for today. Will someone be available to receive the package?
              <small>AI assistant · awaiting send/response integration</small>
            </div>
            <div className="bubble customer">
              I may be home around 6.
              <small>Example conversation</small>
            </div>
            <div className="bubble bot">
              Would you like to review available delivery options?
              <small>AI assistant · example</small>
            </div>
            <div className="chat-compose">
              <span>WhatsApp messaging is managed by the connected service</span>
              <button disabled aria-label="Send message">↑</button>
            </div>
          </div>
        </Panel>

        <Panel>
          <p className="eyebrow">DELIVERY DECISION</p>
          <h2>Customer state</h2>
          <div className="state-list">
            {[
              ['Contact initiated', 'done'],
              ['Waiting for response', 'current'],
              ['Availability confirmed', 'pending'],
              ['Plan re-ranked', 'pending'],
              ['Delivery outcome', 'pending'],
            ].map(([x, s]) => (
              <div className={`state-row ${s}`} key={x}>
                <i />
                {x}
              </div>
            ))}
          </div>

          <div className="slot-note">
            <b>Alternative slots</b>
            <p>Slots and success estimates should come from the decision service. None are available from the current frontend API contract.</p>
          </div>

          <Link className="button secondary full-button" to="/journey">See this shipment journey</Link>
        </Panel>
      </div>
    </Shell>
  )
}
