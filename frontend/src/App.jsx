import { useState } from 'react'
import './App.css'
import { api } from './api/client.js'



const nav = [
  ['/', 'Command center', '⌂'], ['/warehouse', 'Warehouse & priority', '▦'],
  ['/dispatch', 'Dispatch units', '⇢'], ['/delivery', 'Routes & risk', '⌖'],
  ['/whatsapp', 'Customer WhatsApp', '◉'], ['/journey', 'Order 360 journey', '↗'],
]
const stages = [
  ['Order created', 'ORD-1042', 'done'], ['Picking wave', 'W-43175', 'done'],
  ['AI priority', 'Critical', 'done'], ['Picking complete', '3 locations', 'done'],
  ['Dispatch unit', 'DU-03', 'done'], ['Route & stop', 'R-00143 · B-24.2C', 'done'],
  ['Delivery risk', 'Check live model', 'current'], ['WhatsApp', 'Awaiting availability', 'pending'],
  ['Re-rank & deliver', 'Outcome pending', 'pending'],
]

function Shell({ children, title }) {
  const path = window.location.pathname.replace(/\/$/, '') || '/'
  return <div className="shell"><aside className="sidebar">
    <a className="brand" href="/"><span className="brand-mark">N</span><span>NextGen<small>LOGISTICS CONTROL</small></span></a>
    <p className="nav-label">OPERATIONS</p><nav>{nav.map(([href, label, icon]) => <a key={href} className={`nav-link ${path === href ? 'active' : ''}`} href={href}><span className="nav-icon">{icon}</span>{label}</a>)}</nav>
    <div className="sidebar-bottom"><span className="status-dot" /> Backend connection configured<small>Live data depends on service availability</small></div>
  </aside><div className="content-area"><header className="topbar"><span>Operations <b>/</b> {title}</span><span className="live-tag"><i /> CONTROL CENTER</span></header><main className="page-content">{children}</main><footer className="site-footer"><span>NextGen Logistics · Operations workspace</span><span><a href="/privacy">Privacy</a><a href="/terms">Terms</a></span></footer></div></div>
}

function Heading({ eyebrow, title, description, action }) { return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action}</div> }
function Panel({ children, className = '' }) { return <section className={`panel ${className}`}>{children}</section> }
function Result({ value }) { return value && <Panel className="result-wrap"><h3>Backend response</h3><pre className="result-box">{JSON.stringify(value, null, 2)}</pre></Panel> }
function Badge({ children, tone = 'blue' }) { return <span className={`badge ${tone}`}>{children}</span> }

function Journey({ compact = false }) {
  return <Panel className={`journey-panel ${compact ? 'compact' : ''}`}><div className="panel-head"><div><p className="eyebrow">CONNECTED SHIPMENT</p><h2>ORD-1042 <span className="muted">· Customer #1042</span></h2></div><Badge tone="orange">IN DELIVERY PLANNING</Badge></div>
    <div className="journey-track">{stages.map(([name, detail, state], i) => <div className={`journey-stage ${state}`} key={name}><div className="stage-marker">{state === 'done' ? '✓' : String(i + 1).padStart(2, '0')}</div><div className="stage-copy"><b>{name}</b><span>{detail}</span></div>{i < stages.length - 1 && <div className="stage-connector" />}</div>)}</div>
    <div className="journey-foot"><span>Warehouse handoff <b>DU-03 → R-00143</b></span><a href="/journey">Open complete shipment journey →</a></div>
  </Panel>
}

function Dashboard() {
  return <Shell title="Command center"><Heading eyebrow="NETWORK OVERVIEW" title="One connected logistics journey" description="Follow an order from picking priority through dispatch, delivery risk, customer availability, and final outcome." action={<Badge tone="green">● SYSTEM READY</Badge>} />
    <div className="metric-grid"><Panel><span className="metric-label">WAREHOUSE</span><b className="metric-value">Picking → ready</b><span className="metric-note">Open operational workflow</span></Panel><Panel><span className="metric-label">DISPATCH</span><b className="metric-value">Unit DU-03</b><span className="metric-note">Route R-00143 · 118 stops</span></Panel><Panel><span className="metric-label">DELIVERY RISK</span><b className="metric-value">Live model lookup</b><span className="metric-note">Risk values come from backend</span></Panel><Panel><span className="metric-label">CUSTOMER</span><b className="metric-value">Availability pending</b><span className="metric-note">WhatsApp workflow</span></Panel></div>
    <Journey compact />
    <div className="dashboard-grid"><Panel><div className="panel-head"><div><p className="eyebrow">LAYER 1 · WAREHOUSE</p><h2>Goods to dispatch</h2></div><a href="/warehouse" className="text-link">Open warehouse →</a></div><div className="flow-mini"><span>Orders & goods</span><b>→</b><span>Picking wave</span><b>→</b><span>AI priority</span><b>→</b><span>Dispatch unit</span></div><p className="panel-copy">Upload and validate warehouse data, run the picking simulation, or request ranked tasks.</p></Panel>
      <Panel><div className="panel-head"><div><p className="eyebrow">LAYER 2 · LAST MILE</p><h2>Route to delivery outcome</h2></div><a href="/delivery" className="text-link">Open routes →</a></div><div className="flow-mini"><span>Route & stops</span><b>→</b><span>Risk score</span><b>→</b><span>WhatsApp</span><b>→</b><span>Re-rank</span></div><p className="panel-copy">Check a stop against the trained risk model, then coordinate customer availability and delivery options.</p></Panel></div>
    <Panel className="notice"><span className="notice-mark">i</span><p><b>Data integrity:</b> shipment identifiers above are a walkthrough example. Network totals and customer outcomes appear only when supplied by connected services.</p></Panel>
  </Shell>
}

function Warehouse() {
  const [file, setFile] = useState(null), [result, setResult] = useState(null), [busy, setBusy] = useState(false)
  const run = async action => { setBusy(true); setResult(null); try { if (action === 'upload') { if (!file) throw new Error('Choose a CSV or Excel file first.'); setResult(await api.warehouseUpload(file)) } else if (action === 'simulation') setResult(await api.warehouseSimulation()); else setResult(await api.taskRanking()) } catch (e) { setResult({ error: e.message }) } finally { setBusy(false) } }
  return <Shell title="Warehouse & priority"><Heading eyebrow="LAYER 1 · WAREHOUSE" title="Goods, picking and priority" description="Prepare warehouse data, inspect picking operations, and move ready orders toward dispatch." />
    <div className="warehouse-banner"><div><p className="eyebrow">ACTIVE PICKING WAVE</p><h2>W-43175 <Badge tone="red">CRITICAL PRIORITY</Badge></h2><p>Example shipment ORD-1042 · 3 warehouse locations · dispatch handoff DU-03</p></div><a className="button secondary" href="/journey">View order journey</a></div>
    <div className="work-grid"><Panel><div className="section-title"><span className="step-num">01</span><h2>Upload warehouse dataset</h2></div><p className="panel-copy">Validate the customer orders, product, storage location, strategy, and navigation inputs.</p><label className="file-picker">Choose CSV or Excel dataset<input type="file" accept=".csv,.xls,.xlsx" onChange={e => setFile(e.target.files?.[0] || null)} /></label>{file && <p className="file-name">Selected: {file.name}</p>}<button className="button primary" disabled={busy} onClick={() => run('upload')}>{busy ? 'Working…' : 'Upload and validate'}</button></Panel>
    <Panel><div className="section-title"><span className="step-num">02</span><h2>Picking operations</h2></div><p className="panel-copy">Run the warehouse simulation or ask the service for its current task ranking.</p><div className="button-stack"><button className="button primary" disabled={busy} onClick={() => run('simulation')}>Run warehouse simulation</button><button className="button secondary" disabled={busy} onClick={() => run('ranking')}>Retrieve task ranking</button></div></Panel></div>
    <div className="warehouse-lower"><Panel><p className="eyebrow">WAREHOUSE MAP · SCHEMATIC</p><h2>Picking locations</h2><p className="panel-copy">Location occupancy and picker paths populate from warehouse service data.</p><div className="warehouse-map">{['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4'].map((x,i)=><div className={i===1||i===6||i===9?'map-cell selected':''} key={x}>{x}<small>{i===1?'A-1.2D':i===6?'P-13.2A':i===9?'P-12.3C':'Storage'}</small></div>)}</div></Panel><Panel><p className="eyebrow">PRIORITY QUEUE</p><h2>Next picking tasks</h2><p className="panel-copy">The live task ranking is returned by the warehouse model.</p><div className="queue-item"><Badge tone="red">CRITICAL</Badge><span><b>ORD-1042</b><small>3 locations · sample</small></span><a href="/journey">↗</a></div><div className="queue-item"><Badge tone="orange">URGENT</Badge><span><b>Awaiting live ranking</b><small>Run task ranking to populate</small></span></div><div className="tag-list"><span>Orders</span><span>Waves</span><span>Storage locations</span><span>Navigation points</span></div></Panel></div><Result value={result} />
  </Shell>
}

function Dispatch() {
  const [orderId, setOrderId] = useState(''), [unitId, setUnitId] = useState(''), [simulation, setSimulation] = useState(true), [file, setFile] = useState(null), [result, setResult] = useState(null), [busy, setBusy] = useState(false)
  const submit = async e => { e.preventDefault(); setBusy(true); setResult(null); try { setResult(file ? await api.dispatchBatch(file) : await api.dispatchPlan({ orderIds: [orderId], dispatchUnitId: unitId, simulationMode: simulation })) } catch (err) { setResult({ error: err.message }) } finally { setBusy(false) } }
  return <Shell title="Dispatch units"><Heading eyebrow="WAREHOUSE HANDOFF" title="Dispatch unit control" description="Connect ready goods to a dispatch unit and review the service's dispatch plan." />
    <div className="unit-grid">{[['DU-01','AVAILABLE','78%','12'],['DU-02','LOADING','91%','18'],['DU-03','DISPATCHED','84%','21']].map(([id,status,capacity,packages])=><Panel key={id} className="unit-card"><div className="panel-head"><h2>{id}</h2><Badge tone={status==='AVAILABLE'?'green':status==='LOADING'?'orange':'blue'}>{status}</Badge></div><div className="capacity"><span style={{width:capacity}} /></div><div className="unit-meta"><span>Capacity <b>{capacity}</b></span><span>Packages <b>{packages}</b></span></div><small className="demo-label">Example dispatch unit</small></Panel>)}</div>
    <Panel className="form-panel"><form onSubmit={submit}><p className="eyebrow">BACKEND DISPATCH PLAN</p><h2>Create or simulate a plan</h2><p className="panel-copy">Use the connected dispatch endpoint. Batch plans accept a CSV or Excel route/stop file.</p><div className="field-grid"><label>Order ID<input required={!file} value={orderId} onChange={e=>setOrderId(e.target.value)} placeholder="ORD-1042" /></label><label>Dispatch unit ID<input required={!file} value={unitId} onChange={e=>setUnitId(e.target.value)} placeholder="DU-03" /></label></div><label className="check-row"><input type="checkbox" checked={simulation} onChange={e=>setSimulation(e.target.checked)} /> Simulation mode</label><label className="file-picker">Optional batch dataset<input type="file" accept=".csv,.xls,.xlsx" onChange={e=>setFile(e.target.files?.[0]||null)} /></label><button className="button primary" disabled={busy}>{busy?'Creating plan…':file?'Create batch plan':'Create dispatch plan'}</button></form></Panel><Result value={result}/>
  </Shell>
}

function Delivery() {
  const [stopId,setStopId]=useState('B-24.2C'),[result,setResult]=useState(null),[busy,setBusy]=useState(false)
  const check=async e=>{e?.preventDefault();setBusy(true);setResult(null);try{setResult(await api.stopRisk(stopId))}catch(err){setResult({error:err.message})}finally{setBusy(false)}}
  return <Shell title="Routes & risk"><Heading eyebrow="LAYER 2 · LAST MILE" title="Route and delivery risk" description="Inspect a route stop, retrieve its live failure probability, and connect the result to customer availability." />
    <div className="route-layout"><Panel className="route-map"><div className="panel-head"><div><p className="eyebrow">ROUTE R-00143</p><h2>Delivery sequence</h2></div><Badge tone="blue">IN TRANSIT · EXAMPLE</Badge></div><div className="route-line">{[['1','Origin','done'],['2','B-21.1A','done'],['3','B-24.2C','risk'],['4','P-12.3C','pending'],['5','P-13.2A','pending']].map(([n,label,state])=><button className={`route-stop ${state}`} key={n} onClick={()=>label.includes('-')&&setStopId(label)}><span>{n}</span><b>{label}</b><small>{state==='risk'?'Selected stop':state==='done'?'Completed':'Upcoming'}</small></button>)}</div><div className="legend"><span><i className="green-dot"/>Complete</span><span><i className="orange-dot"/>Selected stop</span><span><i className="gray-dot"/>Upcoming</span></div></Panel>
      <Panel><p className="eyebrow">STOP RISK MODEL</p><h2>Assess failure probability</h2><p className="panel-copy">Risk output is retrieved from the delivery service; no probability is fabricated in the interface.</p><form onSubmit={check} className="inline-form"><label>Stop ID<input required value={stopId} onChange={e=>setStopId(e.target.value)} /></label><button className="button primary" disabled={busy}>{busy?'Checking…':'Check live risk'}</button></form><div className="risk-empty"><span>◎</span><b>Risk result will appear below</b><small>Uses configured delivery model endpoint</small></div><a className="text-link" href="/whatsapp">Open customer interaction →</a></Panel></div>
    <Panel className="model-note"><h2>Risk context</h2><p>Route, station, capacity, zone, stop and package counts, service time, time window, and historical outcomes may contribute to the trained model result.</p></Panel><Result value={result}/>
  </Shell>
}

function WhatsApp() {
  return <Shell title="Customer WhatsApp"><Heading eyebrow="CUSTOMER AVAILABILITY" title="WhatsApp coordination" description="See the customer response state alongside the delivery decision it informs." action={<Badge tone="purple">CONFIRMATION PENDING</Badge>} />
    <div className="chat-layout"><Panel className="chat-card"><div className="chat-head"><span className="avatar">1042</span><div><b>Customer #1042</b><small>Shipment ORD-1042 · Stop B-24.2C</small></div><Badge tone="purple">PENDING</Badge></div><div className="chat-body"><div className="chat-date">TODAY · DELIVERY CONFIRMATION</div><div className="bubble bot">Your delivery is planned for today. Will someone be available to receive the package?<small>AI assistant · awaiting send/response integration</small></div><div className="bubble customer">I may be home around 6.<small>Example conversation</small></div><div className="bubble bot">Would you like to review available delivery options?<small>AI assistant · example</small></div><div className="chat-compose"><span>WhatsApp messaging is managed by the connected service</span><button disabled aria-label="Send message">↑</button></div></div></Panel>
    <Panel><p className="eyebrow">DELIVERY DECISION</p><h2>Customer state</h2><div className="state-list">{[['Contact initiated','done'],['Waiting for response','current'],['Availability confirmed','pending'],['Plan re-ranked','pending'],['Delivery outcome','pending']].map(([x,s])=><div className={`state-row ${s}`} key={x}><i/>{x}</div>)}</div><div className="slot-note"><b>Alternative slots</b><p>Slots and success estimates should come from the decision service. None are available from the current frontend API contract.</p></div><a className="button secondary full-button" href="/journey">See this shipment journey</a></Panel></div>
  </Shell>
}

function OrderJourney() {
  return <Shell title="Order 360 journey"><Heading eyebrow="END-TO-END TRACKING" title="One shipment, both operational layers" description="A single view connects warehouse priority, dispatch, delivery risk, customer WhatsApp, re-ranking, and outcome." action={<Badge tone="orange">DEMO WALKTHROUGH</Badge>} />
    <div className="journey-hero"><div><p className="eyebrow">SHIPMENT</p><h2>ORD-1042</h2><p>Customer #1042 · 4 items · Picking wave W-43175</p></div><div className="hero-status"><Badge tone="red">CRITICAL PICK PRIORITY</Badge><span>Current stage: delivery planning</span></div></div>
    <Panel className="timeline-panel"><h2>Shipment event timeline</h2><div className="event-timeline">{[['10:02','Order created','Order received by warehouse'],['10:08','Picking wave assigned','W-43175 · 3 locations'],['10:19','AI priority assigned','Critical · warehouse model'],['10:37','Picking completed','Ready for dispatch'],['10:42','Dispatch unit assigned','DU-03'],['11:05','Route generated','R-00143 · stop B-24.2C'],['11:06','Delivery risk assessment','Retrieve current risk from live model'],['11:07','Customer contacted','WhatsApp availability pending'],['—','Re-rank & delivery','Waiting for customer and backend outcome']].map(([time,title,detail],i)=><div className={`event ${i<6?'complete':''}`} key={title}><time>{time}</time><i/><div><b>{title}</b><span>{detail}</span></div></div>)}</div></Panel>
    <div className="journey-actions"><a className="button secondary" href="/warehouse">Warehouse & priority</a><a className="button secondary" href="/dispatch">Dispatch unit</a><a className="button secondary" href="/delivery">Route & live risk</a><a className="button primary" href="/whatsapp">Customer WhatsApp</a></div>
    <Panel className="notice"><span className="notice-mark">i</span><p>Timeline identifiers and timestamps are illustrative demo content. Replace with persisted shipment events when the order tracking endpoint is available.</p></Panel>
  </Shell>
}

function LegalPage({type}) { const privacy=type==='privacy';return <Shell title={privacy?'Privacy':'Terms'}><Heading eyebrow="LEGAL" title={privacy?'Privacy policy':'Terms and conditions'} description="Last updated October 2, 2026"/><Panel className="legal-copy"><h2>{privacy?'Information handled by this application':'Using this service'}</h2><p>This operations interface sends submitted identifiers and files to the configured logistics API. Predictions are decision support and should be reviewed alongside operational constraints and customer preferences.</p><h2>Service operator</h2><p>Processing, retention, and support details are managed by the organization operating the connected service.</p></Panel></Shell> }

export default function App() {
  const path=window.location.pathname.replace(/\/$/,'')||'/'
  if(path==='/warehouse')return <Warehouse/>;if(path==='/dispatch')return <Dispatch/>;if(path==='/delivery')return <Delivery/>;if(path==='/whatsapp')return <WhatsApp/>;if(path==='/journey')return <OrderJourney/>;if(path==='/privacy')return <LegalPage type="privacy"/>;if(path==='/terms')return <LegalPage type="terms"/>;return <Dashboard/>
}
