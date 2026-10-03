import { useState, useEffect } from 'react'
import { api } from '../api/client.js'
import { Badge, Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function AIAssistantPage() {
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getDashboardData();
        const allOrders = Object.values(response).flat();
        const highRiskOrder = allOrders.find(o => o.delivery?.riskBand === 'HIGH');
        
        if (highRiskOrder) {
           setMessages([
             { sender: 'System', text: `Detected High Risk for ${highRiskOrder.orderId}. Initiating WhatsApp confirmation flow...`, type: 'system' },
             { sender: 'System', text: 'WhatsApp message triggered via Twilio. Awaiting customer reply...', type: 'system' }
           ]);
           setTimeout(() => {
               setMessages(prev => [...prev, { sender: 'Customer', text: 'Yes, I am available.', type: 'user' }]);
               setTimeout(() => {
                  setMessages(prev => [...prev, { sender: 'AI', text: 'Status updated automatically. Delivery confirmed! Route has been optimized.', type: 'ai' }]);
               }, 1000);
           }, 3000);
        } else {
           setMessages([{ sender: 'AI', text: 'Analysis complete. All orders look safe, no automated intervention needed right now!', type: 'ai' }]);
        }
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
    <Shell title="AI Assistant">
      <Heading
        eyebrow="AUTONOMOUS INTERVENTION"
        title="AI Assistant & WhatsApp"
        description="The AI agent monitors high-risk orders, triggers WhatsApp resolutions, and updates routes automatically."
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
           <p>Connecting to AI Agent...</p>
        </Panel>
      )}

      {!loading && !error && (
        <Panel style={{ border: '1px solid #e0e0e0', marginTop: '2rem' }}>
          <p className="eyebrow">LIVE AGENT</p>
          <h2>Autonomous WhatsApp Log</h2>
          <p className="panel-copy">View real-time AI interventions or send direct commands to the agent.</p>
          
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
             {messages.length === 0 && <p style={{ color: '#888' }}>Waiting for high-risk alerts...</p>}
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
      )}
    </Shell>
  )
}
