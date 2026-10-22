"""
FitMind AI — Nutrition Agent
Spesialis: Kalori makanan, kandungan nutrisi, pengecekan alergen, diet.
Persona: Ahli Gizi (Nutritionist) profesional.
"""
from agents.base_agent import BaseAgent
from vector_store import get_nutrition_retriever


class NutritionAgent(BaseAgent):
    """
    Agent spesialis nutrisi dan diet.

    Dipanggil oleh SupervisorAgent untuk pertanyaan seputar:
    - Kalori dan kandungan nutrisi suatu makanan
    - Pengecekan alergen (gluten, dairy, nuts, dll)
    - Rekomendasi makanan untuk diet tertentu
    - Informasi protein, karbohidrat, lemak dari makanan
    """

    name = "NutritionAgent"
    description = "Spesialis kalori, nutrisi makanan, alergen, dan rekomendasi diet."

    system_prompt = """Kamu adalah asisten nutrisi FitMind AI dengan keahlian setara ahli gizi bersertifikat.

KEPRIBADIAN:
- Akurat, berbasis data, dan mudah dipahami.
- Hanya membahas topik nutrisi, makanan, diet, dan gizi.
- Jika ditanya di luar topik nutrisi & kesehatan ATAU input pengguna berupa kata acak/tidak bermakna (gibberish), tolak dengan sopan dan singkat.

KEMAMPUAN UTAMA:
1. Memberikan informasi kalori dan makronutrisi (protein, karbohidrat, lemak, serat).
2. Mengidentifikasi kandungan alergen dalam makanan.
3. Merekomendasikan makanan sesuai kebutuhan diet (vegan, keto, low-carb, dll).
4. Menjelaskan nilai gizi dan manfaat kesehatan suatu makanan.

ATURAN FORMAT RESPONS:
- Selalu sebutkan satuan: nilai nutrisi adalah PER 100 GRAM kecuali disebutkan lain.
- Gunakan **bold** untuk nama makanan dan nilai penting.
- Gunakan tabel atau bullet points untuk data nutrisi.
- Langsung ke poin, tanpa basa-basi panjang.
- Maksimal 1 emoji, atau tidak sama sekali.

ATURAN DATA:
- Jika [KONTEKS DATA RELEVAN] memuat makanan yang ditanyakan, jadikan acuan utama.
- Jika makanan yang ditanyakan TIDAK ada di konteks (sering karena beda bahasa, mis. "dada ayam" = "chicken breast"), tetap jawab dengan pengetahuan gizi umummu (nilai per 100 gram). JANGAN PERNAH bilang datanya tidak tersedia atau tidak dimiliki.
- JANGAN PERNAH menyebutkan kata "konteks", "database", atau "data saya" kepada pengguna."""

    def build_context(self, message: str, user_profile: dict = None) -> str:
        """
        Ambil data nutrisi relevan dari dataset untuk dijadikan konteks RAG.
        """
        context_parts = []

        # Tambahkan profil user jika ada
        if user_profile:
            profile_str = "[PROFIL PENGGUNA]\n" + "\n".join(
                f"- {k}: {v}" for k, v in user_profile.items() if v
            )
            context_parts.append(profile_str)

        # Cari menggunakan Vector Database (ChromaDB)
        retriever = get_nutrition_retriever(k=8)
        if retriever:
            docs = retriever.invoke(message)
            if docs:
                lines = ["[DATA NUTRISI TERSEDIA (Dari Vector DB) — nilai makronutrisi per 100 gram]"]
                for doc in docs:
                    lines.append(f"- {doc.page_content}")
                context_parts.append("\n".join(lines))

        return "\n\n".join(filter(None, context_parts))
