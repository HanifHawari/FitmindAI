"""
FitMind AI — Fitness Agent
Spesialis: Latihan gym, program workout, gerakan per body part.
Persona: Personal Trainer profesional.
"""
from agents.base_agent import BaseAgent
from data_loader import search_programs
from vector_store import get_workout_retriever


class FitnessAgent(BaseAgent):
    """
    Agent spesialis kebugaran & latihan.

    Dipanggil oleh SupervisorAgent untuk pertanyaan seputar:
    - Gerakan/latihan per bagian tubuh (dada, punggung, kaki, dll)
    - Rekomendasi program gym (beginner, intermediate, advanced)
    - Teknik latihan yang benar
    - Jadwal latihan mingguan
    """

    name = "FitnessAgent"
    description = "Spesialis latihan gym, program workout, dan gerakan per body part."

    system_prompt = """Kamu adalah asisten latihan FitMind AI dengan keahlian setara personal trainer berpengalaman 10 tahun.

KEPRIBADIAN:
- Tegas, motivatif, dan profesional.
- Hanya membahas topik gym, latihan, olahraga, dan kebugaran fisik.
- Jika ditanya di luar topik kebugaran ATAU input pengguna berupa kata acak/tidak bermakna (gibberish), tolak dengan sopan dan singkat.

KEMAMPUAN UTAMA:
1. Merekomendasikan gerakan/latihan berdasarkan bagian tubuh atau kelompok otot.
2. Membuat program latihan yang disesuaikan level pengguna (pemula, menengah, mahir).
3. Menjelaskan teknik gerakan yang benar dan aman.
4. Membuat jadwal latihan mingguan yang efektif.

ATURAN FORMAT RESPONS:
- Langsung ke poin, tanpa basa-basi.
- Gunakan **bold** untuk nama gerakan.
- Gunakan bullet points (•) untuk daftar.
- Sertakan set dan repetisi jika merekomendasikan latihan.
- Maksimal 1 emoji, atau tidak sama sekali.
- Semua angka set/rep harus konkret (contoh: 3 set x 12 rep).

ATURAN DATA:
- Jika ada [KONTEKS DATA RELEVAN], WAJIB jadikan acuan utama.
- Jika konteks kosong, gunakan pengetahuan bawaanmu sebagai PT untuk merekomendasikan latihan yang akurat. 
- JANGAN PERNAH menyebutkan kata "konteks" atau "database" kepada pengguna."""

    def build_context(self, message: str, user_profile: dict = None) -> str:
        """
        Ambil data latihan relevan dari dataset untuk dijadikan konteks RAG.
        """
        context_parts = []

        # Tambahkan profil user jika ada
        if user_profile:
            profile_str = "[PROFIL PENGGUNA]\n" + "\n".join(
                f"- {k}: {v}" for k, v in user_profile.items() if v
            )
            context_parts.append(profile_str)

        # Cari workout menggunakan Vector Database (ChromaDB)
        retriever = get_workout_retriever(k=5)
        if retriever:
            docs = retriever.invoke(message)
            if docs:
                lines = ["[DATA LATIHAN TERSEDIA (Dari Vector DB)]"]
                for doc in docs:
                    lines.append(f"- {doc.page_content}")
                context_parts.append("\n".join(lines))

        # Tambahkan data program jika relevan
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["program", "jadwal", "rencana", "minggu", "week", "plan"]):
            level = user_profile.get("experience_level", "") if user_profile else ""
            programs = search_programs(level=level, limit=5)
            if programs:
                lines = ["[DATA PROGRAM LATIHAN TERSEDIA]"]
                key_cols = ["title", "level", "goal", "equipment", "program_length",
                            "time_per_workout", "total_exercises", "description"]
                for p in programs[:5]:
                    parts = []
                    for col in key_cols:
                        val = p.get(col, "")
                        if col == "description" and isinstance(val, str) and len(val) > 200:
                            val = val[:197] + "..."
                        if val != "" and val is not None:
                            parts.append(f"{col}: {val}")
                    if parts:
                        lines.append("- " + " | ".join(parts))
                context_parts.append("\n".join(lines))

        return "\n\n".join(filter(None, context_parts))
