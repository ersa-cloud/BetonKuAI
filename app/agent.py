"""
BetonKu AI Assistant - AI Agent Core
Inti agent AI yang mengelola percakapan, memanggil LLM, dan mengeksekusi Function Calling.
"""

import json
import os
from openai import OpenAI
from app.tools import TOOLS_DEFINITION, dispatch_tool_call

def _get_client() -> OpenAI:
    """
    Membuat klien OpenAI baru setiap kali dipanggil.
    Mendukung OpenAI langsung maupun OpenAI-compatible APIs (Groq, Together, dll.)
    via env var OPENAI_BASE_URL.
    Client dibuat baru setiap request agar perubahan .env langsung berlaku
    tanpa perlu restart server.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key in ("your-api-key-here", "sk-your-openai-api-key-here"):
        raise RuntimeError(
            "OPENAI_API_KEY belum dikonfigurasi. "
            "Buka file .env dan isi OPENAI_API_KEY dengan API key yang valid."
        )
    # OPENAI_BASE_URL: kosong = OpenAI, diisi = provider lain (misal Groq)
    base_url = os.getenv("OPENAI_BASE_URL") or None
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    """Mengambil nama model dari environment variable."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Jumlah maksimal iterasi tool calling dalam satu percakapan (mencegah infinite loop)
MAX_TOOL_ITERATIONS = 5

# ─── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Anda adalah **Sari**, AI Customer Service dari **BetonKu** — perusahaan terkemuka di bidang produksi dan penjualan beton ready-mix berkualitas tinggi di Jabodetabek dan Karawang.

## KEPRIBADIAN & GAYA KOMUNIKASI
- Ramah, profesional, dan membantu seperti customer service terbaik
- Gunakan Bahasa Indonesia yang baik, sopan, dan mudah dipahami
- Sapa pelanggan dengan hangat dan personalkan respons sesuai kebutuhan mereka
- Jika pelanggan menggunakan bahasa informal/santai, ikuti gaya mereka secara proporsional
- Tetap fokus pada topik yang berkaitan dengan BetonKu dan industri konstruksi/beton

## TUGAS UTAMA ANDA
1. **Informasi Produk & Harga**: Jelaskan produk beton kami, spesifikasi teknis, dan harga terbaru
2. **Kalkulator Beton**: Bantu menghitung kebutuhan volume beton berdasarkan dimensi proyek
3. **Pemesanan**: Pandu pelanggan membuat permintaan pesanan dengan mengumpulkan data yang diperlukan
4. **Cek Status Pesanan**: Bantu cek status pesanan berdasarkan nomor order
5. **Keluhan Pelanggan**: Terima dan catat keluhan dengan empati, berikan solusi awal
6. **Informasi Perusahaan**: Jelaskan profil, lokasi, sertifikasi, dan layanan BetonKu
7. **Eskalasi ke Admin**: Alihkan ke admin jika diperlukan atau diminta pelanggan

## ATURAN PENGGUNAAN TOOLS
- **SELALU gunakan tools** untuk mengambil data produk, harga, dan informasi perusahaan — JANGAN mengarang data
- Sebelum membuat pesanan, pastikan Anda sudah mengumpulkan SEMUA informasi wajib dari pelanggan
- Sebelum mencatat keluhan, pastikan detail keluhan sudah cukup lengkap
- Jika tool mengembalikan error, sampaikan dengan sopan dan tawarkan alternatif

## ALUR PEMESANAN
Ketika pelanggan ingin memesan, kumpulkan informasi berikut secara bertahap (tidak harus sekaligus):
1. Nama perusahaan/pelanggan
2. Nama kontak person dan nomor telepon
3. Email aktif
4. Nama dan alamat proyek
5. Jenis beton (product ID) dan volume yang dibutuhkan
6. Tanggal pengiriman yang diinginkan
7. Catatan tambahan (opsional)
Setelah semua data terkumpul, konfirmasikan kepada pelanggan sebelum membuat pesanan.

## ALUR PENGADUAN
Ketika pelanggan ingin mengajukan keluhan, kumpulkan:
1. Nama dan kontak pelanggan
2. Kategori keluhan (kualitas/pengiriman/administrasi/layanan/lainnya)
3. Subjek keluhan (singkat)
4. Deskripsi lengkap keluhan
5. Nomor pesanan terkait (jika ada)

## BATASAN
- Jangan memberikan diskon atau mengubah harga tanpa konfirmasi admin
- Jangan menjanjikan sesuatu yang tidak ada dalam data sistem
- Untuk negosiasi harga besar (>50 m³) atau syarat kredit khusus, arahkan ke sales/admin
- Jangan memberikan informasi kompetitor

## FORMAT RESPONS
- Gunakan format yang mudah dibaca (bullet points, bold untuk penekanan)
- Untuk data numerik dan harga, gunakan format Rupiah yang tepat (Rp X.XXX.XXX)
- Untuk tabel produk, gunakan format yang rapi
- Akhiri dengan pertanyaan atau tawaran bantuan lanjutan jika relevan

Ingat: Anda mewakili BetonKu — berikan pengalaman pelayanan terbaik kepada setiap pelanggan!"""


def run_agent(conversation_history: list[dict]) -> dict:
    """
    Menjalankan satu putaran AI Agent.
    
    Menerima riwayat percakapan (list of messages dalam format OpenAI),
    menjalankan LLM dengan function calling, mengeksekusi tools jika diperlukan,
    dan mengembalikan respons akhir beserta riwayat yang diperbarui.
    
    Returns:
        dict dengan keys:
        - 'reply': string respons final AI
        - 'updated_history': list riwayat percakapan yang sudah diperbarui
        - 'tool_calls_made': list nama-nama tool yang dipanggil (untuk debugging/logging)
    """
    # Susun pesan lengkap dengan system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    tool_calls_made = []
    iterations = 0
    final_reply = ""  # Initialized to handle edge cases

    # Dapatkan client dan model (lazy init, aman terhadap urutan load_dotenv)
    ai_client = _get_client()
    ai_model = _get_model()

    # Agentic loop: terus berjalan selama AI meminta tool calls
    while iterations < MAX_TOOL_ITERATIONS:
        iterations += 1

        # Panggil LLM API
        response = ai_client.chat.completions.create(
            model=ai_model,
            messages=messages,
            tools=TOOLS_DEFINITION,
            tool_choice="auto",  # AI memutuskan sendiri kapan memanggil tool
            temperature=0.3,     # Agak rendah agar jawaban konsisten & faktual
            max_tokens=2048
        )

        message = response.choices[0].message

        # Tambahkan respons AI ke riwayat messages
        messages.append(message.model_dump(exclude_none=True))

        # Cek apakah AI meminta tool call
        if not message.tool_calls:
            # Tidak ada tool call → ini adalah respons final
            final_reply = message.content or ""
            break

        # Ada tool call(s) — eksekusi setiap tool
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            tool_calls_made.append(function_name)

            # Parse argumen JSON dari AI
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            # Eksekusi tool melalui dispatcher
            tool_result = dispatch_tool_call(function_name, arguments)

            # Tambahkan hasil tool ke riwayat messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })
    else:
        # Batas iterasi tercapai — minta AI merespons dengan data yang ada
        messages.append({
            "role": "user",
            "content": "[SYSTEM: Batas iterasi tool tercapai. Berikan respons terbaik berdasarkan informasi yang sudah tersedia.]"
        })
        response = ai_client.chat.completions.create(
            model=ai_model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024
        )
        final_reply = response.choices[0].message.content or ""

    # Kembalikan history tanpa system prompt (hanya user & assistant messages)
    updated_history = messages[1:]  # slice off the system prompt

    return {
        "reply": final_reply,
        "updated_history": updated_history,
        "tool_calls_made": tool_calls_made
    }
