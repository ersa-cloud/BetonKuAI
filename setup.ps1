# ============================================================
# setup.ps1 — One-click setup script for BetonKu AI Assistant
# Run once: Right-click → "Run with PowerShell"
#           or in terminal: powershell -ExecutionPolicy Bypass -File setup.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  WARN  $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  ERROR  $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BetonKu AI Assistant — Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ── Step 1: Cek / Install Python ──────────────────────────────
Write-Step "Memeriksa instalasi Python..."

$pythonExe = $null

# Cari Python di lokasi umum
$candidates = @(
    "$projectRoot\venv\Scripts\python.exe",
    "C:\Python313\python.exe", "C:\Python312\python.exe",
    "C:\Python311\python.exe", "C:\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:USERPROFILE\miniforge3\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe",
    "$env:USERPROFILE\anaconda3\python.exe"
)

foreach ($c in $candidates) {
    if ((Test-Path $c) -and ($c -notlike "*venv*")) {
        $ver = & $c --version 2>&1
        if ($ver -match "Python 3") {
            $pythonExe = $c
            Write-Ok "Python ditemukan: $c ($ver)"
            break
        }
    }
}

if (-not $pythonExe) {
    # Coba install Python 3.13 via winget
    $winget = "$env:LOCALAPPDATA\Microsoft\WindowsApps\winget.exe"
    if (Test-Path $winget) {
        Write-Warn "Python tidak ditemukan. Menginstall Python 3.13 via winget..."
        Write-Host "  (Ini mungkin membutuhkan beberapa menit...)" -ForegroundColor Gray
        try {
            & $winget install --id Python.Python.3.13 --silent --accept-package-agreements --accept-source-agreements
            # Refresh PATH setelah instalasi
            $machinePath = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine')
            $userPath    = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
            $env:PATH    = $machinePath + ';' + $userPath
            # Cari lagi di lokasi default winget Python 3.13
            $searchPaths = @(
                'C:\Python313\python.exe',
                "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
            )
            foreach ($c in $searchPaths) {
                if (Test-Path $c) { $pythonExe = $c; break }
            }
            if (-not $pythonExe) {
                $fromPath = Get-Command python -ErrorAction SilentlyContinue
                if ($fromPath) { $pythonExe = $fromPath.Source }
            }
            if ($pythonExe) {
                Write-Ok "Python berhasil diinstall: $pythonExe"
            } else {
                Write-Fail "Python diinstall tapi tidak ditemukan. Restart PowerShell dan jalankan ulang setup.ps1."
                Write-Host "`nAtau install manual dari: https://www.python.org/downloads/" -ForegroundColor Yellow
                Read-Host "Tekan Enter untuk keluar"
                exit 1
            }
        } catch {
            Write-Fail "Gagal install Python via winget: $_"
            Write-Host "`nInstall manual dari: https://www.python.org/downloads/" -ForegroundColor Yellow
            Write-Host "Centang 'Add Python to PATH' saat instalasi!" -ForegroundColor Yellow
            Read-Host "Tekan Enter untuk keluar"
            exit 1
        }
    } else {
        Write-Fail "Python tidak ditemukan dan winget tidak tersedia."
        Write-Host "`nInstall Python manual dari: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Centang 'Add Python to PATH' saat instalasi!" -ForegroundColor Yellow
        Read-Host "Tekan Enter untuk keluar"
        exit 1
    }
}

# ── Step 2: Buat Virtual Environment ──────────────────────────
Write-Step "Membuat virtual environment..."

$venvPath = "$projectRoot\venv"
if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
    & $pythonExe -m venv $venvPath
    Write-Ok "Virtual environment dibuat di: $venvPath"
} else {
    Write-Ok "Virtual environment sudah ada: $venvPath"
}

$venvPython = "$venvPath\Scripts\python.exe"
$venvPip    = "$venvPath\Scripts\pip.exe"
$venvUvicorn = "$venvPath\Scripts\uvicorn.exe"

# ── Step 3: Upgrade pip ────────────────────────────────────────
Write-Step "Upgrade pip..."
& $venvPython -m pip install --upgrade pip --quiet
Write-Ok "pip diupgrade"

# ── Step 4: Install Python dependencies ───────────────────────
Write-Step "Menginstall Python dependencies dari requirements.txt..."
& $venvPip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Gagal install dependencies!"
    exit 1
}
Write-Ok "Semua Python dependencies terinstall"

# Verifikasi uvicorn
if (Test-Path $venvUvicorn) {
    Write-Ok "uvicorn tersedia di: $venvUvicorn"
} else {
    Write-Fail "uvicorn tidak ditemukan setelah instalasi!"
    exit 1
}

# ── Step 5: Buat file .env ─────────────────────────────────────
Write-Step "Memeriksa file .env..."
$envFile = "$projectRoot\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item "$projectRoot\.env.example" $envFile
    Write-Warn "File .env dibuat dari .env.example"
    Write-Warn "PENTING: Buka .env dan isi OPENAI_API_KEY dengan API key Anda!"
} else {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "sk-your") {
        Write-Warn "File .env ada tapi OPENAI_API_KEY belum diisi!"
        Write-Warn "Buka .env dan isi OPENAI_API_KEY dengan API key Anda."
    } else {
        Write-Ok "File .env sudah dikonfigurasi"
    }
}

# ── Step 6: Update tasks.json dengan path venv yang tepat ─────
Write-Step "Memperbarui .vscode/tasks.json dengan path venv..."
# tasks.json akan menggunakan path absolute venv — tidak perlu update manual

# ── Selesai ────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup Selesai!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Python  : $venvPython" -ForegroundColor White
Write-Host "uvicorn : $venvUvicorn" -ForegroundColor White
Write-Host ""
Write-Host "Langkah selanjutnya:" -ForegroundColor Yellow
Write-Host "  1. Buka file .env dan isi OPENAI_API_KEY" -ForegroundColor Yellow
Write-Host "  2. Tekan F5 / Run di VS Code untuk menjalankan aplikasi" -ForegroundColor Yellow
Write-Host "  3. Atau jalankan manual: python run.py" -ForegroundColor Yellow
Write-Host ""
Read-Host "Tekan Enter untuk keluar"
