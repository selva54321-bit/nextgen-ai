import { useState } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function DispatchPage() {
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { sender: 'System', text: 'Detected High Risk for ORD-1042. Initiating WhatsApp confirmation flow...', type: 'system' },
    { sender: 'System', text: 'WhatsApp message triggered via Twilio. Awaiting customer reply...', type: 'system' },
    { sender: 'Customer', text: 'Yes, I am available.', type: 'user' },
    { sender: 'AI', text: 'Status updated automatically. Delivery confirmed! Route has been optimized.', type: 'ai' }
  ]);

  const handleChat = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setMessages([...messages, { sender: 'You', text: chatInput, type: 'user' }]);
    setChatInput('');
    setTimeout(() => {
        setMessages(prev => [...prev, { sender: 'AI', text: 'I am monitoring the network and will update systems automatically.', type: 'ai' }]);
    }, 1000);
  }

  return (
    <Shell title="Dispatch & Risk Analysis">
      <Heading
        eyebrow="AI DELIVERY PREDICTION"
        title="Dispatch Control Center"
        description="Analyze delivery risks and coordinate automated WhatsApp interventions."
      />

      {/* Top: Risk breakdown */}
      <div className="metric-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem', marginTop: '2rem' }}>
        <Panel>
          <span className="metric-label">HIGH RISK</span>
          <b className="metric-value" style={{ color: '#d93025' }}>15%</b>
          <span className="metric-note">24 Orders</span>
        </Panel>
        <Panel>
          <span className="metric-label">MEDIUM RISK</span>
          <b className="metric-value" style={{ color: '#f29900' }}>30%</b>
          <span className="metric-note">48 Orders</span>
        </Panel>
        <Panel>
          <span className="metric-label">LOW RISK</span>
          <b className="metric-value" style={{ color: '#1e8e3e' }}>55%</b>
          <span className="metric-note">88 Orders</span>
        </Panel>
      </div>

      {/* Center: Risk Card */}
      <Panel style={{ marginTop: '2rem' }}>
        <p className="eyebrow">RISK ANALYSIS</p>
        <h2>Delivery Risk Details</h2>
        <div style={{ display: 'flex', gap: '3rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
           <div style={{ flex: 1, minWidth: '250px' }}>
             <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
               Risk Score: <span style={{ color: '#d93025' }}>0.072 (HIGH)</span>
             </h3>
             <p style={{ color: '#555', lineHeight: '1.5' }}>
               Failure probability is elevated for recent batches. The ML model predicts potential delivery failures if no intervention is taken.
             </p>
             <Badge tone="red" style={{ marginTop: '1rem' }}>REQUIRES INTERVENTION</Badge>
           </div>
           <div style={{ flex: 1, minWidth: '250px', background: '#f8f9fa', padding: '1.5rem', borderRadius: '8px' }}>
             <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#333' }}>Top 3 Risk Factors:</h3>
             <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', paddingLeft: '1.2rem', color: '#444' }}>
               <li><b>route_num_stops:</b> Too many stops on the route</li>
               <li><b>total_service_time:</b> Exceeds SLA delivery window</li>
               <li><b>has_time_window:</b> Strict deadline constraints</li>
             </ul>
           </div>
        </div>
      </Panel>

      {/* Finally: AI Assistant */}
      <Panel style={{ marginTop: '2rem', border: '1px solid #e0e0e0' }}>
        <p className="eyebrow">AI ASSISTANT</p>
        <h2>Autonomous WhatsApp Resolutions</h2>
        <p className="panel-copy">The AI agent automatically triggers WhatsApp messages for appropriate reasons and updates the backend.</p>
        
        <div style={{ 
          background: '#f8f9fa', 
          padding: '1.5rem', 
          borderRadius: '8px', 
          minHeight: '250px', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '1rem',
          marginTop: '1.5rem',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
           {messages.map((msg, i) => (
             <div key={i} style={{ 
               alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start', 
               background: msg.type === 'user' ? '#1a73e8' : (msg.type === 'ai' ? '#e8f0fe' : '#e0e0e0'), 
               color: msg.type === 'user' ? 'white' : '#202124', 
               padding: '0.75rem 1.25rem', 
               borderRadius: '12px',
               maxWidth: '80%',
               fontSize: '0.95rem'
             }}>
                <b style={{ display: 'block', fontSize: '0.8rem', opacity: 0.8, marginBottom: '0.2rem' }}>{msg.sender}</b>
                {msg.text}
             </div>
           ))}
        </div>
        
        <form onSubmit={handleChat} style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
           <input 
             type="text" 
             value={chatInput}
             onChange={(e) => setChatInput(e.target.value)}
             placeholder="Type a command to the AI Assistant..." 
             style={{ 
               flex: 1, 
               padding: '0.75rem 1rem', 
               borderRadius: '6px', 
               border: '1px solid #ccc',
               fontSize: '1rem'
             }} 
           />
           <button type="submit" className="button primary" style={{ padding: '0 2rem' }}>Send</button>
        </form>
      </Panel>
    </Shell>
  )
}
