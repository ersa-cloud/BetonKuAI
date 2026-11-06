"""
BetonKu AI Assistant - Tool Functions for AI Function Calling
Definisi fungsi-fungsi yang dapat dipanggil oleh AI Agent melalui Function Calling.
"""

import math
from typing import Any
from app.data_manager import (
    get_all_products,
    get_product_by_id,
    get_additional_services,
    get_price_notes,
    get_company_info,
    get_company_faqs,
    get_delivery_info,
    get_payment_info,
    get_order_by_id,
    create_order,
    create_complaint,
)


# ═══════════════════════════════════════════════════════════════════════════════
# DEFINISI TOOLS UNTUK OPENAI FUNCTION CALLING
# ═══════════════════════════════════════════════════════════════════════════════

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_product_catalog",
            "description": (
                "Mengambil katalog lengkap semua produk beton ready-mix BetonKu beserta harga terbaru. "
                "Panggil fungsi ini ketika pelanggan bertanya tentang produk, jenis beton, daftar harga, "
                "atau ingin membandingkan spesifikasi antar produk."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_availability": {
                        "type": "string",
                        "description": "Filter berdasarkan ketersediaan: 'tersedia', 'indent', atau 'semua' (default).",
                        "enum": ["tersedia", "indent", "semua"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_detail",
            "description": (
                "Mengambil detail spesifik satu produk beton berdasarkan ID produk. "
                "Panggil ini ketika pelanggan menanyakan detail produk tertentu seperti K200, K300, SCC, dll."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "ID produk beton, contoh: 'K175', 'K200', 'K225', 'K250', 'K300', 'K350', 'K400', 'SCC', 'FC'"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_concrete_volume",
            "description": (
                "Menghitung kebutuhan volume beton berdasarkan dimensi elemen struktur proyek. "
                "Panggil fungsi ini ketika pelanggan ingin menghitung kebutuhan beton untuk "
                "pondasi, kolom, balok, plat lantai, jalan, atau elemen lainnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "element_type": {
                        "type": "string",
                        "description": "Tipe elemen struktur: 'balok_lantai', 'kolom', 'pondasi_telapak', 'pondasi_bored_pile', 'plat_lantai', 'jalan', 'dinding', 'custom'",
                        "enum": ["balok_lantai", "kolom", "pondasi_telapak", "pondasi_bored_pile", "plat_lantai", "jalan", "dinding", "custom"]
                    },
                    "dimensions": {
                        "type": "object",
                        "description": (
                            "Dimensi elemen dalam meter. "
                            "Untuk balok/lantai/jalan/dinding: {'panjang': float, 'lebar': float, 'tebal_atau_tinggi': float}. "
                            "Untuk kolom: {'lebar': float, 'tebal': float, 'tinggi': float}. "
                            "Untuk pondasi telapak: {'panjang': float, 'lebar': float, 'tebal': float}. "
                            "Untuk bored pile: {'diameter': float, 'kedalaman': float}. "
                            "Untuk custom: {'volume_m3': float} (input langsung volume)."
                        ),
                        "properties": {
                            "panjang": {"type": "number"},
                            "lebar": {"type": "number"},
                            "tebal_atau_tinggi": {"type": "number"},
                            "tebal": {"type": "number"},
                            "tinggi": {"type": "number"},
                            "diameter": {"type": "number"},
                            "kedalaman": {"type": "number"},
                            "volume_m3": {"type": "number"}
                        }
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Jumlah elemen yang sama (default: 1)"
                    },
                    "waste_factor_percent": {
                        "type": "number",
                        "description": "Faktor tambahan untuk waste/susut dalam persen (default: 5%)"
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Opsional: ID produk beton untuk menghitung estimasi biaya sekaligus (contoh: 'K250')"
                    }
                },
                "required": ["element_type", "dimensions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_information",
            "description": (
                "Mengambil informasi lengkap tentang perusahaan BetonKu: profil, kontak, lokasi batching plant, "
                "sertifikasi, kapasitas produksi, area layanan, FAQ, info pengiriman, dan syarat pembayaran. "
                "Panggil ini untuk pertanyaan umum tentang perusahaan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Jenis informasi: 'profil', 'kontak', 'pengiriman', 'pembayaran', 'faq', 'semua'",
                        "enum": ["profil", "kontak", "pengiriman", "pembayaran", "faq", "semua"]
                    }
                },
                "required": ["info_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_order_request",
            "description": (
                "Membuat permintaan pesanan beton baru dan menyimpannya ke sistem. "
                "Panggil fungsi ini HANYA ketika pelanggan sudah memberikan semua informasi yang diperlukan "
                "dan secara eksplisit meminta untuk membuat pesanan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Nama perusahaan atau pelanggan"},
                    "contact_person": {"type": "string", "description": "Nama orang yang dapat dihubungi"},
                    "phone": {"type": "string", "description": "Nomor telepon/WhatsApp aktif"},
                    "email": {"type": "string", "description": "Alamat email aktif"},
                    "project_name": {"type": "string", "description": "Nama proyek konstruksi"},
                    "project_address": {"type": "string", "description": "Alamat lokasi proyek secara lengkap"},
                    "product_id": {"type": "string", "description": "ID produk beton yang dipesan (contoh: K300)"},
                    "volume_m3": {"type": "number", "description": "Volume beton yang dibutuhkan dalam m³"},
                    "delivery_date": {"type": "string", "description": "Tanggal pengiriman yang diinginkan (format: YYYY-MM-DD)"},
                    "notes": {"type": "string", "description": "Catatan tambahan untuk pesanan (opsional)"}
                },
                "required": ["customer_name", "contact_person", "phone", "email",
                             "project_name", "project_address", "product_id", "volume_m3", "delivery_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": (
                "Memeriksa status pesanan berdasarkan nomor order ID. "
                "Panggil ini ketika pelanggan ingin mengetahui status pesanannya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Nomor ID pesanan, contoh: 'BK-2025-001'"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_complaint",
            "description": (
                "Mencatat dan mengirimkan keluhan pelanggan ke sistem. "
                "Panggil ini ketika pelanggan ingin melaporkan keluhan terkait kualitas produk, "
                "pengiriman, layanan, atau masalah lainnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Nama perusahaan atau pelanggan"},
                    "contact_person": {"type": "string", "description": "Nama orang yang dapat dihubungi"},
                    "phone": {"type": "string", "description": "Nomor telepon aktif"},
                    "email": {"type": "string", "description": "Alamat email"},
                    "category": {
                        "type": "string",
                        "description": "Kategori keluhan",
                        "enum": ["kualitas", "pengiriman", "administrasi", "layanan", "lainnya"]
                    },
                    "subject": {"type": "string", "description": "Judul singkat keluhan"},
                    "description": {"type": "string", "description": "Deskripsi lengkap keluhan"},
                    "related_order_id": {"type": "string", "description": "Nomor order terkait (opsional, contoh: BK-2025-001)"}
                },
                "required": ["customer_name", "contact_person", "phone", "email",
                             "category", "subject", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_admin_handoff",
            "description": (
                "Meminta pengalihan percakapan kepada admin/sales BetonKu secara langsung. "
                "Panggil ini ketika: pelanggan secara eksplisit meminta berbicara dengan admin/manusia, "
                "pertanyaan terlalu kompleks dan membutuhkan negosiasi harga, atau ada masalah mendesak "
                "yang tidak dapat ditangani oleh AI."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Alasan pengalihan ke admin"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Nama pelanggan (jika sudah diketahui)"
                    },
                    "urgency": {
                        "type": "string",
                        "description": "Tingkat urgensi: 'normal', 'segera', 'darurat'",
                        "enum": ["normal", "segera", "darurat"]
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# IMPLEMENTASI HANDLER SETIAP TOOL
# ═══════════════════════════════════════════════════════════════════════════════

def handle_get_product_catalog(filter_availability: str = "semua") -> dict:
    """Handler: Mengambil katalog produk, bisa difilter berdasarkan ketersediaan."""
    products = get_all_products()
    services = get_additional_services()
    notes = get_price_notes()

    if filter_availability != "semua":
        products = [p for p in products if p.get("availability") == filter_availability]

    return {
        "status": "success",
        "products": products,
        "additional_services": services,
        "price_notes": notes,
        "total_products": len(products)
    }


def handle_get_product_detail(product_id: str) -> dict:
    """Handler: Mengambil detail satu produk berdasarkan ID."""
    product = get_product_by_id(product_id)
    if not product:
        return {
            "status": "not_found",
            "message": f"Produk dengan ID '{product_id}' tidak ditemukan.",
            "suggestion": "ID produk yang tersedia: K175, K200, K225, K250, K300, K350, K400, SCC, FC"
        }
    return {"status": "success", "product": product}


def handle_calculate_concrete_volume(
    element_type: str,
    dimensions: dict,
    quantity: int = 1,
    waste_factor_percent: float = 5.0,
    product_id: str = None
) -> dict:
    """
    Handler: Menghitung volume beton berdasarkan tipe elemen dan dimensinya.
    Mengembalikan volume bersih, volume dengan waste, dan estimasi biaya jika product_id diberikan.
    """
    volume_per_unit = 0.0
    calculation_detail = ""

    try:
        if element_type == "balok_lantai":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get("tebal_atau_tinggi", dimensions.get("tebal", 0))
            volume_per_unit = p * l * t
            calculation_detail = f"Balok/Lantai: {p}m × {l}m × {t}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "kolom":
            l = dimensions["lebar"]
            t = dimensions.get("tebal", dimensions.get("lebar", 0))
            h = dimensions.get("tinggi", dimensions.get("tebal_atau_tinggi", 0))
            volume_per_unit = l * t * h
            calculation_detail = f"Kolom: {l}m × {t}m × {h}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "pondasi_telapak":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get("tebal", dimensions.get("tebal_atau_tinggi", 0))
            volume_per_unit = p * l * t
            calculation_detail = f"Pondasi Telapak: {p}m × {l}m × {t}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "pondasi_bored_pile":
            d = dimensions["diameter"]
            k = dimensions["kedalaman"]
            radius = d / 2
            volume_per_unit = math.pi * (radius ** 2) * k
            calculation_detail = f"Bored Pile: π × (Ø{d}m/2)² × {k}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "plat_lantai":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get("tebal_atau_tinggi", dimensions.get("tebal", 0))
            volume_per_unit = p * l * t
            calculation_detail = f"Plat Lantai: {p}m × {l}m × {t}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "jalan":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get("tebal_atau_tinggi", dimensions.get("tebal", 0))
            volume_per_unit = p * l * t
            calculation_detail = f"Jalan Beton: {p}m × {l}m × {t}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "dinding":
            p = dimensions["panjang"]
            t = dimensions.get("tebal_atau_tinggi", dimensions.get("tebal", 0))
            h = dimensions.get("tinggi", 0)
            volume_per_unit = p * t * h
            calculation_detail = f"Dinding: {p}m × {t}m × {h}m = {volume_per_unit:.3f} m³/unit"

        elif element_type == "custom":
            volume_per_unit = dimensions.get("volume_m3", 0)
            calculation_detail = f"Custom: volume langsung = {volume_per_unit:.3f} m³/unit"

        else:
            return {"status": "error", "message": f"Tipe elemen '{element_type}' tidak dikenali."}

    except KeyError as e:
        return {
            "status": "error",
            "message": f"Dimensi yang diperlukan tidak lengkap: {str(e)}. "
                       f"Pastikan semua dimensi dalam meter sudah diisi."
        }

    # Hitung total volume
    volume_net = volume_per_unit * quantity
    waste_factor = waste_factor_percent / 100
    volume_with_waste = volume_net * (1 + waste_factor)
    # Pembulatan ke atas ke kelipatan 0.5 m³
    volume_ordered = math.ceil(volume_with_waste * 2) / 2

    result: dict[str, Any] = {
        "status": "success",
        "element_type": element_type,
        "calculation_detail": calculation_detail,
        "quantity": quantity,
        "volume_per_unit_m3": round(volume_per_unit, 3),
        "volume_net_m3": round(volume_net, 3),
        "waste_factor_percent": waste_factor_percent,
        "volume_with_waste_m3": round(volume_with_waste, 3),
        "volume_recommended_order_m3": volume_ordered,
        "recommendation": (
            f"Disarankan memesan {volume_ordered} m³ "
            f"(sudah termasuk waste {waste_factor_percent}% dan dibulatkan ke atas)"
        )
    }

    # Tambahkan estimasi biaya jika product_id diberikan
    if product_id:
        product = get_product_by_id(product_id)
        if product:
            estimated_cost = volume_ordered * product["price_per_m3"]
            result["cost_estimation"] = {
                "product": product["name"],
                "price_per_m3": product["price_per_m3"],
                "volume_m3": volume_ordered,
                "subtotal": estimated_cost,
                "ppn_11_percent": estimated_cost * 0.11,
                "total_with_ppn": estimated_cost * 1.11,
                "down_payment_30_percent": estimated_cost * 0.30,
                "note": "Harga belum termasuk biaya pengiriman di luar radius 30 km dan jasa pompa beton"
            }

    return result


def handle_get_company_information(info_type: str = "semua") -> dict:
    """Handler: Mengambil informasi perusahaan sesuai tipe yang diminta."""
    result: dict[str, Any] = {"status": "success", "info_type": info_type}

    if info_type in ("profil", "semua"):
        result["company_profile"] = get_company_info()
    if info_type in ("kontak", "semua"):
        company = get_company_info()
        result["contact"] = {
            "phone": company["phone"],
            "whatsapp": company["whatsapp"],
            "email": company["email"],
            "address": company["address"],
            "operational_hours": company["operational_hours"]
        }
    if info_type in ("pengiriman", "semua"):
        result["delivery_info"] = get_delivery_info()
    if info_type in ("pembayaran", "semua"):
        result["payment_info"] = get_payment_info()
    if info_type in ("faq", "semua"):
        result["faqs"] = get_company_faqs()

    return result


def handle_create_order_request(
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
    """Handler: Membuat pesanan baru."""
    try:
        order = create_order(
            customer_name=customer_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            project_name=project_name,
            project_address=project_address,
            product_id=product_id,
            volume_m3=volume_m3,
            delivery_date=delivery_date,
            notes=notes
        )
        return {
            "status": "success",
            "message": "Pesanan berhasil dibuat dan menunggu konfirmasi pembayaran DP.",
            "order": order,
            "next_steps": [
                f"Lakukan pembayaran DP sebesar Rp {order['down_payment']:,.0f} (30% dari total)",
                "Kirim bukti transfer ke WhatsApp kami: +62 812-9000-5678",
                f"Pesanan akan dikonfirmasi dalam 1x24 jam setelah pembayaran diterima",
                f"Nomor pesanan Anda: {order['order_id']}"
            ]
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Gagal membuat pesanan: {str(e)}"}


def handle_check_order_status(order_id: str) -> dict:
    """Handler: Mengecek status pesanan berdasarkan order ID."""
    order = get_order_by_id(order_id)
    if not order:
        return {
            "status": "not_found",
            "message": f"Pesanan dengan ID '{order_id}' tidak ditemukan.",
            "suggestion": "Pastikan nomor pesanan benar. Format: BK-YYYY-NNN (contoh: BK-2025-001)"
        }

    status_labels = {
        "menunggu_konfirmasi": "⏳ Menunggu Konfirmasi Pembayaran",
        "dikonfirmasi": "✅ Pesanan Dikonfirmasi",
        "dalam_pengiriman": "🚚 Dalam Pengiriman",
        "selesai": "✔️ Selesai",
        "dibatalkan": "❌ Dibatalkan"
    }

    return {
        "status": "success",
        "order_id": order["order_id"],
        "status_label": status_labels.get(order["status"], order["status"]),
        "order_details": order
    }


def handle_submit_complaint(
    customer_name: str,
    contact_person: str,
    phone: str,
    email: str,
    category: str,
    subject: str,
    description: str,
    related_order_id: str = ""
) -> dict:
    """Handler: Mencatat keluhan pelanggan baru."""
    try:
        complaint = create_complaint(
            customer_name=customer_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            category=category,
            subject=subject,
            description=description,
            related_order_id=related_order_id
        )
        return {
            "status": "success",
            "message": "Keluhan Anda telah berhasil dicatat dan akan segera ditangani oleh tim kami.",
            "complaint": complaint,
            "next_steps": [
                f"Nomor tiket keluhan Anda: {complaint['complaint_id']}",
                "Tim kami akan menghubungi Anda dalam 1x24 jam kerja",
                "Anda dapat memantau status keluhan dengan nomor tiket di atas",
                "Untuk keluhan mendesak, hubungi kami di: +62 21 8900-1234"
            ]
        }
    except Exception as e:
        return {"status": "error", "message": f"Gagal mencatat keluhan: {str(e)}"}


def handle_request_admin_handoff(
    reason: str,
    customer_name: str = "Pelanggan",
    urgency: str = "normal"
) -> dict:
    """Handler: Memproses permintaan pengalihan ke admin."""
    urgency_messages = {
        "normal": "Permintaan Anda telah dicatat. Admin kami akan segera menghubungi Anda.",
        "segera": "Permintaan Anda ditandai sebagai SEGERA. Admin kami akan menghubungi Anda dalam waktu dekat.",
        "darurat": "🚨 Permintaan DARURAT diterima! Admin kami akan segera menghubungi Anda sekarang."
    }

    return {
        "status": "success",
        "handoff_requested": True,
        "urgency": urgency,
        "message": urgency_messages.get(urgency, urgency_messages["normal"]),
        "contact_options": {
            "whatsapp": "+62 812-9000-5678",
            "phone": "+62 21 8900-1234",
            "email": "info@betonku.co.id",
            "operational_hours": "Senin - Sabtu: 07.00 - 17.00 WIB"
        },
        "reason_recorded": reason
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCHER: Memetakan nama fungsi ke handler yang sesuai
# ═══════════════════════════════════════════════════════════════════════════════

def dispatch_tool_call(function_name: str, arguments: dict) -> dict:
    """
    Dispatcher utama untuk menjalankan tool yang dipanggil oleh AI.
    Menerima nama fungsi dan argumen, mengembalikan hasil eksekusi.
    """
    handlers = {
        "get_product_catalog": handle_get_product_catalog,
        "get_product_detail": handle_get_product_detail,
        "calculate_concrete_volume": handle_calculate_concrete_volume,
        "get_company_information": handle_get_company_information,
        "create_order_request": handle_create_order_request,
        "check_order_status": handle_check_order_status,
        "submit_complaint": handle_submit_complaint,
        "request_admin_handoff": handle_request_admin_handoff,
    }

    handler = handlers.get(function_name)
    if not handler:
        return {"status": "error", "message": f"Fungsi '{function_name}' tidak dikenali."}

    try:
        return handler(**arguments)
    except TypeError as e:
        return {"status": "error", "message": f"Argumen tidak valid untuk '{function_name}': {str(e)}"}
