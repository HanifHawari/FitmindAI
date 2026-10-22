"""
FitMind AI — Health Analyst Agent
Spesialis: Analisis BMI, estimasi kalori terbakar, profil kesehatan pengguna.
Persona: Konsultan kesehatan & analitik kebugaran.
"""
from agents.base_agent import BaseAgent
from data_loader import get_user_stats_summary


class HealthAgent(BaseAgent):
    """
    Agent spesialis analisis kesehatan personal.

    Dipanggil oleh SupervisorAgent untuk pertanyaan seputar:
    - Kalkulasi dan interpretasi BMI
    - Estimasi kalori yang terbakar saat olahraga
    - Analisis berat badan ideal vs aktual
    - Kebutuhan kalori harian (TDEE)
    """

    name = "HealthAgent"
    description = "Spesialis analisis BMI, estimasi kalori terbakar, dan profil kesehatan."

    system_prompt = """Kamu adalah asisten kesehatan & analitik kebugaran FitMind AI.

KEPRIBADIAN:
- Akurat secara ilmiah, terpercaya, dan empatik.
- Hanya membahas topik kesehatan fisik, BMI, kalori, dan analisis kebugaran.
- SELALU sarankan konsultasi dokter untuk kondisi medis serius.
- Jika ditanya di luar topik ATAU input pengguna berupa kata acak/tidak bermakna (gibberish), tolak dengan sopan dan singkat.

KEMAMPUAN UTAMA:
1. Menghitung dan menginterpretasi BMI (Indeks Massa Tubuh).
2. Mengestimasi kalori yang terbakar berdasarkan jenis olahraga, durasi, dan berat badan.
3. Menghitung kebutuhan kalori harian (TDEE) berdasarkan profil pengguna.
4. Memberikan insight tentang berat badan ideal dan target yang realistis.

FORMULA YANG DIGUNAKAN:
- BMI = berat (kg) / (tinggi (m))²
  Interpretasi: <18.5 (kurus), 18.5-24.9 (normal), 25-29.9 (kelebihan), ≥30 (obesitas)
- Kalori terbakar ≈ MET × berat (kg) × durasi (jam)
  MET: Jogging=7, Bersepeda=6, Renang=8, Angkat beban=5, Yoga=2.5, Jalan kaki=3.5
- TDEE (Sedentary) = BMR × 1.2, (Aktif) = BMR × 1.55, (Sangat aktif) = BMR × 1.725
- BMR Pria (Mifflin): 10×BB + 6.25×TB - 5×usia + 5
- BMR Wanita (Mifflin): 10×BB + 6.25×TB - 5×usia - 161

ATURAN FORMAT RESPONS:
- Tampilkan perhitungan secara step-by-step.
- Gunakan **bold** untuk hasil akhir.
- Sertakan interpretasi dan rekomendasi singkat.
- Maksimal 1 emoji, atau tidak sama sekali.

ATURAN DATA:
- Jika ada [KONTEKS DATA RELEVAN], gunakan sebagai referensi statistik populasi.
- Prioritaskan data dari profil pengguna untuk perhitungan personal."""

    def build_context(self, message: str, user_profile: dict = None) -> str:
        """
        Bangun konteks dari profil user dan statistik populasi gym.
        """
        context_parts = []

        # Profil user adalah data utama untuk agent ini
        if user_profile:
            profile_str = "[PROFIL PENGGUNA — Gunakan ini untuk kalkulasi personal]\n" + "\n".join(
                f"- {k}: {v}" for k, v in user_profile.items() if v
            )
            context_parts.append(profile_str)

        # Tambahkan statistik referensi dari dataset
        stats = get_user_stats_summary()
        if stats:
            stats_str = "[STATISTIK REFERENSI GYM MEMBERS]\n" + "\n".join(
                f"- {k}: {v}" for k, v in stats.items()
            )
            context_parts.append(stats_str)

        return "\n\n".join(filter(None, context_parts))
