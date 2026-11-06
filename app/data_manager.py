
"""
BetonKu AI Assistant - Data Manager
Mengelola pembacaan data JSON dan simulasi transaksi.

Mode deployment:
- Data produk dan perusahaan dibaca dari file JSON.
- Data pesanan dan keluhan contoh dibaca dari file JSON.
- Pembuatan pesanan hanya berupa simulasi.
- Pembuatan keluhan hanya berupa simulasi.
- Tidak ada penulisan data ke file JSON.

Dirancang untuk deployment Vercel tanpa database.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid


# ============================================================
# PATH CONFIGURATION
# ============================================================

# app/data_manager.py berada di dalam folder app/.
# Parent dari parent(__file__) adalah root proyek.
DATA_DIR = Path(__file__).parent.parent.resolve() / "data"


# ============================================================
# JSON DATA READER
# ============================================================

def _load_json(filename: str) -> dict:
    """
    Membaca file JSON dari direktori data.

    File JSON hanya digunakan sebagai sumber data statis.
    Tidak ada proses penulisan pada file tersebut.
    """

    filepath = DATA_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"File data '{filename}' tidak ditemukan."
        )

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Format JSON pada '{filename}' tidak valid."
        ) from error


# ============================================================
# PRODUCT DATA
# ============================================================

def get_all_products() -> list[dict]:
    """Mengambil seluruh data produk beton."""

    data = _load_json("products.json")
    return data.get("products", [])


def get_product_by_id(product_id: str) -> dict | None:
    """Mengambil produk berdasarkan ID, misalnya K200 atau K300."""

    products = get_all_products()
    product_id_upper = product_id.strip().upper()

    for product in products:
        if product["id"].upper() == product_id_upper:
            return product

    return None


def get_additional_services() -> list[dict]:
    """Mengambil daftar layanan tambahan."""

    data = _load_json("products.json")
    return data.get("additional_services", [])


def get_price_notes() -> list[str]:
    """Mengambil catatan harga produk."""

    data = _load_json("products.json")
    return data.get("price_notes", [])


# ============================================================
# COMPANY DATA
# ============================================================

def get_company_info() -> dict:
    """Mengambil informasi perusahaan BetonKu."""

    data = _load_json("company_info.json")
    return data.get("company", {})


def get_company_faqs() -> list[dict]:
    """Mengambil daftar FAQ perusahaan."""

    data = _load_json("company_info.json")
    return data.get("faqs", [])


def get_delivery_info() -> dict:
    """Mengambil informasi pengiriman."""

    data = _load_json("company_info.json")
    return data.get("delivery_info", {})


def get_payment_info() -> dict:
    """Mengambil informasi ketentuan pembayaran."""

    data = _load_json("company_info.json")
    return data.get("payment_terms", {})


# ============================================================
# ORDER DATA - READ ONLY
# ============================================================

def get_order_by_id(order_id: str) -> dict | None:
    """
    Mencari pesanan berdasarkan ID.

    Pencarian hanya dilakukan pada data pesanan contoh
    yang tersimpan di orders.json.
    """

    data = _load_json("orders.json")
    order_id_upper = order_id.strip().upper()

    for order in data.get("orders", []):
        if order["order_id"].upper() == order_id_upper:
            return order

    return None


# ============================================================
# ORDER CREATION - SIMULATION
# ============================================================

def create_order(
    customer_name: str,
    contact_person: str,
    phone: str,
    email: str,
    project_name: str,
    project_address: str,
    product_id: str,
    volume_m3: float,
    delivery_date: str,
    notes: str = ""
) -> dict:
    """
    Membuat simulasi pesanan beton.

    Pesanan tidak disimpan ke file JSON atau database.
    Data hanya dikembalikan sebagai hasil simulasi.
    """

    # Validasi produk
    product = get_product_by_id(product_id)

    if not product:
        raise ValueError(
            f"Produk dengan ID '{product_id}' tidak ditemukan."
        )

    if product.get("availability") == "indent":
        raise ValueError(
            f"Produk {product['name']} berstatus indent. "
            "Hubungi tim penjualan untuk konfirmasi ketersediaan."
        )

    # Validasi volume
    if volume_m3 <= 0:
        raise ValueError("Volume beton harus lebih besar dari 0.")

    # Generate ID simulasi unik
    order_id = (
        f"SIM-BK-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    # Perhitungan harga
    price_per_m3 = product["price_per_m3"]
    total_price = price_per_m3 * volume_m3
    down_payment = total_price * 0.30

    # Membuat objek pesanan simulasi
    new_order: dict[str, Any] = {
        "order_id": order_id,
        "customer_name": customer_name,
        "contact_person": contact_person,
        "phone": phone,
        "email": email,
        "project_name": project_name,
        "project_address": project_address,
        "product_id": product["id"],
        "product_name": product["name"],
        "volume_m3": volume_m3,
        "price_per_m3": price_per_m3,
        "total_price": total_price,
        "down_payment": down_payment,
        "status": "simulasi_menunggu_konfirmasi",
        "order_date": datetime.now().strftime("%Y-%m-%d"),
        "delivery_date": delivery_date,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
        "simulation": True,
        "saved_permanently": False,
        "message": (
            "Pesanan ini hanya simulasi untuk demonstrasi. "
            "Data tidak disimpan secara permanen."
        )
    }

    return new_order


# ============================================================
# COMPLAINT DATA - READ ONLY
# ============================================================

def get_complaint_by_id(complaint_id: str) -> dict | None:
    """
    Mencari keluhan berdasarkan ID.

    Pencarian hanya dilakukan pada data keluhan contoh
    yang tersimpan di complaints.json.
    """

    data = _load_json("complaints.json")
    complaint_id_upper = complaint_id.strip().upper()

    for complaint in data.get("complaints", []):
        if complaint["complaint_id"].upper() == complaint_id_upper:
            return complaint

    return None


# ============================================================
# COMPLAINT CREATION - SIMULATION
# ============================================================

def create_complaint(
    customer_name: str,
    contact_person: str,
    phone: str,
    email: str,
    category: str,
    subject: str,
    description: str,
    related_order_id: str = ""
) -> dict:
    """
    Membuat simulasi pengaduan pelanggan.

    Pengaduan tidak disimpan ke file JSON atau database.
    Data hanya dikembalikan sebagai hasil simulasi.
    """

    data = _load_json("complaints.json")

    # Validasi kategori
    valid_categories = list(
        data.get("complaint_categories", {}).keys()
    )

    if category not in valid_categories:
        category = "lainnya"

    # Generate ID simulasi unik
    complaint_id = (
        f"SIM-KL-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    # Membuat objek keluhan simulasi
    new_complaint: dict[str, Any] = {
        "complaint_id": complaint_id,
        "customer_name": customer_name,
        "contact_person": contact_person,
        "phone": phone,
        "email": email,
        "related_order_id": related_order_id,
        "category": category,
        "subject": subject,
        "description": description,
        "priority": "sedang",
        "status": "simulasi_diterima",
        "assigned_to": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "resolution": None,
        "simulation": True,
        "saved_permanently": False,
        "message": (
            "Pengaduan ini hanya simulasi untuk demonstrasi. "
            "Data tidak disimpan secara permanen."
        )
    }

    return new_complaint
