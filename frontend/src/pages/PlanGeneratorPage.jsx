import { useState } from 'react'
import Sidebar from '../components/Sidebar'
import { WorkoutPlanCard, MealPlanCard } from '../components/PlanCard'
import api, { errorDetail } from '../api'

const GOALS = [
  { value: 'muscle_gain', label: 'Massa Otot', desc: 'Hypertrophy & strength' },
  { value: 'weight_loss', label: 'Turun Berat', desc: 'Fat loss & conditioning' },
  { value: 'endurance', label: 'Endurance', desc: 'Stamina & cardio' },
  { value: 'maintenance', label: 'Maintenance', desc: 'Jaga kebugaran' },
]

const LEVELS = [
  { value: 'beginner', label: 'Pemula', color: '#22c55e' },
  { value: 'intermediate', label: 'Menengah', color: '#f59e0b' },
  { value: 'advanced', label: 'Mahir', color: '#ef4444' },
]

const EQUIPMENT = [
  { value: 'Full Gym', label: 'Full Gym' },
  { value: 'Dumbbells Only', label: 'Dumbbells' },
  { value: 'Bodyweight', label: 'Bodyweight' },
]

export default function PlanGeneratorPage({ user }) {
  const [tab, setTab] = useState('workout')
  const [goal, setGoal] = useState('')
  const [level, setLevel] = useState('')
  const [days, setDays] = useState(3)
  const [equipment, setEquipment] = useState('')
  const [dietType, setDietType] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState(null)
  const [error, setError] = useState('')
  const [generationTime, setGenerationTime] = useState(null)

  async function generate() {
    setLoading(true)
    setError('')
    setPlan(null)
    setGenerationTime(null)
    const startTime = Date.now()
    try {
      const body = {
        plan_type: tab,
        goal: goal || undefined,
        level: level || undefined,
        days_per_week: days,
        equipment: equipment || undefined,
        diet_type: dietType || undefined,
        notes: notes || undefined,
      }
      const res = await api.post('/plans/generate', body)
      const endTime = Date.now()
      if (res.data.success && res.data.data) {
        setPlan(res.data.data)
        setGenerationTime(((endTime - startTime) / 1000).toFixed(2))
      } else {
        setError('Gagal generate plan. Coba lagi.')
      }
    } catch (err) {
      setError(errorDetail(err, 'Terjadi error. Pastikan backend berjalan.'))
    }
    setLoading(false)
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar username={user?.username} avatarData={user?.avatar_data} />
      <main className="dashboard-main plan-page">
        {/* Header */}
        <div className="plan-header" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em', marginBottom: 4 }}>
            AI Plan Generator
          </h1>
          <p style={{ fontSize: 14, color: '#a3a3a3' }}>
            Generate program latihan atau meal plan terstruktur dengan AI.
          </p>
        </div>

        {/* Plan Type Tabs */}
        <div className="plan-tabs" style={{ display: 'flex', gap: 4, marginBottom: 28, borderBottom: '1px solid #2a2a2a', paddingBottom: 1 }}>
          {[{ key: 'workout', label: 'Workout Plan' }, { key: 'meal', label: 'Meal Plan' }].map(t => (
            <button key={t.key} className={tab === t.key ? 'is-active' : ''} onClick={() => { setTab(t.key); setPlan(null); }}
              style={{
                padding: '9px 18px', background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 14, fontWeight: 500, fontFamily: '"Fira Sans", Arial, sans-serif',
                color: tab === t.key ? '#22c55e' : '#a3a3a3',
                borderBottom: tab === t.key ? '2px solid #22c55e' : '2px solid transparent',
                marginBottom: -1, transition: 'all 0.2s',
              }}>{t.label}</button>
          ))}
        </div>

        <div className={`plan-grid${plan ? '' : ' single'}`} style={{ gap: 24 }}>
          {/* ── Form ── */}
          <div className="card plan-form" style={{ padding: 24, alignSelf: 'start' }}>
            {/* Goal */}
            <label style={labelStyle}>Goal</label>
            <div className="plan-goals" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              {GOALS.map(g => (
                <button key={g.value} className={goal === g.value ? 'is-selected' : ''} aria-pressed={goal === g.value} onClick={() => setGoal(g.value)}
                  style={{
                    ...optionBtnStyle,
                    borderColor: goal === g.value ? '#22c55e' : '#2a2a2a',
                    background: goal === g.value ? 'rgba(34,197,94,0.08)' : '#111',
                  }}>
                  <div style={{ fontSize: 14 }}>{g.label}</div>
                  <div style={{ fontSize: 11, color: '#525252' }}>{g.desc}</div>
                </button>
              ))}
            </div>

            {/* Level */}
            <label style={labelStyle}>Level</label>
            <div className="plan-levels" style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {LEVELS.map(l => (
                <button key={l.value} onClick={() => setLevel(l.value)}
                  className={level === l.value ? 'badge-green' : 'badge-gray'}
                  style={{ cursor: 'pointer', padding: '6px 14px', fontSize: 13, flex: 1 }}>
                  {l.label}
                </button>
              ))}
            </div>

            {tab === 'workout' && (
              <>
                {/* Days per week */}
                <label style={labelStyle}>Hari / Minggu</label>
                <div className="plan-days" style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
                  {[2, 3, 4, 5, 6].map(d => (
                    <button key={d} className={days === d ? 'is-selected' : ''} aria-pressed={days === d} onClick={() => setDays(d)}
                      style={{
                        ...dayBtnStyle,
                        borderColor: days === d ? '#22c55e' : '#2a2a2a',
                        color: days === d ? '#22c55e' : '#a3a3a3',
                        background: days === d ? 'rgba(34,197,94,0.08)' : '#111',
                      }}>{d}</button>
                  ))}
                </div>

                {/* Equipment */}
                <label style={labelStyle}>Equipment</label>
                <div className="plan-equipment" style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                  {EQUIPMENT.map(e => (
                    <button key={e.value} onClick={() => setEquipment(e.value)}
                      className={equipment === e.value ? 'badge-green' : 'badge-gray'}
                      style={{ cursor: 'pointer', padding: '6px 14px', fontSize: 13 }}>
                      {e.label}
                    </button>
                  ))}
                </div>
              </>
            )}

            {tab === 'meal' && (
              <>
                <label style={labelStyle}>Tipe Diet</label>
                <select className="input-field" value={dietType} onChange={e => setDietType(e.target.value)}
                  style={{ marginBottom: 16, cursor: 'pointer' }}>
                  <option value="">Normal</option>
                  <option value="keto">Keto</option>
                  <option value="vegan">Vegan</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="paleo">Paleo</option>
                </select>
              </>
            )}

            {/* Notes */}
            <label style={labelStyle}>Catatan (opsional)</label>
            <textarea className="input-field" rows={2} placeholder="Contoh: fokus punggung dan bicep..."
              value={notes} onChange={e => setNotes(e.target.value)}
              style={{ marginBottom: 20, resize: 'none' }} />

            {/* Generate Button */}
            <button className="btn-primary" style={{ width: '100%', padding: '12px 20px', fontSize: 15 }}
              onClick={generate} disabled={loading}>
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <span style={{
                    width: 16, height: 16, border: '2px solid rgba(0,0,0,0.2)',
                    borderTop: '2px solid #0a0a0a', borderRadius: '50%',
                    animation: 'spin 0.7s linear infinite', display: 'inline-block',
                  }} />
                  Generating...
                </span>
              ) : (
                `Generate ${tab === 'meal' ? 'Meal' : 'Workout'} Plan`
              )}
            </button>

            {error && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, fontSize: 13, color: '#ef4444' }}>
                {error}
              </div>
            )}
          </div>

          {/* ── Result ── */}
          {plan && (
            <div>
              {tab === 'workout'
                ? <WorkoutPlanCard plan={plan} generationTime={generationTime} />
                : <MealPlanCard plan={plan} generationTime={generationTime} />}
            </div>
          )}

          {/* Empty state */}
          {!plan && !loading && (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', padding: 60, color: '#525252',
            }}>
              <div style={{ fontSize: 15, textAlign: 'center', maxWidth: 300 }}>
                Isi formulir, lalu tekan <strong style={{ color: '#22c55e' }}>Generate</strong> untuk membuat {tab === 'workout' ? 'program latihan' : 'meal plan'} terstruktur.
              </div>
            </div>
          )}
        </div>

        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </main>
    </div>
  )
}

const labelStyle = {
  fontSize: 12, fontWeight: 600, color: '#a3a3a3', textTransform: 'uppercase',
  letterSpacing: '0.06em', marginBottom: 8, display: 'block',
}

const optionBtnStyle = {
  padding: '10px 12px', borderRadius: 8, border: '1px solid #2a2a2a',
  cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
  fontFamily: '"Fira Sans", Arial, sans-serif', color: '#f5f5f5',
}

const dayBtnStyle = {
  width: 40, height: 40, borderRadius: 8, border: '1px solid #2a2a2a',
  cursor: 'pointer', fontSize: 15, fontWeight: 600,
  fontFamily: '"Fira Sans", Arial, sans-serif', transition: 'all 0.15s',
}
