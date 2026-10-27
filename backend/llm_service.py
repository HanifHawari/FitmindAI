"""
FitMind AI — LLM Service (Entry Point Multi-Agent System)

File ini sekarang berfungsi sebagai ENTRY POINT dan compatibility layer.
Semua logika AI sekarang didelegasikan ke sistem multi-agent di folder /agents/.

Arsitektur Multi-Agent:
  SupervisorAgent
    ├── FitnessAgent   → Latihan, gym, program workout
    ├── NutritionAgent → Kalori, nutrisi, alergen, diet
    └── HealthAgent    → BMI, kalori terbakar, analisis kesehatan

Flow:
  User message
    → SupervisorAgent.route_and_stream()
      → _classify_intent() [Regex-based classification]
        → Agent terpilih.build_context() [RAG dari CSV]
          → Agent terpilih.stream() [LLM respons]
            → User
"""
import logging
from typing import AsyncGenerator

from agents.supervisor import SupervisorAgent, _classify_by_regex

logger = logging.getLogger(__name__)

# ==============================================================
# Singleton Supervisor — satu instance digunakan sepanjang runtime
# ==============================================================
_supervisor = SupervisorAgent()


# ==============================================================
# Public API — dipanggil oleh routers/chat.py
# (interface sama persis seperti sebelumnya agar tidak perlu
#  ubah banyak kode di chat.py)
# ==============================================================

async def chat_stream(
    message: str,
    chat_history: list[dict],
    user_profile: dict = None
) -> AsyncGenerator[str, None]:
    """
    Stream respons dari sistem multi-agent.

    Supervisor akan:
    1. Mengklasifikasikan intent pesan menggunakan Regex untuk respons instan.
    2. Mendelegasikan ke agent spesialis yang tepat.
    3. Streaming respons agent ke pemanggil.

    Args:
        message: Pesan user terbaru
        chat_history: Riwayat percakapan [{"role": "user"/"assistant", "content": "..."}]
        user_profile: Profil user dari frontend (opsional)

    Yields:
        Potongan teks dari agent yang dipilih
    """
    logger.info(f"[LLM Service] Menerima pesan, mendelegasikan ke Supervisor...")
    async for chunk in _supervisor.route_and_stream(message, chat_history, user_profile):
        yield chunk
    logger.info(f"[LLM Service] Ditangani oleh: {_supervisor.get_last_agent().upper()}")


async def chat_simple(
    message: str,
    chat_history: list[dict],
    user_profile: dict = None
) -> str:
    """Non-streaming version dari chat_stream()."""
    full_response = ""
    async for chunk in chat_stream(message, chat_history, user_profile):
        full_response += chunk
    return full_response


def detect_intent(message: str) -> tuple[str, dict]:
    """
    Deteksi intent dari pesan user (digunakan oleh chat.py untuk logging DB).

    Sekarang menggunakan klasifikasi berbasis kata kunci (Regex) 
    agar lebih cepat dan efisien.

    Returns:
        (agent_name, {}) — agent_name: "fitness", "nutrition", atau "health"
    """
    agent_name = _classify_by_regex(message)
    return agent_name, {}


# ==============================================================
# Utility — untuk endpoint /api/chat/intents dan debugging
# ==============================================================

def list_agents() -> dict[str, str]:
    """Kembalikan semua agent yang terdaftar."""
    return SupervisorAgent.list_agents()
