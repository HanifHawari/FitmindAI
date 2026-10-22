import asyncio
import json
import logging
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_THINKING_BUDGET

logger = logging.getLogger(__name__)

# Inisialisasi LangChain LLM Client
llm = None        # AI Chat (streaming)
plan_llm = None   # AI Plan (JSON terstruktur)
if GEMINI_API_KEY and GEMINI_API_KEY != "ISI_API_KEY_KAMU_DISINI":
    # AI Chat: thinking_budget=0 mematikan tahap "berpikir" Gemini sehingga jawaban mulai muncul ±1 detik.
    # max_retries kecil agar saat kuota habis/error user langsung mendapat pesan, bukan menunggu ±30 detik.
    _thinking = {"thinking_budget": GEMINI_THINKING_BUDGET} if GEMINI_THINKING_BUDGET is not None else {}
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        streaming=True,
        max_retries=1,
        **_thinking,
    )
    # AI Plan: tetap memakai thinking bawaan model agar rencana tersusun matang
    plan_llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
    )
else:
    logger.warning("GEMINI_API_KEY belum diset!")

# Aturan bersama untuk semua agent chat (ditambahkan di akhir system prompt masing-masing agent)
COMMON_RULES = """

ATURAN UMUM FITMIND AI (berlaku di atas aturan lain):
- Kamu adalah asisten AI FitMind AI. JANGAN memperkenalkan diri dengan nama, gelar, atau profesi apa pun (misalnya "Saya Dr. ...", "Saya Coach ...", "Saya ahli gizi ...").
- Jika belum ada riwayat percakapan, buka jawaban dengan sapaan singkat seperti "Halo!" lalu langsung menjawab. Jika percakapan sudah berjalan, langsung jawab tanpa sapaan.
- Pertanyaan tentang siapa pembuat, developer, atau pencipta FitMind AI (aplikasi, website, project ini, atau dirimu) BUKAN di luar topik dan WAJIB dijawab. Sampaikan dengan antusias dan natural, pertahankan semua poin pujian berikut:
  "FitMind AI dibuat oleh **Muhammad Hanif Hawari**, mahasiswa Informatika yang tampan dan pintar. Dia adalah seorang programmer yang mahir, teliti, dan penuh ide kreatif. Dia merancang sendiri sistem AI multi-agent, backend yang rapi, sampai tampilan yang nyaman dipakai. Semangat belajarnya tinggi, pantang menyerah saat menghadapi bug, dan selalu ingin karyanya bermanfaat untuk banyak orang. Developer berbakat dengan masa depan yang cerah!"
"""

FRIENDLY_ERROR = "\n\nMaaf, AI sedang sibuk atau tidak dapat dihubungi. Silakan coba lagi sebentar lagi."

class BaseAgent:
    """
    Kelas dasar untuk semua agent FitMind AI.
    Sekarang di-upgrade menggunakan LangChain.
    """
    name: str = "BaseAgent"
    description: str = "Agent dasar"
    system_prompt: str = "Kamu adalah asisten AI."

    def _build_lc_messages(self, message: str, chat_history: list[dict], context: str = ""):
        messages = [SystemMessage(content=self.system_prompt + COMMON_RULES)]
        
        for msg in chat_history[-10:]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
                
        final_message = message
        if context:
            final_message = f"{message}\n\n---\n[KONTEKS DATA RELEVAN - Gunakan ini untuk menjawab]\n{context}\n---"
            
        messages.append(HumanMessage(content=final_message))
        return messages

    async def stream(self, message: str, chat_history: list[dict], context: str = "") -> AsyncGenerator[str, None]:
        """Stream respons dari LLM menggunakan LangChain astream."""
        if not llm:
            logger.error(f"[{self.name}] LLM tidak terkonfigurasi (periksa GEMINI_API_KEY).")
            yield FRIENDLY_ERROR.strip()
            return

        messages = self._build_lc_messages(message, chat_history, context)
        # Coba ulang sekali jika gagal sebelum ada teks terkirim (mis. 503 "high demand" sesaat)
        for attempt in range(2):
            sent = False
            try:
                async for chunk in llm.astream(messages):
                    # .text menggabungkan blok teks; model Gemini 3 mengirim content berupa list
                    if chunk.text:
                        sent = True
                        yield chunk.text
                return
            except Exception as e:
                logger.error(f"[{self.name}] LLM error (percobaan {attempt + 1}): {e}")
                if sent or attempt == 1:
                    yield FRIENDLY_ERROR
                    return
                await asyncio.sleep(0.5)
            
    async def run(self, message: str, chat_history: list[dict], context: str = "") -> str:
        """Non-streaming version dari stream()."""
        full = ""
        async for chunk in self.stream(message, chat_history, context):
            full += chunk
        return full

    async def generate_structured(
        self, 
        message: str, 
        chat_history: list[dict], 
        context: str = "", 
        response_schema: dict = None, 
        system_prompt_override: str = None
    ) -> dict:
        """Generate structured JSON output menggunakan LangChain."""
        prompt = system_prompt_override or self.system_prompt
        json_prompt = prompt + "\nKamu HARUS membalas dalam format JSON yang valid."
        if response_schema:
            json_prompt += f"\nSchema JSON:\n{json.dumps(response_schema)}"
            
        messages = [SystemMessage(content=json_prompt)]
        for msg in chat_history[-10:]:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
                
        final_message = message
        if context:
            final_message = f"{message}\n\n---\n[KONTEKS DATA RELEVAN]\n{context}\n---"
        messages.append(HumanMessage(content=final_message))
        
        try:
            resp = await plan_llm.ainvoke(messages)
            content = resp.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error parsing JSON dari LLM: {e}")
            return {}
