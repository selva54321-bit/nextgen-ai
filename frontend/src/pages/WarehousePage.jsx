import { useState, useMemo, useEffect } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function WarehousePage() {
  const [batches, setBatches] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getDashboardData();
        setBatches(response);
      } catch (e) {
        if (e.message.includes('Failed to fetch')) {
           setError("Backend isn't running");
        } else {
           setError(e.message);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleDepart = (batchId) => {
     alert(`Vehicle for batch ${batchId} has departed for delivery!`);
  }

  // Flatten all orders to create the priority queue
  const priorityQueue = useMemo(() => {
    if (!batches) return [];
    const allOrders = [];
    Object.values(batches).forEach(batchOrders => {
      allOrders.push(...batchOrders);
    });
    // Sort by failure probability descending
    return allOrders.sort((a, b) => (b.delivery?.failureProbability || 0) - (a.delivery?.failureProbability || 0));
  }, [batches]);

  return (
    <Shell title="Warehouse & priority">
      <Heading
        eyebrow="LAYER 1 · WAREHOUSE"
        title="Dynamic Batching & Waveless Picking"
        description="Real-time order priority ranking and dynamic vehicle batching."
      />

      {error && (
         <Panel style={{ marginTop: '2rem', marginBottom: '2rem', border: '2px solid #d93025' }}>
           <h2 style={{ color: '#d93025', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              ⚠️ Backend isn't running
           </h2>
           <p style={{ marginTop: '0.5rem' }}>The Spring Boot backend could not be reached. Please ensure the backend server is running on port 8080.</p>
         </Panel>
      )}

      {loading && !error && (
        <Panel style={{ marginTop: '2rem' }}>
           <p>Syncing warehouse data...</p>
        </Panel>
      )}

      {batches && !error && (
        <div style={{ display: 'flex', gap: '2rem', marginTop: '2rem', alignItems: 'flex-start' }}>
          {/* Left Side: Priority Queue */}
          <div style={{ width: '35%', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Panel>
              <p className="eyebrow">PRIORITY QUEUE</p>
              <h2>Ranked Orders</h2>
              <p className="panel-copy">Sorted based on real-time SLA risk score</p>
              
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {priorityQueue.map((order, idx) => {
                  const prob = order.delivery?.failureProbability || 0;
                  const score = Math.round(prob * 100);
                  const tone = score > 10 ? 'red' : (score > 5 ? 'orange' : 'blue');
                  const label = score > 10 ? 'CRITICAL' : (score > 5 ? 'HIGH' : 'NORMAL');
                  
                  return (
                    <div key={idx} className="queue-item" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.5rem', background: '#f8f9fa', borderRadius: '8px' }}>
                      <Badge tone={tone}>{label}</Badge>
                      <span style={{ flex: 1 }}>
                        <b>{order.orderId}</b>
                        <br /><small>Risk Score: {score}</small>
                      </span>
                    </div>
                  );
                })}
              </div>
            </Panel>
          </div>

          {/* Right Side: Batches / Vehicles */}
          <div style={{ width: '65%', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Heading eyebrow="BATCHES" title="Vehicles Ready for Dispatch" />
            
            <div className="unit-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              {Object.entries(batches).map(([batchId, orders]) => (
                <Panel key={batchId} className="unit-card" style={{ display: 'flex', flexDirection: 'column' }}>
                  <div className="panel-head">
                    <h2>Vehicle ({batchId})</h2>
                    <Badge tone="green">READY</Badge>
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: '1rem 0' }}>Contains {orders.length} orders:</p>
                    <ul style={{ paddingLeft: '1.2rem', marginBottom: '1.5rem', maxHeight: '150px', overflowY: 'auto' }}>
                       {orders.map((o, i) => (
                         <li key={i}>{o.orderId} (Risk: {o.delivery?.riskBand})</li>
                       ))}
                    </ul>
                  </div>
                  <button className="button primary" onClick={() => handleDepart(batchId)} style={{ width: '100%' }}>
                    Vehicle has departed for delivery
                  </button>
                </Panel>
              ))}
            </div>
          </div>
        </div>
      )}

    </Shell>
  )
}
