# 🏗️ BetonKu AI Assistant

> **AI Customer Service** untuk perusahaan beton ready-mix BetonKu — dibangun dengan FastAPI, OpenAI Function Calling, Tailwind CSS, dan Vanilla JavaScript.

![BetonKu AI Assistant](https://img.shields.io/badge/BetonKu-AI_Assistant-0f2044?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat&logo=openai&logoColor=white)

---

## 📋 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Arsitektur Aplikasi](#-arsitektur-aplikasi)
- [Prasyarat](#-prasyarat)
- [Instalasi & Menjalankan](#-instalasi--menjalankan)
- [Cara Penggunaan](#-cara-penggunaan)
- [Struktur Proyek](#-struktur-proyek)
- [Konfigurasi](#-konfigurasi)
- [Function Calling — Daftar Tools AI](#-function-calling--daftar-tools-ai)
- [Data Dummy](#-data-dummy)
- [Pengembangan Lanjut](#-pengembangan-lanjut)

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🤖 **AI Chat Kontekstual** | AI Agent (Sari) yang memahami konteks percakapan multi-turn menggunakan GPT-4o-mini |
| 📦 **Katalog Produk & Harga** | Informasi lengkap 9 produk beton K-175 hingga Fiber Reinforced Concrete dengan harga real-time dari JSON |
| 🔢 **Kalkulator Beton** | Hitung kebutuhan volume beton untuk 8 tipe elemen (balok, kolom, pondasi, plat lantai, jalan, dll.) lengkap dengan estimasi biaya |
| 📝 **Form Pemesanan** | AI memandu pengisian data pesanan secara natural, validasi, dan menyimpan ke JSON |
| 🔍 **Cek Status Pesanan** | Cek status pesanan real-time berdasarkan nomor order (BK-YYYY-NNN) |
| 📢 **Pencatatan Keluhan** | AI menerima keluhan pelanggan, kategorisasi otomatis, dan pencatatan ke sistem |
| 👤 **Eskalasi ke Admin** | Pengalihan percakapan ke admin/sales dengan informasi kontak dan tingkat urgensi |
| 🔧 **Function Calling** | 8 tools yang dapat dipanggil AI secara otomatis sesuai konteks percakapan |
| 💾 **Manajemen Sesi** | Riwayat percakapan per sesi dengan persistensi di localStorage browser |

---

## 🏛️ Arsitektur Aplikasi

```
Browser (Tailwind CSS + Vanilla JS)
        │
        │  HTTP/JSON (REST API)
        ▼
FastAPI Server (main.py)
        │
        ▼
AI Agent (app/agent.py)
   ├── System Prompt (Sari persona)
   ├── OpenAI GPT-4o-mini
   └── Agentic Loop (max 5 iterasi)
            │
            ▼ Function Calling
   Tool Dispatcher (app/tools.py)
   ├── get_product_catalog
   ├── get_product_detail
   ├── calculate_concrete_volume
   ├── get_company_information
   ├── create_order_request
   ├── check_order_status
   ├── submit_complaint
   └── request_admin_handoff
            │
            ▼
   Data Manager (app/data_manager.py)
   ├── data/products.json
   ├── data/orders.json
   ├── data/complaints.json
   └── data/company_info.json
```

---

## 🛠️ Prasyarat

- **Python 3.11+** (direkomendasikan 3.11 atau 3.12)
- **OpenAI API Key** — daftar di [platform.openai.com](https://platform.openai.com)
- **pip** atau **uv** (package manager)
- Koneksi internet (untuk mengakses OpenAI API dan Tailwind CSS CDN)

---

## 🚀 Instalasi & Menjalankan

### 1. Clone atau buka folder proyek

```bash
# Jika dari repository
git clone <repository-url>
cd betonku-ai-assistant

# Atau langsung buka folder proyek
cd "BetonKu AI Assistant2"
```

### 2. Buat Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies (untuk Tailwind CSS CLI)

> Prasyarat: [Node.js](https://nodejs.org/) versi 18+

```bash
npm install
```

### 5. Konfigurasi Environment Variables

```bash
# Salin file contoh
cp .env.example .env   # macOS/Linux
copy .env.example .env  # Windows
```

Buka file `.env` dan isi nilai berikut:

```env
# Wajib: API Key OpenAI Anda
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx

# Opsional: Ganti model (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Opsional: Port server (default: 8000)
PORT=8000
```

### 6. Jalankan Server

**Cara termudah** — gunakan script launcher yang otomatis mengatur working directory:
```bash
python run.py
```

**Atau langsung dengan uvicorn** (pastikan dijalankan dari folder root proyek):
```bash
# PENTING: harus dijalankan dari folder root proyek (tempat main.py berada)
cd "BetonKu AI Assistant2"

uvicorn main:app --reload --port 8000
```

> ⚠️ **Catatan penting:** Jika uvicorn tidak dijalankan dari folder root proyek,
> server tidak akan menemukan folder `static/` dan fitur chat tidak akan berfungsi.
> Gunakan `python run.py` untuk menghindari masalah ini secara otomatis.

### 7. Buka Aplikasi

Buka browser dan akses: **http://localhost:8000**

---

## 🎨 Tailwind CSS CLI

Aplikasi menggunakan **Tailwind CSS v4 CLI** — tidak ada CDN, semua CSS dikompilasi secara lokal.

### File-file yang terlibat

| File | Keterangan |
|------|-----------|
| `static/css/tailwind.input.css` | **Source** — Definisi `@theme` (warna brand, shadow, font) + directive `@import "tailwindcss"` |
| `static/css/tailwind.output.css` | **Output** — CSS yang sudah dikompilasi & diminify, dimuat langsung oleh browser |
| `package.json` | Berisi npm scripts untuk build dan watch |

### Cara Menjalankan Tailwind CLI

```bash
# Build sekali (produksi) — hasilkan file output yang diminify
npm run css:build

# Watch mode (development) — auto-rebuild saat ada perubahan
npm run css:watch
```

Atau langsung tanpa npm script:
```bash
# Build manual
npx @tailwindcss/cli -i ./static/css/tailwind.input.css -o ./static/css/tailwind.output.css --minify

# Watch manual
npx @tailwindcss/cli -i ./static/css/tailwind.input.css -o ./static/css/tailwind.output.css --watch
```

### Kapan perlu recompile?

Recompile diperlukan **setiap kali** Anda:
- Menambah kelas Tailwind baru di `index.html` atau JS
- Mengubah warna, shadow, atau font di `tailwind.input.css`
- **Tidak perlu** recompile jika hanya mengubah Python/logic backend

---

## 💬 Cara Penggunaan

### Bertanya tentang Produk & Harga
```
"Tampilkan semua produk beton beserta harganya"
"Berapa harga beton K-300 per m³?"
"Apa perbedaan beton K-250 dan K-300?"
```

### Menghitung Kebutuhan Beton
```
"Hitung kebutuhan beton untuk plat lantai 10m x 8m tebal 12cm"
"Berapa m³ beton untuk 10 kolom ukuran 40x40cm tinggi 4 meter?"
"Saya butuh beton untuk jalan 500m panjang, lebar 6m, tebal 20cm"
```

### Membuat Pesanan
```
"Saya ingin memesan beton K-250 sebanyak 30 m³"
[AI akan memandu Anda mengisi data yang diperlukan secara bertahap]
```

### Mengecek Status Pesanan
```
"Cek status pesanan BK-2025-001"
"Pesanan saya dengan nomor BK-2025-003 sudah sampai mana?"
```

### Mengajukan Keluhan
```
"Saya ingin melaporkan keluhan terkait beton yang tidak sesuai spesifikasi"
"Truk mixer terlambat 3 jam dari jadwal yang dijanjikan"
```

### Menghubungi Admin
```
"Saya ingin berbicara dengan sales BetonKu"
"Tolong hubungkan saya dengan admin untuk negosiasi harga"
```

---

## 📁 Struktur Proyek

```
BetonKu AI Assistant2/
│
├── main.py                    # FastAPI app, routing, session management
├── run.py                     # Launcher script (set workdir, cek .env & deps)
├── requirements.txt           # Python dependencies
├── package.json               # Node.js deps + npm scripts (css:build, css:watch)
├── .env.example               # Template environment variables
├── .env                       # (buat sendiri, tidak di-commit)
│
├── app/                       # Backend modules
│   ├── __init__.py
│   ├── agent.py               # AI Agent core & agentic loop (lazy OpenAI client)
│   ├── tools.py               # 8 Tool definitions & handlers (Function Calling)
│   └── data_manager.py        # JSON data CRUD operations (Path-based)
│
├── data/                      # JSON data storage (dummy data)
│   ├── products.json          # Katalog 9 produk beton + harga
│   ├── orders.json            # Data pesanan pelanggan
│   ├── complaints.json        # Data keluhan pelanggan
│   └── company_info.json      # Profil, FAQ, info pengiriman & pembayaran
│
└── static/                    # Frontend (disajikan oleh FastAPI)
    ├── index.html             # Halaman utama aplikasi
    ├── css/
    │   ├── tailwind.input.css  # SOURCE Tailwind v4: @theme + custom styles
    │   ├── tailwind.output.css # OUTPUT compiled CSS (dimuat oleh browser)
    │   └── style.css           # (legacy, tidak dimuat — referensi saja)
    └── js/
        └── app.js             # Frontend logic, markdown renderer, Fetch API
```

---

## ⚙️ Konfigurasi

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `OPENAI_API_KEY` | *(wajib)* | API key dari OpenAI platform |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model OpenAI yang digunakan. Bisa diganti ke `gpt-4o` untuk akurasi lebih tinggi |
| `PORT` | `8000` | Port server FastAPI |

### Mengganti Model AI

Untuk akurasi yang lebih tinggi (dengan biaya lebih besar), ubah di `.env`:

```env
OPENAI_MODEL=gpt-4o
```

---

## 🔧 Function Calling — Daftar Tools AI

AI Agent (Sari) dapat memanggil 8 tools berikut secara otomatis:

| Tool | Deskripsi |
|------|-----------|
| `get_product_catalog` | Mengambil katalog lengkap semua produk beton & harga |
| `get_product_detail` | Mengambil detail satu produk berdasarkan ID (K200, K300, dll.) |
| `calculate_concrete_volume` | Menghitung volume beton berdasarkan dimensi elemen struktur |
| `get_company_information` | Mengambil profil, kontak, FAQ, info pengiriman & pembayaran |
| `create_order_request` | Membuat pesanan baru dan menyimpannya ke JSON |
| `check_order_status` | Mengecek status pesanan berdasarkan order ID |
| `submit_complaint` | Mencatat keluhan pelanggan ke sistem |
| `request_admin_handoff` | Memproses permintaan eskalasi ke admin/sales |

### Alur Function Calling (Agentic Loop)

```
User Message
     │
     ▼
OpenAI API (model + tools)
     │
     ├── Tool Call Requested? ─── YES ──► Execute Tool ──► Feed Result Back ──► Loop
     │
     └── NO (final answer)
          │
          ▼
     Response to User
```

Maksimum **5 iterasi** per pesan untuk mencegah infinite loop.

---

## 📊 Data Dummy

### Produk Beton (9 produk)
| ID | Nama | Harga/m³ |
|----|------|---------|
| K175 | Beton K-175 | Rp 840.000 |
| K200 | Beton K-200 | Rp 890.000 |
| K225 | Beton K-225 | Rp 940.000 |
| K250 | Beton K-250 | Rp 995.000 |
| K300 | Beton K-300 | Rp 1.085.000 |
| K350 | Beton K-350 | Rp 1.195.000 |
| K400 | Beton K-400 | Rp 1.350.000 |
| SCC | Self Compacting Concrete | Rp 1.250.000 |
| FC | Fiber Reinforced Concrete | Rp 1.420.000 |

### Pesanan Demo
- **BK-2025-001** — PT Bangun Jaya Abadi (K-300, 120 m³) — `dalam_pengiriman`
- **BK-2025-002** — CV Mitra Konstruksi (K-200, 45 m³) — `selesai`
- **BK-2025-003** — Bapak Hendra Wijaya (K-225, 15 m³) — `menunggu_konfirmasi`

---

## 🔮 Pengembangan Lanjut

Beberapa fitur yang bisa dikembangkan:

- **Database Real** — Ganti JSON lokal dengan PostgreSQL/MongoDB
- **Autentikasi** — Tambahkan login pelanggan dengan JWT
- **Webhook WhatsApp** — Integrasikan dengan WhatsApp Business API
- **Dashboard Admin** — Halaman admin untuk melihat semua pesanan & keluhan
- **Redis Sessions** — Ganti in-memory sessions dengan Redis untuk produksi
- **Rate Limiting** — Tambahkan rate limit pada API endpoint
- **Streaming Response** — Implementasi SSE untuk respons AI real-time (stream)
- **Voice Input** — Integrasi Whisper API untuk input suara

---

## 📄 Lisensi

Proyek ini dibuat sebagai contoh/demo aplikasi AI Customer Service. Bebas digunakan dan dimodifikasi untuk keperluan belajar.

---

<div align="center">
  <strong>BetonKu AI Assistant</strong> — Dibangun dengan ❤️ menggunakan FastAPI + OpenAI
</div>
