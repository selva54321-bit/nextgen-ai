import { NavLink, Link } from 'react-router-dom'

export const nav = [
  ['/', 'Command center', '⌂'],
  ['/warehouse', 'Warehouse & priority', '▦'],
  ['/dispatch', 'Dispatch units', '⇢'],
  ['/delivery', 'Routes & risk', '⌖'],
  ['/whatsapp', 'Customer WhatsApp', '◉'],
  ['/journey', 'Order 360 journey', '↗'],
]

export function Shell({ children, title }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-mark">N</span>
          <span>
            NextGen<small>LOGISTICS CONTROL</small>
          </span>
        </Link>
        <p className="nav-label">OPERATIONS</p>
        <nav>
          {nav.map(([href, label, icon]) => (
            <NavLink
              key={href}
              to={href}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="status-dot" />
          Backend connection configured
          <small>Live data depends on service availability</small>
        </div>
      </aside>

      <div className="content-area">
        <header className="topbar">
          <span>
            Operations <b>/</b> {title}
          </span>
          <span className="live-tag">
            <i /> CONTROL CENTER
          </span>
        </header>

        <main className="page-content">{children}</main>

        <footer className="site-footer">
          <span>NextGen Logistics · Operations workspace</span>
          <span>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
          </span>
        </footer>
      </div>
    </div>
  )
}
