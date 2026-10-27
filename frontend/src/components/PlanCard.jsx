import { useState } from 'react'
import api, { errorDetail } from '../api'
import { useToast, ToastContainer } from './Toast'

/**
 * WorkoutPlanCard — Render workout plan JSON sebagai kartu visual interaktif.
 */
export function WorkoutPlanCard({ plan, generationTime }) {
  const [expandedDay, setExpandedDay] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const { toasts, showToast, dismiss } = useToast()

  if (!plan) return null
  
  // Fallback if the LLM returned JSON but didn't follow the exact 'schedule' schema
  if (!plan.schedule) {
    return (
      <div className="card animate-fadeinup" style={{ padding: 24, background: '#1a1a1a', border: '1px solid #ef4444' }}>
        <h3 style={{ color: '#ef4444', marginBottom: 12 }}>⚠ AI tidak mengembalikan format yang sesuai</h3>
        <pre style={{ fontSize: 12, overflowX: 'auto', color: '#a3a3a3' }}>
          {JSON.stringify(plan, null, 2)}
        </pre>
      </div>
    )
  }

  const syncToCalendar = async () => {
    setSyncing(true)
    try {
      // Send the entire plan object
      const res = await api.post('/calendar/export', plan, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `fitmind_${plan.plan_type || 'workout'}.ics`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch {
      alert('Gagal export ke calendar.')
    }
    setSyncing(false)
  }

  const sendToWhatsApp = async () => {
    // Ambil user dari localStorage
    const storedUser = JSON.parse(localStorage.getItem('fitmind_user') || '{}')
    const phone = storedUser.phone
    
    if (!phone) {
      showToast('Nomor WhatsApp belum terdaftar! Silakan login/register ulang.', 'warning', { title: 'Nomor Tidak Ditemukan' })
      return
    }

    setSyncing(true)
    showToast('Sedang mengirim ke WhatsApp...', 'info', { title: 'Mengirim', duration: 3000 })
    try {
      const res = await api.post('/whatsapp/send-plan', plan)
      if (res.data.success) {
        showToast('Program latihan berhasil dikirim ke WhatsApp kamu!', 'success', { title: 'Terkirim!' })
      }
    } catch (err) {
      const detail = errorDetail(err, '')
      const isToken = detail.toLowerCase().includes('token') || detail.toLowerCase().includes('fonnte')
      showToast(
        isToken
          ? 'Token Fonnte habis atau tidak valid. Hubungi admin untuk memperbarui token.'
          : (detail || 'Gagal mengirim WhatsApp. Coba beberapa saat lagi.'),
        'error',
        { title: isToken ? 'Token Fonnte Habis' : 'Gagal Mengirim' }
      )
    }
    setSyncing(false)
  }

  return (
    <div className="card animate-fadeinup" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px', borderBottom: '1px solid #2a2a2a',
        background: 'linear-gradient(135deg, rgba(34,197,94,0.08) 0%, transparent 60%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f5f5f5', letterSpacing: '-0.02em' }}>
            {plan.title || 'Workout Plan'}
          </h3>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {plan.level && <span className="badge-green">{plan.level}</span>}
          {plan.goal && <span className="badge-gray">{plan.goal}</span>}
          {plan.days_per_week && (
            <span className="badge-gray">{plan.days_per_week} hari/minggu</span>
          )}
          {generationTime && (
            <span className="badge-gray" style={{ color: '#a855f7', borderColor: 'rgba(168,85,247,0.3)', background: 'rgba(168,85,247,0.1)' }}>
              AI: {generationTime}s
            </span>
          )}
        </div>
      </div>

      {/* Schedule */}
      <div style={{ padding: '16px 24px' }}>
        {plan.schedule.map((session, i) => (
          <div key={i} style={{
            marginBottom: i < plan.schedule.length - 1 ? 12 : 0,
            border: '1px solid #2a2a2a', borderRadius: 10,
            overflow: 'hidden', transition: 'border-color 0.2s',
          }}>
            {/* Day header — clickable */}
            <button
              onClick={() => setExpandedDay(expandedDay === i ? null : i)}
              style={{
                width: '100%', display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', padding: '12px 16px', background: '#111111',
                border: 'none', cursor: 'pointer', color: '#f5f5f5',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: 'rgba(34,197,94,0.12)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700, color: '#22c55e',
                }}>
                  {session.day?.slice(0, 2) || `D${i + 1}`}
                </div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{session.day}</div>
                  <div style={{ fontSize: 12, color: '#a3a3a3' }}>{session.focus}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: '#525252' }}>
                  {session.exercises?.length || 0} gerakan
                </span>
                <span style={{
                  fontSize: 16, color: '#525252', transition: 'transform 0.2s',
                  transform: expandedDay === i ? 'rotate(180deg)' : 'rotate(0)',
                }}>▾</span>
              </div>
            </button>

            {/* Exercises — expanded */}
            {expandedDay === i && session.exercises && (
              <div style={{ padding: '12px 16px', background: '#0d0d0d' }}>
                {session.exercises.map((ex, j) => (
                  <div key={j} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 0',
                    borderBottom: j < session.exercises.length - 1 ? '1px solid #1a1a1a' : 'none',
                  }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500, color: '#f5f5f5' }}>
                        {ex.name}
                      </div>
                      <div style={{ fontSize: 12, color: '#525252', marginTop: 2 }}>
                        {ex.muscle_group && <span>{ex.muscle_group}</span>}
                        {ex.notes && <span> · {ex.notes}</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 12, flexShrink: 0 }}>
                      <Stat label="Sets" value={ex.sets} />
                      <Stat label="Reps" value={ex.reps} />
                      {ex.rest_seconds && <Stat label="Rest" value={`${ex.rest_seconds}s`} />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Tips */}
      {plan.tips && plan.tips.length > 0 && (
        <div style={{ padding: '0 24px 20px' }}>
          <div style={{
            background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)',
            borderRadius: 8, padding: '12px 16px',
          }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#22c55e', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Tips
            </div>
            {plan.tips.map((tip, i) => (
              <div key={i} style={{ fontSize: 13, color: '#a3a3a3', marginBottom: 4 }}>
                • {tip}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{
        padding: '16px 24px', borderTop: '1px solid #2a2a2a',
        display: 'flex', gap: 8, flexWrap: 'wrap',
      }}>
        <button className="btn-primary" style={{ fontSize: 13, padding: '8px 14px' }} onClick={syncToCalendar} disabled={syncing}>
          Sync ke Calendar
        </button>
        <button className="btn-primary" style={{ fontSize: 13, padding: '8px 14px', backgroundColor: '#25D366', borderColor: '#25D366', color: '#fff' }} onClick={sendToWhatsApp} disabled={syncing}>
          {syncing ? 'Mengirim...' : 'Kirim ke WhatsApp'}
        </button>
      </div>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}

/**
 * MealPlanCard — Render meal plan JSON sebagai kartu visual.
 */
export function MealPlanCard({ plan, generationTime }) {
  const [syncing, setSyncing] = useState(false)
  const { toasts, showToast, dismiss } = useToast()

  if (!plan) return null

  // Fallback if the LLM returned JSON but didn't follow the exact 'meals' schema
  if (!plan.meals) {
    return (
      <div className="card animate-fadeinup" style={{ padding: 24, background: '#1a1a1a', border: '1px solid #ef4444' }}>
        <h3 style={{ color: '#ef4444', marginBottom: 12 }}>⚠ AI tidak mengembalikan format yang sesuai</h3>
        <pre style={{ fontSize: 12, overflowX: 'auto', color: '#a3a3a3' }}>
          {JSON.stringify(plan, null, 2)}
        </pre>
      </div>
    )
  }

  const syncToCalendar = async () => {
    setSyncing(true)
    try {
      const res = await api.post('/calendar/export', plan, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `fitmind_${plan.plan_type || 'meal'}.ics`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch {
      showToast('Gagal export ke calendar.', 'error', { title: 'Export Gagal' })
    }
    setSyncing(false)
  }

  const sendToWhatsApp = async () => {
    // Ambil user dari localStorage
    const storedUser = JSON.parse(localStorage.getItem('fitmind_user') || '{}')
    const phone = storedUser.phone
    
    if (!phone) {
      showToast('Nomor WhatsApp belum terdaftar! Silakan login/register ulang.', 'warning', { title: 'Nomor Tidak Ditemukan' })
      return
    }

    setSyncing(true)
    showToast('Sedang mengirim meal plan ke WhatsApp...', 'info', { title: 'Mengirim', duration: 3000 })
    try {
      const res = await api.post('/whatsapp/send-plan', plan)
      if (res.data.success) {
        showToast('Meal plan berhasil dikirim ke WhatsApp kamu!', 'success', { title: 'Terkirim!' })
      }
    } catch (err) {
      const detail = errorDetail(err, '')
      const isToken = detail.toLowerCase().includes('token') || detail.toLowerCase().includes('fonnte')
      showToast(
        isToken
          ? 'Token Fonnte habis atau tidak valid. Hubungi admin untuk memperbarui token.'
          : (detail || 'Gagal mengirim WhatsApp. Coba beberapa saat lagi.'),
        'error',
        { title: isToken ? 'Token Fonnte Habis' : 'Gagal Mengirim' }
      )
    }
    setSyncing(false)
  }

  const macros = [
    { label: 'Kalori', value: plan.daily_calories, unit: 'kkal', color: '#ef4444' },
    { label: 'Protein', value: plan.daily_protein_g, unit: 'g', color: '#22c55e' },
    { label: 'Karbo', value: plan.daily_carbs_g, unit: 'g', color: '#f59e0b' },
    { label: 'Lemak', value: plan.daily_fat_g, unit: 'g', color: '#3b82f6' },
  ]

  return (
    <div className="card animate-fadeinup" style={{ overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px', borderBottom: '1px solid #2a2a2a',
        background: 'linear-gradient(135deg, rgba(245,158,11,0.08) 0%, transparent 60%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f5f5f5' }}>
            {plan.title || 'Meal Plan'}
          </h3>
          {generationTime && (
            <span className="badge-gray" style={{ marginLeft: 'auto', color: '#a855f7', borderColor: 'rgba(168,85,247,0.3)', background: 'rgba(168,85,247,0.1)', fontSize: 13, padding: '4px 10px' }}>
              AI: {generationTime}s
            </span>
          )}
        </div>
        {/* Macro summary */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {macros.map((m, i) => m.value != null && (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: m.color }}>{m.value}</div>
              <div style={{ fontSize: 11, color: '#525252', textTransform: 'uppercase' }}>
                {m.label} {m.unit && `(${m.unit})`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Meals */}
      <div style={{ padding: '16px 24px' }}>
        {plan.meals.map((meal, i) => (
          <div key={i} style={{
            marginBottom: i < plan.meals.length - 1 ? 16 : 0,
            padding: '14px 16px', background: '#111111',
            borderRadius: 10, border: '1px solid #2a2a2a',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f5f5f5' }}>
                {meal.meal_name}
              </div>
              {meal.time && (
                <span style={{ fontSize: 12, color: '#525252' }}>⏰ {meal.time}</span>
              )}
            </div>
            {meal.foods && meal.foods.map((food, j) => (
              <div key={j} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 0',
                borderBottom: j < meal.foods.length - 1 ? '1px solid #1a1a1a' : 'none',
              }}>
                <div>
                  <span style={{ fontSize: 13, color: '#f5f5f5' }}>{food.name}</span>
                  <span style={{ fontSize: 12, color: '#525252', marginLeft: 8 }}>{food.portion}</span>
                </div>
                <div style={{ display: 'flex', gap: 10, fontSize: 12, color: '#a3a3a3' }}>
                  <span style={{ color: '#ef4444' }}>{food.calories}kkal</span>
                  {food.protein_g != null && <span>P:{food.protein_g}g</span>}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Tips */}
      {plan.tips && plan.tips.length > 0 && (
        <div style={{ padding: '0 24px 20px' }}>
          <div style={{
            background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)',
            borderRadius: 8, padding: '12px 16px',
          }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#f59e0b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Tips Nutrisi
            </div>
            {plan.tips.map((tip, i) => (
              <div key={i} style={{ fontSize: 13, color: '#a3a3a3', marginBottom: 4 }}>
                • {tip}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{
        padding: '16px 24px', borderTop: '1px solid #2a2a2a',
        display: 'flex', gap: 8, flexWrap: 'wrap',
      }}>
        <button className="btn-primary" style={{ fontSize: 13, padding: '8px 14px' }} onClick={syncToCalendar} disabled={syncing}>
          Sync ke Calendar
        </button>
        <button className="btn-primary" style={{ fontSize: 13, padding: '8px 14px', backgroundColor: '#25D366', borderColor: '#25D366', color: '#fff' }} onClick={sendToWhatsApp} disabled={syncing}>
          {syncing ? 'Mengirim...' : 'Kirim ke WhatsApp'}
        </button>
      </div>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div style={{ textAlign: 'center', minWidth: 36 }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: '#22c55e' }}>{value}</div>
      <div style={{ fontSize: 10, color: '#525252', textTransform: 'uppercase' }}>{label}</div>
    </div>
  )
}
