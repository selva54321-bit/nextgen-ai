import { useState, useMemo, useEffect } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DispatchPage() {
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
    if (!batches) return null;
    const allOrders = Object.values(batches).flat();
    let high = 0, med = 0, low = 0;
    allOrders.forEach(o => {
      const risk = o.delivery?.riskBand || 'UNKNOWN';
      if (risk === 'HIGH') high++;
      else if (risk === 'MEDIUM') med++;
      else low++;
    });
    const total = allOrders.length;

    // Find worst order for factors
    const worstOrder = allOrders.sort((a, b) => (b.delivery?.failureProbability || 0) - (a.delivery?.failureProbability || 0))[0];

    return {
      high, med, low, total,
      highPct: Math.round((high / total) * 100),
      medPct: Math.round((med / total) * 100),
      lowPct: Math.round((low / total) * 100),
      worstOrder
    };
  }, [batches]);

  return (
    <Shell title="Dispatch & Risk Analysis">
      <Heading
        eyebrow="AI DELIVERY PREDICTION"
        title="Dispatch Control Center"
        description="Analyze delivery risks based on advanced ML models."
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
          <p>Syncing risk data...</p>
        </Panel>
      )}

      {stats && !error && (
        <>
          {/* Top: Risk breakdown */}
          <div className="metric-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', marginTop: '2rem' }}>
            <Panel>
              <span className="metric-label">HIGH RISK</span>
              <b className="metric-value" style={{ color: '#d93025' }}>{stats.highPct}%</b>
              <span className="metric-note">{stats.high} Orders</span>
            </Panel>
            <Panel>
              <span className="metric-label">MEDIUM RISK</span>
              <b className="metric-value" style={{ color: '#f29900' }}>{stats.medPct}%</b>
              <span className="metric-note">{stats.med} Orders</span>
            </Panel>
            <Panel>
              <span className="metric-label">LOW RISK</span>
              <b className="metric-value" style={{ color: '#1e8e3e' }}>{stats.lowPct}%</b>
              <span className="metric-note">{stats.low} Orders</span>
            </Panel>
          </div>

          {/* Center: Risk Card */}
          <Panel style={{ marginTop: '2rem' }}>
            <p className="eyebrow">RISK ANALYSIS</p>
            <h2>Delivery Risk Details</h2>
            {stats.worstOrder ? (
              <div style={{ display: 'flex', gap: '3rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '250px' }}>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
                    Risk Score: <span style={{ color: '#d93025' }}>{stats.worstOrder.delivery?.failureProbability} ({stats.worstOrder.delivery?.riskBand})</span>
                  </h3>
                  <p style={{ color: '#555', lineHeight: '1.5' }}>
                    Failure probability is elevated for order {stats.worstOrder.orderId}. The ML model predicts potential delivery failures if no intervention is taken.
                  </p>
                  {stats.worstOrder.delivery?.riskBand === 'HIGH' && (
                    <Badge tone="red" style={{ marginTop: '1rem' }}>REQUIRES INTERVENTION</Badge>
                  )}
                </div>
                <div style={{ flex: 1, minWidth: '250px', background: '#f8f9fa', padding: '1.5rem', borderRadius: '8px' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#333' }}>Top 3 Risk Factors:</h3>
                  <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', paddingLeft: '1.2rem', color: '#444' }}>
                    {stats.worstOrder.delivery?.topFactors?.map((f, i) => (
                      <li key={i}><b>{f}</b></li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p>No orders to analyze.</p>
            )}
          </Panel>
        </>
      )}
    </Shell>
  )
}
