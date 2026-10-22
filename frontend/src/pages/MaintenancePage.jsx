import { useState } from 'react'
import { Link } from 'react-router-dom'
import './MaintenancePage.css'

// Halaman yang tampil otomatis saat server/database (Neon) tidak bisa diakses
export default function MaintenancePage({ onRetry }) {
  const [checking, setChecking] = useState(false)
  const [stillDown, setStillDown] = useState(false)

  async function handleRetry() {
    setChecking(true)
    try {
      setStillDown(await onRetry())
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="maintenance-page">
      <header className="maintenance-header">
        <Link className="maintenance-brand" to="/" aria-label="FitMindAI, beranda">
          FitMind<span>AI</span>
        </Link>
      </header>

      <main className="maintenance-main">
        <section className="maintenance-card" aria-labelledby="maintenance-title">
          <div className="maintenance-icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
            </svg>
          </div>

          <h1 id="maintenance-title">SEDANG DALAM <span>PEMELIHARAAN</span></h1>
          <p>
            Server FitMindAI sedang tidak dapat diakses untuk sementara. Kami sedang memulihkan
            layanan secepatnya, silakan kembali beberapa saat lagi.
          </p>

          <div className="maintenance-status" aria-live="polite">
            <span className="maintenance-status-dot" aria-hidden="true" />
            {checking
              ? 'Memeriksa status server…'
              : stillDown
                ? 'Server belum tersedia. Kami akan memeriksa ulang otomatis.'
                : 'Cek ulang otomatis setiap 60 detik'}
          </div>

          <div className="maintenance-actions">
            <button className="maintenance-button maintenance-button-primary" type="button" onClick={handleRetry} disabled={checking}>
              {checking ? 'Memeriksa…' : 'Coba lagi'}
            </button>
            <Link className="maintenance-button maintenance-button-secondary" to="/">Kembali ke beranda</Link>
          </div>
        </section>
      </main>

      <footer className="maintenance-footer">© {new Date().getFullYear()} FitMindAI</footer>
    </div>
  )
}
