import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import DashboardPage from './pages/DashboardPage.jsx'
import WarehousePage from './pages/WarehousePage.jsx'
import DispatchPage from './pages/DispatchPage.jsx'
import DeliveryPage from './pages/DeliveryPage.jsx'
import WhatsAppPage from './pages/WhatsAppPage.jsx'
import OrderJourneyPage from './pages/OrderJourneyPage.jsx'
import LegalPage from './pages/LegalPage.jsx'

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/warehouse" element={<WarehousePage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/delivery" element={<DeliveryPage />} />
        <Route path="/whatsapp" element={<WhatsAppPage />} />
        <Route path="/journey" element={<OrderJourneyPage />} />
        <Route path="/privacy" element={<LegalPage type="privacy" />} />
        <Route path="/terms" element={<LegalPage type="terms" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
