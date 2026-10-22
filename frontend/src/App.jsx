import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import NutritionPage from './pages/NutritionPage'
import WorkoutPage from './pages/WorkoutPage'
import ProfilePage from './pages/ProfilePage'
import PlanGeneratorPage from './pages/PlanGeneratorPage'
import MaintenancePage from './pages/MaintenancePage'
import api, { fetchMaintenance, MAINTENANCE_EVENT } from './api'

// Interval cek ulang status server selama mode maintenance
const STATUS_RECHECK_MS = 60000

function clearStoredSession() {
  localStorage.removeItem('fitmind_token')
  localStorage.removeItem('fitmind_user')
  localStorage.removeItem('fitmind_profile')
}

// Komponen Wrapper untuk membatasi akses halaman hanya untuk user yang sudah login/terdaftar
function ProtectedRoute({ children, user }) {
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loaded, setLoaded] = useState(false) // Flag untuk memastikan pengecekan localStorage selesai sebelum merender halaman
  const [maintenance, setMaintenance] = useState(false) // true saat server/database tidak bisa diakses

  // Mengambil data pengguna berdasarkan token yang tersimpan di localStorage
  const loadUser = useCallback(async () => {
    const stored = localStorage.getItem('fitmind_user')
    const token = localStorage.getItem('fitmind_token')
    if (!stored || !token) {
      localStorage.removeItem('fitmind_user')
      return
    }
    try {
      const { data } = await api.get('/users/me')
      setUser(data)
    } catch (error) {
      // Hanya sesi tidak valid yang menghapus login; saat maintenance (503) token tetap disimpan
      if (error.response?.status === 401) clearStoredSession()
    }
  }, [])

  // Cek ulang status server; jika sudah pulih, muat ulang user sebelum keluar dari mode maintenance
  const recheckStatus = useCallback(async () => {
    const down = await fetchMaintenance()
    if (!down) await loadUser()
    setMaintenance(down)
    return down
  }, [loadUser])

  // Saat aplikasi pertama kali dimuat: cek status server dan sesi user secara paralel.
  // Status tidak menahan render; mode maintenance aktif begitu hasilnya diterima.
  useEffect(() => {
    fetchMaintenance().then(setMaintenance)
    loadUser().finally(() => setLoaded(true))
  }, [loadUser])

  // Request mana pun yang dibalas 503 maintenance mengaktifkan mode maintenance
  useEffect(() => {
    const enterMaintenance = () => setMaintenance(true)
    window.addEventListener(MAINTENANCE_EVENT, enterMaintenance)
    return () => window.removeEventListener(MAINTENANCE_EVENT, enterMaintenance)
  }, [])

  // Selama maintenance, cek ulang otomatis agar aplikasi kembali normal tanpa reload
  useEffect(() => {
    if (!maintenance) return
    const timer = setInterval(recheckStatus, STATUS_RECHECK_MS)
    return () => clearInterval(timer)
  }, [maintenance, recheckStatus])

  // Callback untuk sinkronisasi state user ketika ada perubahan profil (misal: berat badan, tinggi badan)
  async function handleProfileSaved() {
    try {
      const { data } = await api.get('/users/me')
      setUser(data)
    } catch {
      // The profile page keeps its own saved state if the refresh fails.
    }
  }

  // Menghindari flash halaman login jika user sebenarnya sudah terautentikasi
  // (kecuali server sudah diketahui maintenance, maka langsung tampilkan)
  if (!loaded && !maintenance) return null

  // Saat database dinyatakan tidak tersedia oleh server, halaman aplikasi diganti halaman maintenance;
  // landing page tetap tampil
  const guard = (element) => maintenance ? <MaintenancePage onRetry={recheckStatus} /> : element

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Jika user sudah login, redirect otomatis dari login/register ke dashboard */}
        <Route path="/login" element={guard(user ? <Navigate to="/dashboard" replace /> : <LoginPage />)} />
        <Route path="/register" element={guard(user ? <Navigate to="/dashboard" replace /> : <RegisterPage />)} />
        <Route path="/dashboard" element={guard(
          <ProtectedRoute user={user}>
            <DashboardPage user={user} />
          </ProtectedRoute>
        )} />
        <Route path="/chat" element={guard(
          <ProtectedRoute user={user}>
            <ChatPage user={user} />
          </ProtectedRoute>
        )} />
        <Route path="/nutrition" element={guard(
          <ProtectedRoute user={user}>
            <NutritionPage user={user} />
          </ProtectedRoute>
        )} />
        <Route path="/workout" element={guard(
          <ProtectedRoute user={user}>
            <WorkoutPage user={user} />
          </ProtectedRoute>
        )} />
        <Route path="/plan" element={guard(
          <ProtectedRoute user={user}>
            <PlanGeneratorPage user={user} />
          </ProtectedRoute>
        )} />
        <Route path="/profile" element={guard(
          <ProtectedRoute user={user}>
            <ProfilePage user={user} onProfileSaved={handleProfileSaved} />
          </ProtectedRoute>
        )} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
