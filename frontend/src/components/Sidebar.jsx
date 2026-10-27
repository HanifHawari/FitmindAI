import { Link, NavLink } from 'react-router-dom'
import { useState } from 'react'
import UserAvatar from './UserAvatar'

// Ikon menu dari public/icons/menu. PNG dipakai sebagai mask CSS supaya
// warnanya mengikuti `color` menu (abu-abu biasa, hijau saat aktif).
function NavIcon({ src }) {
  return <span className="nav-icon" style={{ '--nav-icon': `url(${src})` }} aria-hidden="true" />
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '/icons/menu/dashboard.png' },
  { to: '/chat',      label: 'AI Chat',   icon: '/icons/menu/ai-chat.png'   },
  { to: '/plan',      label: 'AI Plan',   icon: '/icons/menu/ai-plan.png'   },
  { to: '/nutrition', label: 'Nutrition', icon: '/icons/menu/nutrition.png' },
  { to: '/workout',   label: 'Workout',   icon: '/icons/menu/workout.png'   },
  { to: '/profile',   label: 'Profile',   icon: '/icons/menu/profile.png'   },
]

export default function Sidebar({ username, avatarData }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  function handleLogout() {
    localStorage.removeItem('fitmind_token')
    localStorage.removeItem('fitmind_user')
    localStorage.removeItem('fitmind_profile')
    setMobileOpen(false)
    window.location.href = '/'
  }

  return (
    <>
      {/* ── Mobile Top Bar ──────────────────────────────────── */}
      <div className="sidebar-mobile-bar">
        <button
          className="sidebar-menu-button"
          onClick={() => setMobileOpen(prev => !prev)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? '✕' : '☰'}
        </button>
        <div className="sidebar-mobile-title"><small>FITMIND AI</small><strong>Halo, {username || 'Atlet'}</strong></div>
        <Link to="/profile" aria-label="Buka profil" className="sidebar-mobile-avatar">
          <UserAvatar username={username} avatarData={avatarData} size={42} />
        </Link>
      </div>

      {/* ── Mobile Drawer Overlay ───────────────────────────── */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className={`sidebar-aside ${mobileOpen ? 'sidebar-open' : ''}`}>
        {/* Logo (Desktop) */}
        <div className="sidebar-logo">
          <Link to="/dashboard" className="sidebar-brand">FitMind<span>AI</span></Link>
        </div>
        <Link to="/profile" className="sidebar-user">
          <UserAvatar username={username} avatarData={avatarData} size={42} />
          <span><strong>{username || 'Atlet'}</strong><small>Lihat profil</small></span>
        </Link>

        {/* Navigation */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/dashboard'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              <span className="nav-icon-bg">
                <NavIcon src={item.icon} />
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="btn-ghost sidebar-logout"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Logout
        </button>
      </aside>

      <nav className="sidebar-bottom-nav" aria-label="Navigasi utama">
        {navItems.filter(item => item.to !== '/nutrition').map(item => (
          <NavLink key={item.to} to={item.to} end={item.to === '/dashboard'}>
            <NavIcon src={item.icon} />
            <span>{item.to === '/dashboard' ? 'Home' : item.to === '/plan' ? 'Plan' : item.to === '/profile' ? 'Profil' : item.label}</span>
          </NavLink>
        ))}
      </nav>

      <style>{`
        /* ── Desktop Sidebar ── */
        .sidebar-aside {
          width: 220px;
          min-height: 100vh;
          background: #111111;
          border-right: 1px solid #2a2a2a;
          display: flex;
          flex-direction: column;
          padding: 24px 12px;
          position: fixed;
          top: 0;
          left: 0;
          z-index: 200;
          overflow-y: auto;
          box-sizing: border-box;
        }
        .sidebar-logo {
          padding-left: 14px;
          margin-bottom: 32px;
        }
        .sidebar-mobile-bar {
          display: none;
        }
        .sidebar-overlay {
          display: none;
        }
        .sidebar-logout {
          width: 100%;
          text-align: left;
          margin-top: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        /* Nav icon background */
        .nav-icon-bg {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 30px;
          height: 30px;
          border-radius: 8px;
          background: rgba(163,163,163,0.06);
          flex-shrink: 0;
          transition: background 0.2s;
        }
        .nav-item.active .nav-icon-bg {
          background: rgba(34,197,94,0.12);
        }
        .nav-icon {
          width: 20px;
          height: 20px;
          flex-shrink: 0;
          background-color: currentColor;
          -webkit-mask: var(--nav-icon) center / contain no-repeat;
          mask: var(--nav-icon) center / contain no-repeat;
          opacity: 0.45;
        }
        .nav-item.active .nav-icon {
          opacity: 0.8;
        }
        .nav-item:hover .nav-icon-bg {
          background: rgba(163,163,163,0.1);
        }

        /* ── Mobile ── */
        @media (max-width: 768px) {
          .sidebar-aside {
            top: 72px;
            height: calc(100dvh - 72px);
            transform: translateX(-100%);
            transition: transform 0.3s ease;
            /* Padding bottom agar ada sedikit ruang saat scroll sampai bawah */
            padding-bottom: 16px;
          }
          .sidebar-aside.sidebar-open {
            transform: translateX(0);
          }
          .sidebar-logo {
            display: none;
          }
          .sidebar-mobile-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 72px;
            background: #111111;
            border-bottom: 1px solid #2a2a2a;
            padding: 0 16px;
            z-index: 300;
          }
          .sidebar-overlay {
            display: block;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.6);
            z-index: 150;
          }

        }
      `}</style>
    </>
  )
}
