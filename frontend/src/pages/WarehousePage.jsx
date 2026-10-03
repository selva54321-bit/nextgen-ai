import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { Badge, Heading, Panel, Result } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function WarehousePage() {
  const [result, setResult] = useState(null)
  
  const handleDepart = (batchId) => {
     alert(`Vehicle for batch ${batchId} has departed for delivery!`);
  }

  return (
    <Shell title="Warehouse & priority">
      <Heading
        eyebrow="LAYER 1 · WAREHOUSE"
        title="Dynamic Batching & Waveless Picking"
        description="Real-time order priority ranking and dynamic vehicle batching."
      />

      <div style={{ display: 'flex', gap: '2rem', marginTop: '2rem', alignItems: 'flex-start' }}>
        {/* Left Side: Priority Queue */}
        <div style={{ width: '35%', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Panel>
            <p className="eyebrow">PRIORITY QUEUE</p>
            <h2>Ranked Orders</h2>
            <p className="panel-copy">Sorted based on real-time priority score and SLA</p>
            
            <div className="queue-item" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Badge tone="red">CRITICAL</Badge>
              <span style={{ flex: 1 }}>
                <b>ORD-1042</b>
                <br /><small>Priority Score: 98</small>
              </span>
            </div>
            
            <div className="queue-item" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Badge tone="orange">HIGH</Badge>
              <span style={{ flex: 1 }}>
                <b>ORD-2091</b>
                <br /><small>Priority Score: 85</small>
              </span>
            </div>
            
            <div className="queue-item" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Badge tone="blue">NORMAL</Badge>
              <span style={{ flex: 1 }}>
                <b>ORD-3310</b>
                <br /><small>Priority Score: 45</small>
              </span>
            </div>
            
            <div className="queue-item" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Badge tone="blue">NORMAL</Badge>
              <span style={{ flex: 1 }}>
                <b>ORD-4102</b>
                <br /><small>Priority Score: 30</small>
              </span>
            </div>
          </Panel>
        </div>

        {/* Right Side: Batches / Vehicles */}
        <div style={{ width: '65%', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Heading eyebrow="BATCHES" title="Vehicles Ready for Dispatch" />
          
          <div className="unit-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            
            {/* Batch 1 */}
            <Panel className="unit-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="panel-head">
                <h2>Vehicle 1 (DU-01)</h2>
                <Badge tone="orange">LOADING</Badge>
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: '1rem 0' }}>Contains:</p>
                <ul style={{ paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
                   <li>ORD-1042</li>
                   <li>ORD-2091</li>
                </ul>
              </div>
              <button className="button primary" onClick={() => handleDepart('DU-01')} style={{ width: '100%' }}>
                Vehicle has departed for delivery
              </button>
            </Panel>
            
            {/* Batch 2 */}
            <Panel className="unit-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="panel-head">
                <h2>Vehicle 2 (DU-02)</h2>
                <Badge tone="green">READY</Badge>
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ margin: '1rem 0' }}>Contains:</p>
                <ul style={{ paddingLeft: '1.2rem', marginBottom: '1.5rem' }}>
                   <li>ORD-3310</li>
                   <li>ORD-4102</li>
                </ul>
              </div>
              <button className="button primary" onClick={() => handleDepart('DU-02')} style={{ width: '100%' }}>
                Vehicle has departed for delivery
              </button>
            </Panel>
            
          </div>
        </div>
      </div>

    </Shell>
  )
}
