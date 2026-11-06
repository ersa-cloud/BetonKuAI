
"""
BetonKu AI Assistant - FastAPI Main Application
Entry point utama server backend.
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# Muat environment variables untuk penggunaan lokal.
# Di Vercel, gunakan Environment Variables pada dashboard.
load_dotenv(BASE_DIR / ".env")

# ============================================================
# IMPORTS
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.agent import run_agent


# ============================================================
# SESSION STORAGE
# ============================================================

# Penyimpanan sementara di memori.
# Catatan: sesi tidak dijamin bertahan setelah instance
# serverless Vercel berhenti atau berganti.
sessions: dict[str, list[dict]] = {}


# ============================================================
# API KEY VALIDATION
# ============================================================

def is_api_key_configured() -> bool:
    """Memeriksa apakah API key sudah dikonfigurasi."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    invalid_keys = (
        "",
        "your-api-key-here",
        "sk-your-openai-api-key-here",
    )

    return api_key not in invalid_keys and not api_key.startswith("http")


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler untuk startup dan shutdown."""

    if not is_api_key_configured():
        print("[WARNING] OPENAI_API_KEY belum dikonfigurasi.")
    else:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"[OK] API Key terdeteksi. Model: {model}")

    print("[START] BetonKu AI Assistant siap dijalankan!")

    yield

    print("[STOP] BetonKu AI Assistant dimatikan.")


# ============================================================
# FASTAPI INITIALIZATION
# ============================================================

app = FastAPI(
    title="BetonKu AI Assistant API",
    description="API Backend untuk BetonKu AI Customer Service",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# STATIC FILES
# ============================================================

if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ChatRequest(BaseModel):
    """Request body untuk endpoint /api/chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pesan dari pelanggan",
    )

    session_id: str = Field(
        default="",
        description="ID sesi percakapan",
    )


class ChatResponse(BaseModel):
    """Response body dari endpoint /api/chat."""

    session_id: str
    reply: str
    tool_calls_made: list[str]
    timestamp: str


class ResetRequest(BaseModel):
    """Request body untuk mereset sesi percakapan."""

    session_id: str


# ============================================================
# FRONTEND ENDPOINT
# ============================================================

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Menyajikan halaman utama frontend."""

    if not INDEX_HTML.exists():
        raise HTTPException(
            status_code=404,
            detail="File frontend index.html tidak ditemukan.",
        )

    return FileResponse(str(INDEX_HTML))


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health_check():
    """Memeriksa status aplikasi."""

    return {
        "status": "ok",
        "service": "BetonKu AI Assistant",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key_configured": is_api_key_configured(),
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint utama percakapan.

    Menerima pesan pelanggan, menjalankan AI Agent,
    dan mengembalikan respons.
    """

    # Validasi API key
    if not is_api_key_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "API key belum dikonfigurasi. "
                "Periksa OPENAI_API_KEY pada Environment Variables."
            ),
        )

    # Membuat atau mengambil session ID
    session_id = request.session_id.strip()

    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in sessions:
        sessions[session_id] = []

    conversation_history = sessions[session_id]

    # Tambahkan pesan pengguna
    conversation_history.append({
        "role": "user",
        "content": request.message,
    })

    # Jalankan AI Agent
    try:
        result = run_agent(conversation_history)

    except RuntimeError as e:
        conversation_history.pop()

        print(f"[AGENT ERROR] {e}")

        raise HTTPException(
            status_code=503,
            detail="Layanan AI sedang tidak tersedia. Silakan coba kembali.",
        )

    except Exception as e:
        conversation_history.pop()

        err_msg = str(e)

        print(f"[CHAT ERROR] {err_msg}")

        # Deteksi kesalahan API key
        if (
            "401" in err_msg
            or "invalid_api_key" in err_msg
            or "Incorrect API key" in err_msg
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    "API key tidak valid. "
                    "Periksa konfigurasi API key dan provider AI."
                ),
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Terjadi kesalahan saat memproses pesan. "
                "Silakan coba kembali."
            ),
        )

    # Simpan riwayat percakapan di memori
    sessions[session_id] = result["updated_history"]

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        tool_calls_made=result["tool_calls_made"],
        timestamp=datetime.now().isoformat(),
    )


# ============================================================
# RESET SESSION
# ============================================================

@app.post("/api/chat/reset")
async def reset_session(request: ResetRequest):
    """Menghapus riwayat percakapan berdasarkan session ID."""

    session_id = request.session_id.strip()

    if session_id in sessions:
        del sessions[session_id]

        return {
            "status": "ok",
            "message": "Sesi percakapan telah direset.",
        }

    return {
        "status": "ok",
        "message": "Sesi tidak ditemukan atau sudah direset.",
    }


# ============================================================
# SESSION HISTORY
# ============================================================

@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Mengambil riwayat percakapan untuk keperluan debugging."""

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Sesi tidak ditemukan.",
        )

    history = sessions[session_id]

    # Hanya tampilkan pesan user dan assistant
    filtered_history = [
        {
            "role": message["role"],
            "content": message.get("content", ""),
        }
        for message in history
        if message.get("role") in ("user", "assistant")
    ]

    return {
        "session_id": session_id,
        "message_count": len(filtered_history),
        "history": filtered_history,
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Menangani HTTP exception."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """Menangani kesalahan internal server."""

    print(f"[INTERNAL SERVER ERROR] {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Terjadi kesalahan internal server.",
        },
    )
