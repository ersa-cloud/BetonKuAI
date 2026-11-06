"""
BetonKu AI Assistant — Startup Script
Jalankan: python run.py
"""

import os
import sys
from pathlib import Path

# Pastikan dijalankan dari direktori yang benar
BASE_DIR = Path(__file__).parent.resolve()
os.chdir(BASE_DIR)  # Set working directory ke root proyek

# Cek apakah file .env ada
env_file = BASE_DIR / ".env"
env_example = BASE_DIR / ".env.example"

if not env_file.exists():
    if env_example.exists():
        print("=" * 60)
        print("[WARNING] FILE .env TIDAK DITEMUKAN!")
        print("=" * 60)
        print()
        print("Langkah-langkah setup:")
        print(f"  1. Salin file: copy .env.example .env")
        print(f"  2. Buka .env dan isi OPENAI_API_KEY Anda")
        print(f"  3. Jalankan kembali: python run.py")
        print()
        print("Contoh isi .env:")
        print("  OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx")
        print("  OPENAI_MODEL=gpt-4o-mini")
        print()
        # Buat .env kosong dari example agar server bisa jalan (dengan peringatan)
        import shutil
        shutil.copy(env_example, env_file)
        print("[OK] File .env telah dibuat dari .env.example")
        print("   Isi OPENAI_API_KEY sebelum menggunakan fitur AI chat.")
        print()
    else:
        print("[WARNING] File .env dan .env.example tidak ditemukan.")
        print("   Buat file .env dengan isi: OPENAI_API_KEY=sk-proj-xxx")
        print()

# Cek dependencies
try:
    import uvicorn
    import fastapi
    import openai
    import dotenv
except ImportError as e:
    missing = str(e).split("'")[1] if "'" in str(e) else str(e)
    print("=" * 60)
    print(f"[ERROR] DEPENDENCY TIDAK DITEMUKAN: {missing}")
    print("=" * 60)
    print()
    print("Install dependencies dengan:")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)

# Baca PORT dari .env atau default 8000
from dotenv import load_dotenv
load_dotenv(env_file)
port = int(os.getenv("PORT", "8000"))

print("=" * 60)
print("BetonKu AI Assistant")
print("   Solusi Beton Ready-Mix Terpercaya")
print("=" * 60)
print(f"   URL    : http://localhost:{port}")
print(f"   API    : http://localhost:{port}/api/health")
print(f"   Docs   : http://localhost:{port}/docs")
print(f"   Model  : {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key and not api_key.startswith("sk-your"):
    print(f"   API Key: [OK] Dikonfigurasi")
else:
    print(f"   API Key: [WARNING] BELUM DIKONFIGURASI - isi di file .env")
print("=" * 60)
print("   Tekan CTRL+C untuk menghentikan server")
print()

# Jalankan server uvicorn
import uvicorn
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=port,
    reload=True,
    reload_dirs=[str(BASE_DIR)],
    log_level="info"
)
