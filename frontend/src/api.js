import axios from 'axios'

// Mengambil URL API dari environment variable Vite, dengan fallback ke '/api' untuk mode reverse proxy/development
const API_URL = import.meta.env.VITE_API_URL || '/api'

// Event global yang memberi tahu App bahwa server sedang maintenance
export const MAINTENANCE_EVENT = 'fitmind:maintenance'

// Membuat instance Axios dengan konfigurasi dasar untuk komunikasi ke backend FastAPI
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000, // Batas waktu request 30 detik untuk mengantisipasi proses LLM yang membutuhkan waktu lebih lama
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fitmind_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(undefined, (error) => {
  // Backend membalas 503 + maintenance saat database tidak bisa diakses → App menampilkan mode maintenance
  if (error.response?.status === 503 && error.response.data?.maintenance) {
    window.dispatchEvent(new Event(MAINTENANCE_EVENT))
  }
  if (error.response?.status === 401 && !error.config?.url?.endsWith('/users/login')) {
    localStorage.removeItem('fitmind_token')
    localStorage.removeItem('fitmind_user')
    localStorage.removeItem('fitmind_profile')
    window.location.assign('/login')
  }
  return Promise.reject(error)
})

// true hanya jika server menyatakan sedang maintenance (database tidak bisa diakses / MAINTENANCE_MODE).
// Gangguan jaringan biasa tidak dianggap maintenance agar user tetap bisa membuka halaman login.
export async function fetchMaintenance() {
  try {
    const { data } = await api.get('/status', { timeout: 8000 })
    return data?.status === 'maintenance'
  } catch (error) {
    return error.response?.status === 503 && Boolean(error.response.data?.maintenance)
  }
}

export default api

