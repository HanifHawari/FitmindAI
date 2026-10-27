import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './LandingPage.css'

const navItems = [
  { label: 'Manfaat', href: '#manfaat' },
  { label: 'Fitur', href: '#fitur' },
  { label: 'AI Chat', href: '#ai-chat' },
  { label: 'FAQ', href: '#faq' },
]

const problems = [
  {
    title: 'Bingung memilih latihan',
    solution: 'Buat rencana latihan berdasarkan tujuan, level, jumlah hari, dan peralatanmu.',
  },
  {
    title: 'Sulit mengatur makanan',
    solution: 'Cari makanan, gunakan filter alergen, dan susun meal plan dari satu tempat.',
  },
  {
    title: 'Informasi tersebar',
    solution: 'Akses AI Chat, kalkulator kebugaran, workout, dan nutrisi melalui satu aplikasi.',
  },
]

const features = [
  {
    title: 'AI Chat',
    description: 'Tanyakan hal seputar latihan, nutrisi, dan kebugaran. Kamu juga dapat membuka kembali riwayat percakapan.',
    to: '/chat',
    image: '/foto6.jpg',
  },
  {
    title: 'AI Plan',
    description: 'Buat rencana workout atau meal plan dengan pilihan tujuan, tingkat pengalaman, peralatan, dan preferensi makan.',
    to: '/plan',
    image: '/foto7.jpg',
  },
  {
    title: 'Nutrisi & Alergen',
    description: 'Cari informasi makanan, jelajahi makanan sehat, dan saring hasil berdasarkan pantangan tertentu.',
    to: '/nutrition',
    image: '/foto9.jpg',
  },
  {
    title: 'Workout',
    description: 'Temukan gerakan berdasarkan nama atau bagian tubuh, lalu jelajahi daftar program menurut level.',
    to: '/workout',
    image: '/foto8.jpg',
  },
  {
    title: 'Smart Tools',
    description: 'Gunakan kalkulator BMI, estimasi kalori latihan, dan analisis zona detak jantung di dashboard.',
    to: '/dashboard',
    image: '/foto10.jpg',
  },
]

const highlights = [
  { image: '/foto1.jpg', to: '/workout', label: 'Jelajahi Workout' },
  { image: '/foto2.jpg', to: '/plan', label: 'Buat AI Plan' },
  { image: '/foto4.jpg', to: '/chat', label: 'Buka AI Chat' },
]

const gallery = [
  { image: '/foto3.jpg', title: 'Mulai bergerak', to: '/workout' },
  { image: '/foto5.jpg', title: 'Tentukan tujuan', to: '/plan' },
  { image: '/foto11.jpg', title: 'Bangun kebiasaan', to: '/dashboard' },
  { image: '/foto12.jpg', title: 'Terus berkembang', to: '/workout' },
  { image: '/foto13.jpg', title: 'Temukan ritmemu', to: '/workout' },
]

const questions = [
  {
    question: 'Apakah saya memerlukan email untuk mendaftar?',
    answer: 'Tidak. Form pendaftaran saat ini meminta username, nomor WhatsApp, dan password.',
  },
  {
    question: 'Apakah rencana latihan langsung dibuat setelah daftar?',
    answer: 'Setelah masuk, buka AI Plan dan pilih tujuan, level, hari latihan, serta peralatan. Rencana dibuat ketika kamu menekan tombol Generate.',
  },
  {
    question: 'Bisakah saya mencari makanan sesuai pantangan?',
    answer: 'Pencarian makanan menyediakan filter untuk gluten, susu, kacang, kedelai, telur, dan ikan. Tetap periksa informasi produk sebelum dikonsumsi.',
  },
  {
    question: 'Apa saja yang ada di dashboard?',
    answer: 'Dashboard menyediakan kalkulator BMI, estimasi kalori latihan, dan analisis zona detak jantung. Masukkan data yang diminta untuk melihat hasilnya.',
  },
]

const iconPaths = {
  arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  check: <><path d="m5 12 4 4L19 6" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  close: <><path d="M5 5l14 14M19 5 5 19" /></>,
}

function Icon({ name, size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {iconPaths[name]}
    </svg>
  )
}
function SectionHeading({ title, description }) {
  return (
    <div className="landing-section-heading landing-reveal" data-reveal>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  )
}

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)
  const pageRef = useRef(null)
  const headerRef = useRef(null)
  const highlightRef = useRef(null)
  const navigate = useNavigate()

  // Link ke halaman aplikasi (login, daftar, fitur): navigasi SPA tanpa reload
  const handleAuthClick = (e) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return // biarkan buka di tab baru
    e.preventDefault()
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'instant' })
    navigate(e.currentTarget.getAttribute('href'))
  }

  // Menu dropdown mobile: tutup dengan Escape atau ketukan di luar header
  useEffect(() => {
    if (!menuOpen) return
    const closeOnEscape = (e) => { if (e.key === 'Escape') setMenuOpen(false) }
    const closeOnOutsideTap = (e) => { if (!headerRef.current?.contains(e.target)) setMenuOpen(false) }
    document.addEventListener('keydown', closeOnEscape)
    document.addEventListener('pointerdown', closeOnOutsideTap)
    return () => {
      document.removeEventListener('keydown', closeOnEscape)
      document.removeEventListener('pointerdown', closeOnOutsideTap)
    }
  }, [menuOpen])

  useEffect(() => {
    const page = pageRef.current
    if (!page || !('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const observer = new IntersectionObserver((entries, activeObserver) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          activeObserver.unobserve(entry.target)
        }
      })
    }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' })

    page.classList.add('has-scroll-animations')
    page.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element))

    return () => {
      observer.disconnect()
      page.classList.remove('has-scroll-animations')
    }
  }, [])

  // Foto highlight di mobile: slider yang bisa digeser (sentuh atau drag mouse)
  // dan bergeser otomatis tiap 2 detik selama terlihat di layar
  useEffect(() => {
    const track = highlightRef.current
    if (!track) return
    const mobile = window.matchMedia('(max-width: 640px)')
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let timer = null
    let inView = false
    let drag = null
    let suppressClick = false

    const cards = () => Array.from(track.children)
    const offsetOf = index => cards()[index].offsetLeft - cards()[0].offsetLeft
    const nearestIndex = () => {
      const offsets = cards().map((_, index) => Math.abs(offsetOf(index) - track.scrollLeft))
      return offsets.indexOf(Math.min(...offsets))
    }
    const scrollToIndex = index => track.scrollTo({ left: offsetOf(index), behavior: 'smooth' })
    const next = () => {
      const atEnd = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2
      const index = nearestIndex() + 1
      scrollToIndex(atEnd || index >= cards().length ? 0 : index)
    }
    const stop = () => { clearInterval(timer); timer = null }
    const start = () => {
      stop()
      if (mobile.matches && inView && !reducedMotion && !drag) timer = setInterval(next, 2000)
    }

    const onPointerDown = e => {
      if (e.pointerType !== 'mouse' || e.button !== 0 || !mobile.matches) return
      drag = { x: e.clientX, left: track.scrollLeft, moved: false }
      track.classList.add('is-dragging')
      stop()
    }
    const onPointerMove = e => {
      if (!drag) return
      const dx = e.clientX - drag.x
      if (Math.abs(dx) > 5) drag.moved = true
      track.scrollLeft = drag.left - dx
    }
    const onPointerUp = () => {
      if (!drag) return
      track.classList.remove('is-dragging')
      if (drag.moved) {
        suppressClick = true // drag tidak boleh dianggap klik pada kartu
        setTimeout(() => { suppressClick = false }, 0)
        scrollToIndex(nearestIndex())
      }
      drag = null
      start()
    }
    const onClickCapture = e => {
      if (!suppressClick) return
      e.preventDefault()
      e.stopPropagation()
    }
    const preventNativeDrag = e => e.preventDefault()

    const observer = new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting
      start()
    }, { threshold: 0.4 })
    observer.observe(track)

    track.addEventListener('pointerdown', onPointerDown)
    track.addEventListener('click', onClickCapture, true)
    track.addEventListener('dragstart', preventNativeDrag)
    track.addEventListener('touchstart', stop, { passive: true })
    track.addEventListener('touchend', start)
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
    mobile.addEventListener('change', start)

    return () => {
      stop()
      observer.disconnect()
      track.removeEventListener('pointerdown', onPointerDown)
      track.removeEventListener('click', onClickCapture, true)
      track.removeEventListener('dragstart', preventNativeDrag)
      track.removeEventListener('touchstart', stop)
      track.removeEventListener('touchend', start)
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
      mobile.removeEventListener('change', start)
    }
  }, [])

  useEffect(() => {
    const videos = pageRef.current?.querySelectorAll('[data-play-on-view]')
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      pageRef.current?.querySelectorAll('video').forEach(item => item.pause())
      return
    }
    if (!videos?.length) return

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.play().catch(() => {})
        else entry.target.pause()
      })
    }, { rootMargin: '120px 0px' })

    videos.forEach(video => observer.observe(video))
    return () => {
      observer.disconnect()
      videos.forEach(video => video.pause())
    }
  }, [])

  return (
    <div className="landing-page" ref={pageRef}>
      <header className="landing-header" ref={headerRef}>
        <div className="landing-shell landing-header-inner">
          <Link className="landing-brand" to="/" aria-label="FitMindAI, beranda">
            FitMind<span>AI</span>
          </Link>

          <nav id="landing-navigation" className={'landing-nav' + (menuOpen ? ' is-open' : '')} aria-label="Navigasi landing page">
            {navItems.map((item, index) => (
              <a key={item.href} href={item.href} style={{ '--landing-nav-index': index }} onClick={() => setMenuOpen(false)}>{item.label}</a>
            ))}
          </nav>

          <div className="landing-header-actions">
            <a className="landing-login-link" href="/login" onClick={handleAuthClick}>Masuk</a>
            <a className="landing-button landing-button-primary" href="/register" onClick={handleAuthClick}>Daftar Gratis</a>
          </div>
          <button
            className="landing-menu-button"
            type="button"
            aria-label={menuOpen ? 'Tutup menu' : 'Buka menu'}
            aria-controls="landing-navigation"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(open => !open)}
          >
            <Icon name={menuOpen ? 'close' : 'menu'} />
          </button>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-videos" aria-hidden="true">
            <video src="/vid2.mp4" autoPlay loop muted playsInline preload="metadata" />
            <video src="/vid3.mp4" autoPlay loop muted playsInline preload="metadata" />
            <video src="/vid4.mp4" autoPlay loop muted playsInline preload="metadata" />
          </div>
          <div className="landing-shell landing-hero-grid">
            <div className="landing-hero-copy">
              <h1>GO FURTHER IN LIFE<br />LATIH LEBIH <span>CERDAS</span><br />BERSAMA AI</h1>
              <p>Program latihan terukur, perencanaan nutrisi spesifik bebas alergen, dan asisten sains olahraga.</p>
              <div className="landing-hero-actions">
                <a className="landing-button landing-button-primary landing-button-large" href="/register" onClick={handleAuthClick}>
                  Daftar Sekarang
                </a>
                <a className="landing-button landing-button-secondary landing-button-large" href="#fitur">Pelajari Fitur</a>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-highlights" aria-label="Jelajahi FitMindAI">
          <div className="landing-shell landing-highlight-grid" ref={highlightRef} data-reveal>
            {highlights.map((item, index) => (
              <a className={'landing-highlight-card landing-highlight-card-' + (index + 1)} key={item.to} href={item.to} aria-label={item.label} onClick={handleAuthClick}>
                <img className="landing-highlight-media" src={item.image} alt="" loading="lazy" />
              </a>
            ))}
          </div>
        </section>

        <section id="manfaat" className="landing-section landing-section-alt">
          <div className="landing-shell landing-benefit-grid">
            <div className="landing-benefit-copy landing-reveal" data-reveal>
              <h2>Hentikan latihan tanpa arah dan <span>Mulai dengan rencana yang jelas</span></h2>
              <p className="landing-benefit-intro">FitMindAI membantu menghubungkan pilihan latihan, nutrisi, dan informasi kebugaran dalam satu alur.</p>
              <div className="landing-benefit-list landing-cascade" data-reveal>
                {problems.map(problem => (
                  <article className="landing-benefit-item" key={problem.title}>
                    <span className="landing-benefit-check"><Icon name="check" size={19} /></span>
                    <div>
                      <h3>{problem.title}</h3>
                      <p>{problem.solution}</p>
                    </div>
                  </article>
                ))}
              </div>
              <a className="landing-button landing-button-primary" href="#fitur">Jelajahi fitur</a>
            </div>
            <div className="landing-benefit-photo landing-reveal" data-reveal>
              <video src="/vid1.mp4" poster="/foto3.jpg" muted loop playsInline preload="none" aria-hidden="true" data-play-on-view />
            </div>
          </div>
        </section>

        <section id="fitur" className="landing-section">
          <div className="landing-shell">
            <SectionHeading
              title="SEMUA KEBUTUHAN KEBUGARANMU DALAM SATU PLATFORM"
              description="Pilih fitur yang kamu perlukan, dari mencari gerakan hingga membuat rencana latihan dan makan."
            />
            <div className="landing-marquee-outer" aria-label="Fitur FitMindAI">
              <div className="landing-marquee-track">
                {[...features, ...features].map((feature, i) => (
                  <a className="landing-feature-card" href={feature.to} key={feature.title + i} onClick={handleAuthClick}>
                    <img className="landing-feature-media" src={feature.image} alt="" loading="lazy" />
                    <span className="landing-feature-shade" aria-hidden="true" />
                    <span className="landing-feature-content">
                      <h3>{feature.title}</h3>
                      <p>{feature.description}</p>
                    </span>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </section>





        <section id="ai-chat" className="landing-section landing-chat-section">
          <video className="landing-chat-video" src="/gym_bg.mp4" poster="/foto4.jpg" muted loop playsInline preload="none" aria-hidden="true" data-play-on-view />
          <div className="landing-shell landing-chat-grid">
            <div className="landing-chat-copy landing-reveal" data-reveal>
              <h2>Ada pertanyaan tentang latihan atau nutrisi?</h2>
              <p>Buka AI Chat untuk mengajukan pertanyaan. Percakapanmu tersimpan sehingga dapat dibaca kembali saat dibutuhkan.</p>
            </div>
            <div className="landing-chat-preview landing-reveal" data-reveal>
              <div className="landing-chat-preview-header">
                <span className="landing-chat-avatar"><span className="landing-chat-avatar-icon" aria-hidden="true" /></span>
                <div><strong>FitMindAI Chat</strong><small>Contoh topik yang bisa ditanyakan</small></div>
              </div>
              <div className="landing-chat-preview-body">
                <p>Mulai dari pertanyaan yang paling dekat dengan rutinitasmu.</p>
                <div className="landing-chat-suggestions">
                  <span>Bagaimana memilih latihan untuk pemula?</span>
                  <span>Apa informasi nutrisi makanan ini?</span>
                  <span>Bagaimana menyusun jadwal latihan?</span>
                </div>
              </div>
              <div className="landing-chat-preview-input">Tulis pertanyaanmu di AI Chat <Icon name="arrow" size={18} /></div>
            </div>
          </div>
        </section>

        <section className="landing-section landing-gallery" aria-label="Inspirasi aktivitas">
          <div className="landing-shell">
            <SectionHeading
              title="Temukan ritme yang cocok untukmu."
              description="Pilih titik awalmu, susun rencana, lalu gunakan fitur yang kamu perlukan sepanjang perjalanan."
            />
            <div className="landing-gallery-grid landing-cascade" data-reveal>
              {gallery.map(item => (
                <a className="landing-gallery-card" href={item.to} key={item.title} onClick={handleAuthClick}>
                  <img src={item.image} alt="" loading="lazy" />
                  <span>{item.title}</span>
                </a>
              ))}
            </div>
          </div>
        </section>

        <section id="faq" className="landing-section landing-section-alt">
          <div className="landing-shell">
            <SectionHeading
              title="Hal yang sering ditanyakan."
              description="Kenali alur aplikasi sebelum memulai."
            />
            <div className="landing-faq-list landing-cascade" data-reveal>
              {questions.map((item, index) => (
                <details key={item.question} open={index === 0}>
                  <summary>{item.question}<span aria-hidden="true">+</span></summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

      </main>

      <footer className="landing-footer">
        <div className="landing-shell landing-footer-grid landing-reveal" data-reveal>
          <div>
            <Link className="landing-brand" to="/">FitMind<span>AI</span></Link>
            <p>Platform kebugaran berbasis AI untuk latihan, nutrisi, dan rencana yang lebih terarah.</p>
          </div>
          <nav aria-label="Jelajahi"><h3>Jelajahi</h3>{navItems.map(item => <a key={item.href} href={item.href}>{item.label}</a>)}</nav>
          <nav aria-label="Aplikasi"><h3>Aplikasi</h3><a href="/plan" onClick={handleAuthClick}>AI Plan</a><a href="/nutrition" onClick={handleAuthClick}>Nutrisi</a><a href="/workout" onClick={handleAuthClick}>Workout</a></nav>
          <nav aria-label="Akun"><h3>Akun</h3><a href="/login" onClick={handleAuthClick}>Masuk</a><a href="/register" onClick={handleAuthClick}>Daftar</a></nav>
        </div>
        <div className="landing-shell landing-footer-bottom"><span>© {new Date().getFullYear()} FitMindAI. Semua hak dilindungi.</span></div>
      </footer>

      <a className="landing-floating-chat" href="/chat" aria-label="Buka AI Chat" title="Buka AI Chat" onClick={handleAuthClick}>
        <img src="/robot-hello.svg" alt="" />
      </a>
    </div>
  )
}
