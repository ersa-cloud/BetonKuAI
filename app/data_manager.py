"""
BetonKu AI Assistant - Data Manager
Mengelola pembacaan dan penulisan data dari/ke file JSON lokal.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Path absolut ke direktori data — app/data_manager.py ada di dalam subfolder app/,
# jadi parent dari parent(__file__) = root proyek, lalu + "data"
DATA_DIR = Path(__file__).parent.parent.resolve() / "data"


def _load_json(filename: str) -> dict:
    """Membaca file JSON dari direktori data."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filename: str, data: dict) -> None:
    """Menyimpan data ke file JSON di direktori data."""
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Fungsi Data Produk ────────────────────────────────────────────────────────

def get_all_products() -> list[dict]:
    """Mengambil semua data produk beton."""
    data = _load_json("products.json")
    return data["products"]


def get_product_by_id(product_id: str) -> dict | None:
    """Mengambil produk berdasarkan ID (misal: K200, K300)."""
    products = get_all_products()
    product_id_upper = product_id.upper()
    for product in products:
        if product["id"].upper() == product_id_upper:
            return product
    return None


def get_additional_services() -> list[dict]:
    """Mengambil daftar layanan tambahan (pompa, uji kualitas, dll)."""
    data = _load_json("products.json")
    return data["additional_services"]


def get_price_notes() -> list[str]:
    """Mengambil catatan harga produk."""
    data = _load_json("products.json")
    return data["price_notes"]


# ─── Fungsi Data Perusahaan ────────────────────────────────────────────────────

def get_company_info() -> dict:
    """Mengambil informasi lengkap perusahaan BetonKu."""
    data = _load_json("company_info.json")
    return data["company"]


def get_company_faqs() -> list[dict]:
    """Mengambil daftar FAQ perusahaan."""
    data = _load_json("company_info.json")
    return data["faqs"]


def get_delivery_info() -> dict:
    """Mengambil informasi pengiriman."""
    data = _load_json("company_info.json")
    return data["delivery_info"]


def get_payment_info() -> dict:
    """Mengambil informasi pembayaran."""
    data = _load_json("company_info.json")
    return data["payment_terms"]


# ─── Fungsi Data Pesanan ───────────────────────────────────────────────────────

def get_order_by_id(order_id: str) -> dict | None:
    """Mencari pesanan berdasarkan order ID."""
    data = _load_json("orders.json")
    order_id_upper = order_id.upper()
    for order in data["orders"]:
        if order["order_id"].upper() == order_id_upper:
            return order
    return None


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
    Membuat pesanan beton baru dan menyimpannya ke JSON.
    Mengembalikan data pesanan yang baru dibuat.
    """
    data = _load_json("orders.json")

    # Cek apakah produk tersedia
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError(f"Produk dengan ID '{product_id}' tidak ditemukan.")
    if product["availability"] == "indent":
        raise ValueError(
            f"Produk {product['name']} berstatus indent. "
            "Hubungi tim penjualan kami untuk konfirmasi ketersediaan."
        )

    # Generate order ID baru
    data["last_order_number"] += 1
    year = datetime.now().year
    order_id = f"BK-{year}-{str(data['last_order_number']).zfill(3)}"

    # Hitung total harga
    price_per_m3 = product["price_per_m3"]
    total_price = price_per_m3 * volume_m3
    down_payment = total_price * 0.30  # DP 30%

    # Buat objek pesanan baru
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
        "status": "menunggu_konfirmasi",
        "order_date": datetime.now().strftime("%Y-%m-%d"),
        "delivery_date": delivery_date,
        "notes": notes,
        "created_at": datetime.now().isoformat() + "Z"
    }

    # Simpan ke file JSON
    data["orders"].append(new_order)
    _save_json("orders.json", data)

    return new_order


# ─── Fungsi Data Keluhan ───────────────────────────────────────────────────────

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
    Mencatat keluhan pelanggan baru ke file JSON.
    Mengembalikan data keluhan yang baru dibuat.
    """
    data = _load_json("complaints.json")

    # Validasi kategori
    valid_categories = list(data["complaint_categories"].keys())
    if category not in valid_categories:
        category = "lainnya"

    # Generate complaint ID baru
    data["last_complaint_number"] += 1
    year = datetime.now().year
    complaint_id = f"KL-{year}-{str(data['last_complaint_number']).zfill(3)}"

    # Buat objek keluhan baru
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
        "priority": "sedang",  # Default priority, akan dikaji oleh tim
        "status": "diterima",
        "assigned_to": None,
        "created_at": datetime.now().isoformat() + "Z",
        "updated_at": datetime.now().isoformat() + "Z",
        "resolution": None
    }

    # Simpan ke file JSON
    data["complaints"].append(new_complaint)
    _save_json("complaints.json", data)

    return new_complaint


def get_complaint_by_id(complaint_id: str) -> dict | None:
    """Mencari keluhan berdasarkan complaint ID."""
    data = _load_json("complaints.json")
    complaint_id_upper = complaint_id.upper()
    for complaint in data["complaints"]:
        if complaint["complaint_id"].upper() == complaint_id_upper:
            return complaint
    return None
