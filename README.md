# FitMindAI

FitMindAI adalah aplikasi kebugaran dengan landing page, akun pengguna, AI Chat, AI Plan, pencarian latihan dan nutrisi, kalkulator dashboard, serta ekspor rencana ke kalender atau WhatsApp.

## Struktur

- `frontend/` — React 19, Vite, dan React Router.
- `backend/` — FastAPI, SQLAlchemy, layanan AI, dan penyaji hasil build frontend.
- `dataset/` — CSV sumber untuk data latihan, nutrisi, dan program.
- `backend/chroma_db/` — indeks vektor untuk RAG. Jangan hapus tanpa rencana pembuatan ulang.
- `backend/scripts/` — `check_env.py` (cek konfigurasi), `prepare_database.py` (isi database baru), serta tool pengembangan `data_preparation.py` (membangun `master_nutrition.csv` dari CSV mentah), `ingest_vectordb.py` (membangun ulang `chroma_db`), dan `evaluator.py` (evaluasi RAG dengan RAGAS). Tool pengembangan butuh `python -m pip install -r requirements-dev.txt`; server cukup memakai `requirements.txt`.

## Menjalankan secara lokal

1. Salin `backend/.env.example` menjadi `backend/.env`. Isi kunci layanan yang digunakan dan buat `SESSION_SECRET` acak yang panjang. File `.env` tidak boleh dikomit.
2. Buat virtual environment Python di `backend/.venv` dan pasang dependensi dengan `python -m pip install -r requirements.txt`. Jalankan `npm install` di `frontend/`.
3. Jalankan `backend/start.bat` pada Windows (atau aktifkan `.venv\Scripts\Activate.ps1` lalu `python main.py`), lalu `npm run dev` di `frontend/`.
4. Untuk memperbarui halaman yang disajikan backend, jalankan `npm run build:backend` di `frontend/`. Hasil build langsung ditulis ke `backend/dist/`.

Saat startup, backend membuat tabel dan mengisi katalog (nutrisi, program, workout, makanan sehat) dari `dataset/` jika tabelnya masih kosong. Untuk mengisi database baru seperti Neon dari komputer lokal, pakai `scripts/prepare_database.py` (lihat bagian File environment).

## File environment

| File | Dipakai untuk | Dikomit |
| --- | --- | --- |
| `backend/.env` | Menjalankan backend di komputer lokal (SQLite) | Tidak |
| `backend/.env.production` | Variabel Railway (tempel di Variables → Raw Editor) dan import data ke Neon dari lokal | Tidak |
| `frontend/.env` | `VITE_API_URL` dan `VITE_SITE_URL` (domain untuk pratinjau tautan) saat build | Tidak |
| `backend/.env.example`, `frontend/.env.example` | Contoh isi | Ya |

Baris bertanda `[ISI]` wajib diisi manual. Backend membaca `backend/.env`, kecuali `ENV_FILE` diset ke file lain. Dari folder `backend/`:

```powershell
# Cek isi env (variabel kosong, koneksi database, API key Gemini). Nilai rahasia tidak ditampilkan.
.\.venv\Scripts\python.exe scripts\check_env.py
$env:ENV_FILE=".env.production"; .\.venv\Scripts\python.exe scripts\check_env.py

# Buat tabel & isi katalog di Neon (pakai DATABASE_URL dari .env.production)
$env:ENV_FILE=".env.production"; .\.venv\Scripts\python.exe scripts\prepare_database.py
Remove-Item Env:ENV_FILE
```

## Mode maintenance

- Jika database tidak bisa diakses (misalnya kuota Neon habis), backend tetap berjalan. Request yang memakai database dibalas `503` dengan `"maintenance": true`, dan `GET /api/status` melaporkan `"status": "maintenance"`.
- Frontend lalu menampilkan halaman maintenance di rute aplikasi, sementara landing page tetap tampil. Status diperiksa ulang otomatis setiap 60 detik, sehingga aplikasi kembali normal sendiri saat database pulih. Gangguan jaringan biasa tidak dianggap maintenance.
- Set `MAINTENANCE_MODE=true` untuk menampilkan mode maintenance secara manual.
- `GET /health` tidak menyentuh database. Pakai endpoint ini untuk healthcheck hosting agar server tidak di-restart terus saat database mati.

Vite memakai proxy `/api` ke `http://localhost:8000`. Jika frontend dan backend ada di origin berbeda, atur `VITE_API_URL` di frontend serta `ALLOWED_ORIGINS` di backend. Backend memakai `DATABASE_URL` jika diset; jika tidak, backend membuat SQLite lokal.

## Keamanan dan data

API akun memakai token sesi. Gunakan `SESSION_SECRET` yang sama pada semua instance backend supaya sesi tetap berlaku setelah restart. Untuk deployment, gunakan HTTPS dan simpan kunci layanan serta kredensial database pada environment server.

File SQLite lokal dapat berisi akun dan percakapan. `.dockerignore` mencegahnya masuk ke image; gunakan `DATABASE_URL` ke penyimpanan persisten di deployment. Endpoint AI, RapidAPI, dan WhatsApp memerlukan pembatasan laju request di lapisan deployment agar tidak disalahgunakan.

## Tim pengembang

- M Hanif Hawari — Backend Developer
- M Dian Fauzi — Frontend Developer
