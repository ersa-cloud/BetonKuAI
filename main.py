"""
BetonKu AI Assistant - FastAPI Main Application
Entry point utama server backend.
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# ─── Absolute Paths (tidak bergantung pada working directory) ──────────────────
# BASE_DIR selalu menunjuk ke folder proyek tempat main.py berada,
# terlepas dari direktori mana uvicorn dijalankan.
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# Muat environment variables dari file .env SEBELUM import modul lain
# yang menggunakan os.getenv() saat module-load time (seperti app.agent).
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# Import setelah .env dimuat agar os.getenv() sudah tersedia dengan benar
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import run_agent

# ─── Penyimpanan Sesi (In-Memory) ──────────────────────────────────────────────
# Untuk produksi, ganti dengan Redis atau database. 
# Untuk sementara, simpan riwayat percakapan per session ID di memori.
sessions: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler untuk startup dan shutdown."""
    # Validasi bahwa API key sudah dikonfigurasi
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-your"):
        print("[WARNING] OPENAI_API_KEY belum dikonfigurasi di file .env")
        print("   Salin .env.example ke .env dan isi API key Anda.")
    else:
        print(f"[OK] OpenAI API Key terdeteksi (model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')})")

    print("[START] BetonKu AI Assistant siap dijalankan!")
    yield
    print("[STOP] BetonKu AI Assistant dimatikan.")


# ─── Inisialisasi FastAPI ──────────────────────────────────────────────────────
app = FastAPI(
    title="BetonKu AI Assistant API",
    description="API Backend untuk BetonKu AI Customer Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: Izinkan request dari browser (frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sajikan file statis frontend dari folder /static
# Gunakan path absolut agar tidak bergantung pada working directory saat uvicorn dijalankan
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body untuk endpoint /api/chat."""
    message: str = Field(..., min_length=1, max_length=2000, description="Pesan dari pelanggan")
    session_id: str = Field(default="", description="ID sesi percakapan (kosong = buat sesi baru)")


class ChatResponse(BaseModel):
    """Response body dari endpoint /api/chat."""
    session_id: str
    reply: str
    tool_calls_made: list[str]
    timestamp: str


class ResetRequest(BaseModel):
    """Request body untuk mereset sesi percakapan."""
    session_id: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Sajikan halaman utama frontend."""
    return FileResponse(str(INDEX_HTML))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    is_configured = bool(api_key) and api_key not in ("your-api-key-here", "sk-your-openai-api-key-here") and not api_key.startswith("http")
    return {
        "status": "ok",
        "service": "BetonKu AI Assistant",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key_configured": is_configured,
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint utama percakapan.
    Menerima pesan pelanggan, menjalankan AI Agent, dan mengembalikan respons.
    """
    # Validasi API key — tolak placeholder dan URL yang salah dimasukkan sebagai key
    api_key = os.getenv("OPENAI_API_KEY", "")
    invalid_key = (
        not api_key
        or api_key.startswith("sk-your")
        or api_key in ("your-api-key-here", "sk-your-openai-api-key-here")
        or api_key.startswith("http")   # URL salah dimasukkan di field API key
    )
    if invalid_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY belum dikonfigurasi dengan benar di file .env. "
                "Isi dengan API key yang valid (bukan URL). "
                "Untuk Groq: OPENAI_API_KEY=gsk_... dan OPENAI_BASE_URL=https://api.groq.com/openai/v1"
            )
        )

    # Buat atau ambil sesi percakapan
    session_id = request.session_id.strip()
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = []

    conversation_history = sessions[session_id]

    # Tambahkan pesan baru pelanggan ke riwayat
    conversation_history.append({
        "role": "user",
        "content": request.message
    })

    # Jalankan AI Agent
    try:
        result = run_agent(conversation_history)
    except RuntimeError as e:
        # RuntimeError dari _get_client() = API key tidak valid
        conversation_history.pop()
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Hapus pesan yang baru saja ditambahkan jika agent gagal
        conversation_history.pop()
        err_msg = str(e)
        # Deteksi error 401 dari API provider (key salah)
        if "401" in err_msg or "invalid_api_key" in err_msg or "Incorrect API key" in err_msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "API key tidak valid atau salah. "
                    "Periksa OPENAI_API_KEY di file .env. "
                    "Untuk Groq: pastikan OPENAI_BASE_URL=https://api.groq.com/openai/v1 juga diset."
                )
            )
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan saat memproses permintaan: {err_msg}"
        )

    # Simpan riwayat percakapan yang telah diperbarui
    sessions[session_id] = result["updated_history"]

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        tool_calls_made=result["tool_calls_made"],
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/chat/reset")
async def reset_session(request: ResetRequest):
    """Mereset (menghapus) riwayat percakapan untuk session ID tertentu."""
    session_id = request.session_id.strip()
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "ok", "message": "Sesi percakapan telah direset."}
    return {"status": "ok", "message": "Sesi tidak ditemukan (mungkin sudah direset sebelumnya)."}


@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    (Debugging) Mengambil riwayat percakapan untuk session ID tertentu.
    Berguna untuk debugging dan inspeksi percakapan.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")
    history = sessions[session_id]
    # Filter hanya pesan user dan assistant untuk keamanan
    filtered = [
        {"role": m["role"], "content": m.get("content", "")}
        for m in history
        if m["role"] in ("user", "assistant")
    ]
    return {
        "session_id": session_id,
        "message_count": len(filtered),
        "history": filtered
    }


# ─── Error Handlers ────────────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Terjadi kesalahan internal server."}
    )
