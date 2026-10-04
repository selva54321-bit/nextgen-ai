import { useState, useMemo, useEffect } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

// --- Status pipeline ---
const STATUS_STAGES = [
  { key: 'PENDING',            label: 'Order Placed',        icon: '📦' },
  { key: 'PICKING',            label: 'Picking in Progress',  icon: '🔄' },
  { key: 'PACKED',             label: 'Packed & Ready',      icon: '✅' },
  { key: 'READY_FOR_DISPATCH', label: 'Ready for Dispatch',  icon: '🚚' },
  { key: 'DISPATCHED',         label: 'En Route',            icon: '🛣️' },
  { key: 'DELIVERED',          label: 'Delivered',           icon: '🏠' },
]

function getStageIndex(status) {
  const s = (status || '').toUpperCase()
  const idx = STATUS_STAGES.findIndex(st => st.key === s)
  if (idx !== -1) return idx
  if (s === 'CRITICAL') return 2
  if (s === 'READY')    return 3
  return 0
}

const RISK_TONE  = { HIGH: 'red', MEDIUM: 'orange', LOW: 'green' }
const RISK_LABEL = { HIGH: '⚠️ HIGH RISK', MEDIUM: '⚡ MEDIUM RISK', LOW: '✅ LOW RISK' }

// --- Order timeline ---
function OrderTimeline({ stageIndex }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, overflowX: 'auto', paddingBottom: '0.5rem' }}>
      {STATUS_STAGES.map((stage, i) => {
        const done    = i < stageIndex
        const current = i === stageIndex
        return (
          <div key={stage.key} style={{ display: 'flex', alignItems: 'center', flex: '1 0 auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '80px' }}>
              <div style={{
                width: '44px', height: '44px', borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: done ? '1.1rem' : '1.3rem',
                background: done ? '#1e8e3e' : current ? '#1a73e8' : '#e8eaed',
                color: (done || current) ? '#fff' : '#5f6368',
                fontWeight: 700,
                border: current ? '3px solid #1557b0' : '3px solid transparent',
                boxShadow: current ? '0 0 0 3px rgba(26,115,232,0.2)' : 'none',
                transition: 'all 0.3s', flexShrink: 0,
              }}>
                {done ? '✓' : stage.icon}
              </div>
              <span style={{
                marginTop: '0.5rem', fontSize: '0.72rem',
                fontWeight: current ? 700 : 400,
                color: done ? '#1e8e3e' : current ? '#1a73e8' : '#9aa0a6',
                textAlign: 'center', lineHeight: 1.3,
              }}>{stage.label}</span>
            </div>
            {i < STATUS_STAGES.length - 1 && (
              <div style={{
                flex: 1, height: '3px', marginBottom: '22px',
                background: i < stageIndex ? '#1e8e3e' : '#e8eaed',
                transition: 'background 0.3s',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// --- Order tracking result ---
function OrderTrackingResult({ order, batches }) {
  // Find which dispatch unit this order was assigned to
  const dispatchUnit = useMemo(() => {
    if (!batches) return null
    for (const [unitId, orders] of Object.entries(batches)) {
      const match = orders.find(o => o.orderId === order.orderId)
      if (match) return { unitId, matchedOrder: match }
    }
    return null
  }, [batches, order])

  const stageIndex = getStageIndex(order.status)
  const risk       = dispatchUnit?.matchedOrder?.delivery?.riskBand || 'UNKNOWN'
  const factors    = dispatchUnit?.matchedOrder?.delivery?.topFactors || []
  const failProb   = dispatchUnit?.matchedOrder?.delivery?.failureProbability

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '2rem' }}>
      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <p className="eyebrow">ORDER TRACKING</p>
            <h2 style={{ marginTop: '0.25rem' }}>{order.orderId}</h2>
            <p style={{ color: '#5f6368', marginTop: '0.25rem' }}>Customer: {order.customerId}</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
            <Badge tone={order.status === 'CRITICAL' ? 'red' : 'blue'}>{order.status}</Badge>
            {dispatchUnit && <Badge tone="blue">Vehicle: {dispatchUnit.unitId}</Badge>}
          </div>
        </div>
        <div style={{ marginTop: '2rem' }}>
          <OrderTimeline stageIndex={stageIndex} />
        </div>
      </Panel>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <Panel>
          <p className="eyebrow">DELIVERY DETAILS</p>
          <h3 style={{ marginTop: '0.25rem', marginBottom: '1rem' }}>Shipment Info</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
            {[
              ['Order ID',      order.orderId],
              ['Customer',      order.customerId],
              ['Status',        order.status],
              ['Dispatch Unit', dispatchUnit?.unitId || '—'],
              ['Created At',    order.createdAt ? new Date(order.createdAt).toLocaleString() : '—'],
              ['Deadline',      order.deadline   ? new Date(order.deadline).toLocaleString()  : '—'],
            ].map(([label, value]) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #e8eaed', paddingBottom: '0.5rem' }}>
                <span style={{ color: '#5f6368' }}>{label}</span>
                <b>{value}</b>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <p className="eyebrow">DELIVERY RISK</p>
          <h3 style={{ marginTop: '0.25rem', marginBottom: '1rem' }}>AI Risk Assessment</h3>
          {dispatchUnit?.matchedOrder ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Badge tone={RISK_TONE[risk] || 'blue'}>{RISK_LABEL[risk] || risk}</Badge>
                {failProb != null && (
                  <span style={{ fontSize: '0.85rem', color: '#5f6368' }}>
                    Failure prob: <b>{Math.round(failProb * 100)}%</b>
                  </span>
                )}
              </div>
              {factors.length > 0 && (
                <div style={{ background: '#f8f9fa', borderRadius: '8px', padding: '1rem' }}>
                  <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Top Risk Factors:</p>
                  <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.85rem', color: '#444', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {factors.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#9aa0a6', fontSize: '0.9rem' }}>AI prediction not yet cached for this order.</p>
          )}
        </Panel>
      </div>
    </div>
  )
}

// --- Route tracking result ---
function RouteTrackingResult({ unit, dbOrders, aiOrders }) {
  // Merge DB orders with AI risk data where available
  const orders = useMemo(() => {
    return dbOrders.map(dbOrder => {
      const aiMatch = (aiOrders || []).find(o => o.orderId === dbOrder.orderId)
      return { ...dbOrder, delivery: aiMatch?.delivery || null }
    })
  }, [dbOrders, aiOrders])

  const highRisk  = orders.filter(o => o.delivery?.riskBand === 'HIGH' || (o.delivery?.failureProbability || 0) > 0.05)
  const totalRisk = orders.reduce((s, o) => s + (o.delivery?.failureProbability || 0), 0)
  const avgRisk   = orders.length ? (totalRisk / orders.length * 100).toFixed(1) : 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '2rem' }}>
      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <p className="eyebrow">ROUTE TRACKING</p>
            <h2 style={{ marginTop: '0.25rem' }}>Vehicle: {unit.unitId}</h2>
            <p style={{ color: '#5f6368', marginTop: '0.25rem' }}>
              {unit.availability} · Location: {unit.currentLocation || '—'} · Capacity: {unit.capacity ?? '—'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Badge tone={unit.availability === 'AVAILABLE' ? 'green' : unit.availability === 'BUSY' ? 'orange' : 'red'}>
              {unit.availability}
            </Badge>
            <Badge tone={highRisk.length > 0 ? 'red' : 'green'}>
              {highRisk.length > 0 ? `${highRisk.length} High Risk` : '✅ All Clear'}
            </Badge>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginTop: '2rem' }}>
          {[
            ['Total Orders',  orders.length,              '#1a73e8', '#e8f0fe'],
            ['High Risk',     highRisk.length,            '#e65100', '#fff3e0'],
            ['On Track',      orders.length - highRisk.length, '#1e8e3e', '#e8f5e9'],
          ].map(([label, value, color, bg]) => (
            <div key={label} style={{ background: bg, borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
              <b style={{ fontSize: '2rem', display: 'block', color }}>{value}</b>
              <span style={{ fontSize: '0.8rem', color: '#5f6368', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <p className="eyebrow">STOP MANIFEST</p>
        <h3 style={{ marginTop: '0.25rem', marginBottom: '1.5rem' }}>
          {orders.length > 0 ? `All ${orders.length} Orders on This Vehicle` : 'No orders assigned yet (AI data pending)'}
        </h3>
        {orders.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {orders.map((order, i) => {
              const risk  = order.delivery?.riskBand || 'UNKNOWN'
              const prob  = Math.round((order.delivery?.failureProbability || 0) * 100)
              const stage = STATUS_STAGES[getStageIndex(order.status)]
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '1rem',
                  padding: '1rem', borderRadius: '8px',
                  background: risk === 'HIGH' ? '#fff5f5' : '#f8f9fa',
                  border: `1px solid ${risk === 'HIGH' ? '#ffcccc' : '#e8eaed'}`,
                }}>
                  <div style={{
                    width: '32px', height: '32px', borderRadius: '50%',
                    background: '#1a73e8', color: '#fff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: '0.8rem', flexShrink: 0,
                  }}>{i + 1}</div>
                  <div style={{ flex: 1 }}>
                    <b style={{ fontSize: '0.9rem' }}>{order.orderId}</b>
                    <div style={{ fontSize: '0.8rem', color: '#5f6368', marginTop: '0.15rem' }}>
                      {stage?.label || order.status}
                    </div>
                  </div>
                  <Badge tone={RISK_TONE[risk] || 'blue'}>{prob}% Risk</Badge>
                </div>
              )
            })}
          </div>
        ) : (
          <p style={{ color: '#9aa0a6', fontSize: '0.9rem' }}>
            Load the dashboard first to cache AI predictions, then route manifest will appear here.
          </p>
        )}
      </Panel>
    </div>
  )
}

// --- Quick-pick chip ---
function Chip({ label, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: '0.3rem 0.75rem', borderRadius: '6px',
      border: '1px solid #e8eaed', background: '#f8f9fa',
      fontSize: '0.8rem', cursor: 'pointer', transition: 'background 0.15s',
    }}
    onMouseEnter={e => e.target.style.background = '#e8eaed'}
    onMouseLeave={e => e.target.style.background = '#f8f9fa'}
    >{label}</button>
  )
}

// --- Main Page ---
export default function TrackingPage() {
  const [dbOrders,        setDbOrders]        = useState([])
  const [dbUnits,         setDbUnits]         = useState([])
  const [unitAssignments, setUnitAssignments] = useState(null)   // { unitId -> [orders] } from DB
  const [batches,         setBatches]         = useState(null)   // AI-enriched data (optional)
  const [loadingDb, setLoadingDb] = useState(true)
  const [error,     setError]     = useState(null)

  const [mode,     setMode]     = useState('order')
  const [query,    setQuery]    = useState('')
  const [searched, setSearched] = useState('')
  const [result,   setResult]   = useState(null)
  const [notFound, setNotFound] = useState(false)

  // Fetch raw DB data immediately (fast, no AI)
  useEffect(() => {
    Promise.all([api.getAllOrders(), api.getAllUnits(), api.getUnitAssignments()])
      .then(([orders, units, assignments]) => {
        setDbOrders(orders || [])
        setDbUnits(units || [])
        setUnitAssignments(assignments || {})
      })
      .catch(e => setError(e.message))
      .finally(() => setLoadingDb(false))

    // Also fetch AI-enriched batches in background for risk data
    api.getDashboardData()
      .then(data => setBatches(data))
      .catch(() => {/* silent — risk data is optional */})
  }, [])

  const handleSearch = () => {
    const q = query.trim().toUpperCase()
    setSearched(q)
    setNotFound(false)
    setResult(null)
    if (!q) return

    if (mode === 'order') {
      const order = dbOrders.find(o => o.orderId?.toUpperCase() === q)
      if (order) setResult({ type: 'order', order })
      else       setNotFound(true)
    } else {
      const unit = dbUnits.find(u => u.unitId?.toUpperCase() === q)
      if (unit) setResult({ type: 'route', unit })
      else      setNotFound(true)
    }
  }

  const handleKeyDown = e => { if (e.key === 'Enter') handleSearch() }

  return (
    <Shell title="Tracking">
      <Heading
        eyebrow="LIVE TRACKING"
        title="Order & Route Tracker"
        description="Track any order by its ID to see its current stage, or track a vehicle route by its dispatch unit ID."
      />

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem' }}>
        {[['order', '📦 Order / Product'], ['route', '🚚 Vehicle Route']].map(([m, label]) => (
          <button key={m}
            onClick={() => { setMode(m); setResult(null); setNotFound(false); setQuery('') }}
            style={{
              padding: '0.6rem 1.5rem', borderRadius: '8px',
              border: mode === m ? '2px solid #1a73e8' : '2px solid #e8eaed',
              background: mode === m ? '#e8f0fe' : '#fff',
              color: mode === m ? '#1a73e8' : '#3c4043',
              fontWeight: mode === m ? 700 : 400,
              cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s',
            }}>{label}</button>
        ))}
      </div>

      {/* Search bar */}
      <Panel style={{ marginTop: '1.5rem' }}>
        <p className="eyebrow">{mode === 'order' ? 'ORDER LOOKUP' : 'ROUTE LOOKUP'}</p>
        <h3 style={{ marginTop: '0.25rem', marginBottom: '1rem' }}>
          {mode === 'order' ? 'Enter Order ID (e.g. ORD-1001)' : 'Enter Dispatch Unit ID (e.g. DU-01)'}
        </h3>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <input
            id="tracking-input"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={mode === 'order' ? 'ORD-1001' : 'DU-01'}
            style={{
              flex: 1, padding: '0.75rem 1rem', borderRadius: '8px',
              border: '1.5px solid #e8eaed', fontSize: '1rem', outline: 'none',
            }}
            onFocus={e => e.target.style.border = '1.5px solid #1a73e8'}
            onBlur={e => e.target.style.border = '1.5px solid #e8eaed'}
          />
          <button id="tracking-search-btn"
            onClick={handleSearch}
            disabled={loadingDb || !query.trim()}
            style={{
              padding: '0.75rem 2rem', borderRadius: '8px', border: 'none',
              background: '#1a73e8', color: '#fff', fontWeight: 700,
              fontSize: '1rem', cursor: 'pointer',
              opacity: loadingDb || !query.trim() ? 0.6 : 1, transition: 'opacity 0.2s',
            }}>Track →</button>
        </div>

        {loadingDb && <p style={{ marginTop: '1rem', color: '#5f6368', fontSize: '0.9rem' }}>Loading from database…</p>}
        {error     && <p style={{ marginTop: '1rem', color: '#d93025', fontSize: '0.9rem' }}>⚠️ {error}</p>}

        {/* Quick-pick chips from real DB */}
        {!loadingDb && !result && !notFound && (
          <div style={{ marginTop: '1rem' }}>
            <p style={{ fontSize: '0.8rem', color: '#9aa0a6', marginBottom: '0.5rem' }}>
              {mode === 'order'
                ? `${dbOrders.length} orders in database:`
                : `${dbUnits.length} vehicles in database:`}
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {mode === 'order'
                ? dbOrders.map(o => <Chip key={o.orderId} label={o.orderId} onClick={() => setQuery(o.orderId)} />)
                : dbUnits.map(u => <Chip key={u.unitId}  label={u.unitId}  onClick={() => setQuery(u.unitId)} />)
              }
            </div>
          </div>
        )}
      </Panel>

      {/* Not found */}
      {notFound && (
        <Panel style={{ marginTop: '1.5rem', border: '1.5px solid #ffcccc' }}>
          <p style={{ color: '#d93025', fontWeight: 600 }}>
            ❌ {mode === 'order' ? `Order "${searched}"` : `Vehicle "${searched}"`} not found.
          </p>
          <p style={{ color: '#5f6368', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Check the ID and try again. Use the chips above to browse all available {mode === 'order' ? 'orders' : 'vehicles'} from the database.
          </p>
        </Panel>
      )}

      {/* Results */}
      {result?.type === 'order' && (
        <OrderTrackingResult order={result.order} batches={batches} />
      )}
      {result?.type === 'route' && (
        <RouteTrackingResult
          unit={result.unit}
          dbOrders={unitAssignments?.[result.unit.unitId] || []}
          aiOrders={batches?.[result.unit.unitId] || []}
        />
      )}
    </Shell>
  )
}
