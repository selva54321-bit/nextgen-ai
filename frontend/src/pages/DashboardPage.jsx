import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DashboardPage() {
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

  const stats = useMemo(() => {
    if (!batches) return { total: '...', batches: '...', risk: '...', customers: '...' };
    const allOrders = Object.values(batches).flat();
    const highRisk = allOrders.filter(o => o.delivery?.riskBand === 'HIGH').length;
    return {
       total: allOrders.length,
       batches: Object.keys(batches).length,
       risk: highRisk,
       customers: highRisk // simulating customers needing contact
    };
  }, [batches]);

  return (
    <Shell title="Command center">
      <Heading
        eyebrow="NETWORK OVERVIEW"
        title="One connected logistics journey"
        description="Follow an order from picking priority through dispatch, delivery risk, customer availability, and final outcome."
        action={<Badge tone={error ? "red" : (loading ? "orange" : "green")}>{error ? "● BACKEND OFFLINE" : (loading ? "● SYNCING..." : "● SYSTEM READY")}</Badge>}
      />

      {error && (
         <Panel style={{ marginTop: '2rem', marginBottom: '2rem', border: '2px solid #d93025' }}>
           <h2 style={{ color: '#d93025', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              ⚠️ Backend isn't running
           </h2>
           <p style={{ marginTop: '0.5rem' }}>The Spring Boot backend could not be reached. Please ensure the backend server is running on port 8080.</p>
         </Panel>
      )}

      {!error && (
        <>
          <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
            <Panel>
              <span className="metric-label">WAREHOUSE</span>
              <b className="metric-value">{stats.total} Orders</b>
              <span className="metric-note">Processed in waveless picking</span>
            </Panel>
            <Panel>
              <span className="metric-label">DISPATCH</span>
              <b className="metric-value">{stats.batches} Vehicles</b>
              <span className="metric-note">Batches dynamically created</span>
            </Panel>
            <Panel>
              <span className="metric-label">DELIVERY RISK</span>
              <b className="metric-value" style={{ color: stats.risk > 0 ? '#d93025' : 'inherit' }}>{stats.risk} High Risk</b>
              <span className="metric-note">Identified by ML prediction</span>
            </Panel>
            <Panel>
              <span className="metric-label">CUSTOMER</span>
              <b className="metric-value">{stats.customers} Pending</b>
              <span className="metric-note">WhatsApp verification queue</span>
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
                Check the dynamic batching and priority ranking of orders from the warehouse engine.
              </p>
            </Panel>

            <Panel>
              <div className="panel-head">
                <div>
                  <p className="eyebrow">LAYER 2 · LAST MILE</p>
                  <h2>Risk Analysis & AI Assistant</h2>
                </div>
                <Link to="/dispatch" className="text-link">Open dispatch →</Link>
              </div>
              <p className="panel-copy">
                Analyze last-mile delivery risks and utilize the AI assistant for automated WhatsApp resolutions.
              </p>
            </Panel>
          </div>
        </>
      )}
    </Shell>
  )
}
