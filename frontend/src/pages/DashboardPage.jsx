import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import api from '../api'

const zoneColors = {
  'Zone 1 (Recovery)': '#a3a3a3',
  'Zone 2 (Fat Burn)': '#22c55e',
  'Zone 3 (Cardio)': '#f59e0b',
  'Zone 4 (Anaerobic)': '#f97316',
  'Zone 5 (Max)': '#ef4444',
}

const bmiColorMap = { Normal: '#22c55e', Underweight: '#f59e0b', Overweight: '#f97316', Obese: '#ef4444' }

export default function DashboardPage({ user }) {
  const [profile, setProfile] = useState(null)
  const [activeCalculator, setActiveCalculator] = useState('bmi')
  const weeklyTarget = Number(profile?.workout_frequency)
  const hasWeeklyTarget = Number.isInteger(weeklyTarget) && weeklyTarget >= 1 && weeklyTarget <= 7
  const workoutNames = { Strength: 'Latihan kekuatan', Cardio: 'Kardio', HIIT: 'HIIT', Yoga: 'Yoga', Mixed: 'Campuran' }
  const equipmentNames = { None: 'Tanpa alat', Dumbbells: 'Dumbbell', Barbell: 'Barbell', Machine: 'Mesin gym', 'Full Gym': 'Gym lengkap' }

  useEffect(() => {
    if (!user?.username) return
    let active = true
    api.get(`/users/${user.username}/profile`)
      .then(({ data }) => { if (active) setProfile(data.data) })
      .catch(() => {})
    return () => { active = false }
  }, [user?.username])

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar username={user?.username} avatarData={user?.avatar_data} />
      <main className="dashboard-main dashboard-home">
        <section className="dash-hero">
          <div className="dash-hero-copy">
            <span className="dash-eyebrow">RUANG LATIHANMU</span>
            <h1>Siap bergerak hari ini, <span>{user?.username || 'Atlet'}?</span></h1>
            <p>Temukan gerakan yang cocok dan susun rencana latihan sesuai tujuanmu.</p>
            <Link className="dash-hero-cta" to="/plan"><span>Buat rencana latihan</span><span aria-hidden="true">→</span></Link>
          </div>
          <div className="dash-hero-image">
            <img className="dash-hero-logo" src="/logo-transparent.png" alt="Logo FitMindAI" />
          </div>
        </section>
        <div className="dash-metrics" aria-label="Ringkasan profil">
          <div><strong>{profile?.bmi ?? '—'}</strong><span>BMI tersimpan</span></div>
          <div><strong>{profile?.workout_frequency ? `${profile.workout_frequency} hari` : '—'}</strong><span>Latihan per minggu</span></div>
          <div><strong>{profile?.goal || '—'}</strong><span>Tujuan utama</span></div>
        </div>
        <section className="dash-section">
          <div className="dash-section-heading">
            <h2>Kalkulator Cepat</h2>
            <div className="dash-calc-tabs" role="tablist" aria-label="Pilih kalkulator">
              {[
                { key: 'bmi', label: 'BMI' },
                { key: 'calories', label: 'Kalori Bakar' },
                { key: 'bpm', label: 'Detak Jantung' },
              ].map(item => <button key={item.key} role="tab" aria-selected={activeCalculator === item.key}
                className={activeCalculator === item.key ? 'is-active' : ''}
                onClick={() => setActiveCalculator(item.key)}>{item.label}</button>)}
            </div>
          </div>
          <div className="dash-calculator-grid">
            <div className={`dash-calc-panel ${activeCalculator === 'bmi' ? 'is-active' : ''}`}><BMICard /></div>
            <div className={`dash-calc-panel ${activeCalculator === 'calories' ? 'is-active' : ''}`}><CaloriesCard /></div>
            <div className={`dash-calc-panel ${activeCalculator === 'bpm' ? 'is-active' : ''}`}><BPMCard /></div>
          </div>
        </section>
        <section className="dash-section">
          <div className="dash-section-heading"><h2>Rencana Latihanmu</h2></div>
          <div className="dash-training-grid">
            <div className="dash-training-card">
              <div className="dash-training-card-heading"><h3>Target mingguan</h3><strong>{hasWeeklyTarget ? `${weeklyTarget} hari` : 'Belum diatur'}</strong></div>
              {hasWeeklyTarget ? (
                <>
                  <div className="dash-week-chart" role="img" aria-label={`Target latihan ${weeklyTarget} dari 7 hari per minggu`}>
                    {Array.from({ length: 7 }, (_, index) => <span key={index} className={index < weeklyTarget ? 'is-target' : ''} />)}
                  </div>
                  <p>Batang hijau menunjukkan target latihan, bukan latihan yang sudah selesai.</p>
                </>
              ) : <p>Isi frekuensi latihan di profil untuk melihat target mingguanmu.</p>}
              <Link to="/profile">Atur target <span aria-hidden="true">→</span></Link>
            </div>
            <div className="dash-training-card">
              <div className="dash-training-card-heading"><h3>Preferensi latihan</h3></div>
              <dl className="dash-training-details">
                <div><dt>Jenis latihan</dt><dd>{workoutNames[profile?.workout_type] || profile?.workout_type || 'Belum diatur'}</dd></div>
                <div><dt>Peralatan</dt><dd>{equipmentNames[profile?.equipment] || profile?.equipment || 'Belum diatur'}</dd></div>
                <div><dt>Durasi per sesi</dt><dd>{profile?.session_duration ? `${profile.session_duration} menit` : 'Belum diatur'}</dd></div>
              </dl>
              <Link to="/workout">Cari gerakan <span aria-hidden="true">→</span></Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

/* ─── BMI Card ─────────────────────────────────────────── */
function BMICard() {
  const [weight, setWeight] = useState('')
  const [height, setHeight] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function calculate() {
    if (!weight || !height) return
    setLoading(true)
    try {
      const res = await api.get('/dashboard/calculate-bmi', {
        params: { weight_kg: parseFloat(weight), height_m: parseFloat(height) / 100 },
      })
      setResult(res.data.data)
    } catch {}
    setLoading(false)
  }

  const color = result ? (bmiColorMap[result.category] || '#a3a3a3') : '#22c55e'

  return (
    <div className="card" style={{ padding: 24 }}>
      <SectionHeader label="Kalkulator BMI" />
      {result && (
        <div style={{ textAlign: 'center', marginBottom: 18 }}>
          <div className="metric-value" style={{ color }}>{result.bmi}</div>
          <div className="metric-label">{result.category}</div>
          <div style={{ fontSize: 12, color: '#525252', marginTop: 6 }}>
            Berat ideal: {result.ideal_weight_range.min} – {result.ideal_weight_range.max} kg
          </div>
          {result.dataset_avg_bmi && (
            <div style={{ fontSize: 12, color: '#525252', marginTop: 2 }}>
              Rata-rata dataset: {result.dataset_avg_bmi}
            </div>
          )}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <input className="input-field" placeholder="Berat (kg)" type="number" value={weight} onChange={e => setWeight(e.target.value)} />
        <input className="input-field" placeholder="Tinggi (cm)" type="number" value={height} onChange={e => setHeight(e.target.value)} />
      </div>
      <button className="btn-primary" style={{ width: '100%' }} onClick={calculate} disabled={loading}>
        {loading ? 'Menghitung...' : 'Hitung BMI'}
      </button>
    </div>
  )
}

/* ─── Calories Card ─────────────────────────────────────── */
function CaloriesCard() {
  const [age, setAge] = useState('')
  const [weight, setWeight] = useState('')
  const [bpm, setBpm] = useState('')
  const [duration, setDuration] = useState('')
  const [type, setType] = useState('Cardio')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function calculate() {
    if (!age || !weight || !bpm || !duration) return
    setLoading(true)
    try {
      const res = await api.get('/dashboard/estimate-calories', {
        params: {
          age: parseInt(age),
          weight_kg: parseFloat(weight),
          avg_bpm: parseInt(bpm),
          duration_hours: parseFloat(duration) / 60,
          workout_type: type,
        },
      })
      setResult(res.data.data)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ padding: 24 }}>
      <SectionHeader label="Estimasi Kalori Terbakar" />
      {result && (
        <div style={{ textAlign: 'center', marginBottom: 18 }}>
          <div className="metric-value" style={{ color: '#ef4444' }}>{result.estimated_calories}</div>
          <div className="metric-label">kkal terbakar</div>
          {result.dataset_avg_calories_burned && (
            <div style={{ fontSize: 12, color: '#525252', marginTop: 6 }}>
              Rata-rata gym member: {result.dataset_avg_calories_burned} kkal
            </div>
          )}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
        <input className="input-field" placeholder="Usia" type="number" value={age} onChange={e => setAge(e.target.value)} />
        <input className="input-field" placeholder="Berat (kg)" type="number" value={weight} onChange={e => setWeight(e.target.value)} />
        <input className="input-field" placeholder="BPM rata-rata" type="number" value={bpm} onChange={e => setBpm(e.target.value)} />
        <input className="input-field" placeholder="Durasi (menit)" type="number" value={duration} onChange={e => setDuration(e.target.value)} />
      </div>
      <select className="input-field" value={type} onChange={e => setType(e.target.value)} style={{ marginBottom: 10, cursor: 'pointer' }}>
        {['HIIT', 'Cardio', 'Strength', 'Yoga'].map(t => <option key={t} value={t}>{t}</option>)}
      </select>
      <button className="btn-primary" style={{ width: '100%' }} onClick={calculate} disabled={loading}>
        {loading ? 'Menghitung...' : 'Estimasi Kalori'}
      </button>
    </div>
  )
}

/* ─── BPM Zone Card ─────────────────────────────────────── */
function BPMCard() {
  const [age, setAge] = useState('')
  const [bpm, setBpm] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function analyze() {
    if (!age || !bpm) return
    setLoading(true)
    try {
      const res = await api.get('/dashboard/bpm-analysis', {
        params: { age: parseInt(age), avg_bpm: parseInt(bpm) },
      })
      setResult(res.data.data)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="card" style={{ padding: 24 }}>
      <SectionHeader label="Zona Detak Jantung" />
      {result && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 2 }}>
            <div className="metric-value" style={{ color: zoneColors[result.current_zone] || '#22c55e' }}>
              {result.avg_bpm}
            </div>
            <div style={{ fontSize: 13, color: '#a3a3a3' }}>BPM</div>
          </div>
          <div style={{ fontSize: 13, color: zoneColors[result.current_zone] || '#22c55e', fontWeight: 600, marginBottom: 10 }}>
            {result.current_zone}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {result.zones && Object.entries(result.zones).map(([zone, range]) => (
              <div key={zone} style={{
                display: 'flex', justifyContent: 'space-between', fontSize: 12,
                padding: '5px 8px', borderRadius: 5,
                background: zone === result.current_zone ? 'rgba(34,197,94,0.08)' : 'transparent',
                border: `1px solid ${zone === result.current_zone ? 'rgba(34,197,94,0.2)' : 'transparent'}`,
              }}>
                <span style={{ color: zone === result.current_zone ? '#22c55e' : '#a3a3a3' }}>{zone}</span>
                <span style={{ color: '#525252' }}>{range.min_bpm}–{range.max_bpm}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <input className="input-field" placeholder="Usia" type="number" value={age} onChange={e => setAge(e.target.value)} />
        <input className="input-field" placeholder="BPM rata-rata" type="number" value={bpm} onChange={e => setBpm(e.target.value)} />
      </div>
      <button className="btn-primary" style={{ width: '100%' }} onClick={analyze} disabled={loading}>
        {loading ? 'Menganalisis...' : 'Analisis BPM'}
      </button>
    </div>
  )
}

function SectionHeader({ label }) {
  return (
    <>
      <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#a3a3a3', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ height: 1, background: '#2a2a2a', marginBottom: 18 }} />
    </>
  )
}
