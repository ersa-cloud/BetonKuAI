
"""
BetonKu AI Assistant - Tool Functions for AI Function Calling

Definisi fungsi-fungsi yang dapat dipanggil oleh AI Agent
melalui OpenAI-compatible Function Calling.

Mode deployment:
- Membaca data produk dan perusahaan dari JSON.
- Membaca data pesanan dan keluhan contoh dari JSON.
- Pembuatan pesanan hanya berupa simulasi.
- Pembuatan keluhan hanya berupa simulasi.
- Tidak ada penyimpanan transaksi permanen.
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


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS_DEFINITION = [

    # --------------------------------------------------------
    # 1. GET PRODUCT CATALOG
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_product_catalog",
            "description": (
                "Mengambil katalog lengkap semua produk beton ready-mix BetonKu "
                "beserta harga dan spesifikasinya. "
                "Panggil fungsi ini ketika pelanggan bertanya tentang produk, "
                "jenis beton, daftar harga, atau ingin membandingkan produk."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_availability": {
                        "type": "string",
                        "description": (
                            "Filter ketersediaan produk: "
                            "'tersedia', 'indent', atau 'semua'."
                        ),
                        "enum": ["tersedia", "indent", "semua"]
                    }
                },
                "required": []
            }
        }
    },

    # --------------------------------------------------------
    # 2. GET PRODUCT DETAIL
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_product_detail",
            "description": (
                "Mengambil detail spesifik satu produk beton berdasarkan ID. "
                "Panggil ketika pelanggan menanyakan spesifikasi produk tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": (
                            "ID produk beton, contoh: K175, K200, K225, "
                            "K250, K300, K350, K400, SCC, atau FC."
                        )
                    }
                },
                "required": ["product_id"]
            }
        }
    },

    # --------------------------------------------------------
    # 3. CALCULATE CONCRETE VOLUME
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "calculate_concrete_volume",
            "description": (
                "Menghitung kebutuhan volume beton berdasarkan dimensi "
                "elemen struktur proyek seperti pondasi, kolom, balok, "
                "plat lantai, jalan, dan dinding."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "element_type": {
                        "type": "string",
                        "description": "Jenis elemen struktur.",
                        "enum": [
                            "balok_lantai",
                            "kolom",
                            "pondasi_telapak",
                            "pondasi_bored_pile",
                            "plat_lantai",
                            "jalan",
                            "dinding",
                            "custom"
                        ]
                    },
                    "dimensions": {
                        "type": "object",
                        "description": (
                            "Dimensi dalam meter. "
                            "Untuk balok, plat, jalan: panjang, lebar, tebal_atau_tinggi. "
                            "Untuk kolom: lebar, tebal, tinggi. "
                            "Untuk pondasi telapak: panjang, lebar, tebal. "
                            "Untuk bored pile: diameter, kedalaman. "
                            "Untuk custom: volume_m3."
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
                        "description": "Jumlah elemen yang sama. Default 1."
                    },
                    "waste_factor_percent": {
                        "type": "number",
                        "description": "Persentase tambahan waste. Default 5%."
                    },
                    "product_id": {
                        "type": "string",
                        "description": (
                            "Opsional: ID produk beton untuk menghitung "
                            "estimasi biaya, misalnya K250."
                        )
                    }
                },
                "required": ["element_type", "dimensions"]
            }
        }
    },

    # --------------------------------------------------------
    # 4. GET COMPANY INFORMATION
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_company_information",
            "description": (
                "Mengambil informasi perusahaan BetonKu seperti profil, "
                "kontak, lokasi, kapasitas produksi, area layanan, FAQ, "
                "informasi pengiriman, dan ketentuan pembayaran."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Jenis informasi yang dibutuhkan.",
                        "enum": [
                            "profil",
                            "kontak",
                            "pengiriman",
                            "pembayaran",
                            "faq",
                            "semua"
                        ]
                    }
                },
                "required": ["info_type"]
            }
        }
    },

    # --------------------------------------------------------
    # 5. CREATE ORDER REQUEST - SIMULATION
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "create_order_request",
            "description": (
                "Membuat SIMULASI permintaan pesanan beton. "
                "Panggil hanya ketika pelanggan sudah memberikan semua "
                "informasi yang diperlukan dan secara eksplisit meminta "
                "untuk membuat pesanan. "
                "Pesanan hanya untuk demonstrasi dan TIDAK disimpan permanen. "
                "Jangan menyebut pesanan sebagai transaksi resmi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Nama perusahaan atau pelanggan."
                    },
                    "contact_person": {
                        "type": "string",
                        "description": "Nama orang yang dapat dihubungi."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Nomor telepon atau WhatsApp."
                    },
                    "email": {
                        "type": "string",
                        "description": "Alamat email pelanggan."
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Nama proyek konstruksi."
                    },
                    "project_address": {
                        "type": "string",
                        "description": "Alamat lengkap lokasi proyek."
                    },
                    "product_id": {
                        "type": "string",
                        "description": "ID produk beton, contoh K300."
                    },
                    "volume_m3": {
                        "type": "number",
                        "description": "Volume beton dalam meter kubik."
                    },
                    "delivery_date": {
                        "type": "string",
                        "description": "Tanggal pengiriman format YYYY-MM-DD."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Catatan tambahan, opsional."
                    }
                },
                "required": [
                    "customer_name",
                    "contact_person",
                    "phone",
                    "email",
                    "project_name",
                    "project_address",
                    "product_id",
                    "volume_m3",
                    "delivery_date"
                ]
            }
        }
    },

    # --------------------------------------------------------
    # 6. CHECK ORDER STATUS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": (
                "Memeriksa status pesanan berdasarkan nomor order ID. "
                "Pencarian menggunakan data pesanan contoh yang tersedia."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "Nomor ID pesanan, contoh BK-2025-001."
                        )
                    }
                },
                "required": ["order_id"]
            }
        }
    },

    # --------------------------------------------------------
    # 7. SUBMIT COMPLAINT - SIMULATION
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "submit_complaint",
            "description": (
                "Membuat SIMULASI pengaduan pelanggan terkait kualitas "
                "produk, pengiriman, administrasi, layanan, atau masalah lainnya. "
                "Panggil ketika pelanggan ingin mencoba membuat pengaduan. "
                "Pengaduan hanya simulasi, tidak dikirim ke admin, "
                "dan tidak disimpan secara permanen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Nama perusahaan atau pelanggan."
                    },
                    "contact_person": {
                        "type": "string",
                        "description": "Nama orang yang dapat dihubungi."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Nomor telepon pelanggan."
                    },
                    "email": {
                        "type": "string",
                        "description": "Alamat email pelanggan."
                    },
                    "category": {
                        "type": "string",
                        "description": "Kategori keluhan.",
                        "enum": [
                            "kualitas",
                            "pengiriman",
                            "administrasi",
                            "layanan",
                            "lainnya"
                        ]
                    },
                    "subject": {
                        "type": "string",
                        "description": "Judul singkat keluhan."
                    },
                    "description": {
                        "type": "string",
                        "description": "Deskripsi lengkap keluhan."
                    },
                    "related_order_id": {
                        "type": "string",
                        "description": "Nomor pesanan terkait, opsional."
                    }
                },
                "required": [
                    "customer_name",
                    "contact_person",
                    "phone",
                    "email",
                    "category",
                    "subject",
                    "description"
                ]
            }
        }
    },

    # --------------------------------------------------------
    # 8. REQUEST ADMIN HANDOFF
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "request_admin_handoff",
            "description": (
                "Memberikan informasi kontak admin BetonKu ketika pelanggan "
                "meminta berbicara dengan manusia, membutuhkan negosiasi harga, "
                "atau memiliki masalah yang tidak dapat ditangani AI. "
                "Fungsi ini tidak mengirim notifikasi langsung kepada admin."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Alasan pengalihan ke admin."
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Nama pelanggan jika diketahui."
                    },
                    "urgency": {
                        "type": "string",
                        "description": "Tingkat urgensi.",
                        "enum": ["normal", "segera", "darurat"]
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


# ============================================================
# PRODUCT HANDLERS
# ============================================================

def handle_get_product_catalog(
    filter_availability: str = "semua"
) -> dict:
    """Mengambil katalog produk."""

    products = get_all_products()
    services = get_additional_services()
    notes = get_price_notes()

    if filter_availability != "semua":
        products = [
            product
            for product in products
            if product.get("availability") == filter_availability
        ]

    return {
        "status": "success",
        "products": products,
        "additional_services": services,
        "price_notes": notes,
        "total_products": len(products)
    }


def handle_get_product_detail(product_id: str) -> dict:
    """Mengambil detail produk."""

    product = get_product_by_id(product_id)

    if not product:
        return {
            "status": "not_found",
            "message": f"Produk dengan ID '{product_id}' tidak ditemukan.",
            "suggestion": (
                "Periksa kembali ID produk yang diminta pelanggan."
            )
        }

    return {
        "status": "success",
        "product": product
    }


# ============================================================
# CONCRETE VOLUME CALCULATOR
# ============================================================

def handle_calculate_concrete_volume(
    element_type: str,
    dimensions: dict,
    quantity: int = 1,
    waste_factor_percent: float = 5.0,
    product_id: str = None
) -> dict:
    """Menghitung kebutuhan volume beton dan estimasi biaya."""

    if quantity < 1:
        return {
            "status": "error",
            "message": "Jumlah elemen minimal 1."
        }

    if waste_factor_percent < 0:
        return {
            "status": "error",
            "message": "Persentase waste tidak boleh negatif."
        }

    volume_per_unit = 0.0
    calculation_detail = ""

    try:
        if element_type == "balok_lantai":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get(
                "tebal_atau_tinggi",
                dimensions.get("tebal", 0)
            )

            volume_per_unit = p * l * t
            calculation_detail = f"{p} × {l} × {t}"

        elif element_type == "kolom":
            l = dimensions["lebar"]
            t = dimensions.get("tebal", l)
            h = dimensions.get(
                "tinggi",
                dimensions.get("tebal_atau_tinggi", 0)
            )

            volume_per_unit = l * t * h
            calculation_detail = f"{l} × {t} × {h}"

        elif element_type == "pondasi_telapak":
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get(
                "tebal",
                dimensions.get("tebal_atau_tinggi", 0)
            )

            volume_per_unit = p * l * t
            calculation_detail = f"{p} × {l} × {t}"

        elif element_type == "pondasi_bored_pile":
            d = dimensions["diameter"]
            depth = dimensions["kedalaman"]

            volume_per_unit = math.pi * (d / 2) ** 2 * depth
            calculation_detail = (
                f"π × ({d}/2)² × {depth}"
            )

        elif element_type in ("plat_lantai", "jalan"):
            p = dimensions["panjang"]
            l = dimensions["lebar"]
            t = dimensions.get(
                "tebal_atau_tinggi",
                dimensions.get("tebal", 0)
            )

            volume_per_unit = p * l * t
            calculation_detail = f"{p} × {l} × {t}"

        elif element_type == "dinding":
            p = dimensions["panjang"]
            t = dimensions.get(
                "tebal_atau_tinggi",
                dimensions.get("tebal", 0)
            )
            h = dimensions["tinggi"]

            volume_per_unit = p * t * h
            calculation_detail = f"{p} × {t} × {h}"

        elif element_type == "custom":
            volume_per_unit = dimensions["volume_m3"]
            calculation_detail = (
                f"Volume langsung: {volume_per_unit} m³"
            )

        else:
            return {
                "status": "error",
                "message": "Jenis elemen struktur tidak dikenali."
            }

    except KeyError as error:
        return {
            "status": "error",
            "message": (
                f"Dimensi {error} belum diberikan. "
                "Lengkapi seluruh dimensi dalam satuan meter."
            )
        }

    if volume_per_unit <= 0:
        return {
            "status": "error",
            "message": "Dimensi harus menghasilkan volume lebih besar dari 0."
        }

    volume_net = volume_per_unit * quantity

    volume_with_waste = volume_net * (
        1 + waste_factor_percent / 100
    )

    # Pembulatan ke atas ke kelipatan 0,5 m³
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
            f"termasuk waste {waste_factor_percent}%."
        )
    }

    if product_id:
        product = get_product_by_id(product_id)

        if product:
            estimated_cost = (
                volume_ordered * product["price_per_m3"]
            )

            result["cost_estimation"] = {
                "product": product["name"],
                "price_per_m3": product["price_per_m3"],
                "volume_m3": volume_ordered,
                "subtotal": estimated_cost,
                "ppn_11_percent": estimated_cost * 0.11,
                "total_with_ppn": estimated_cost * 1.11,
                "down_payment_30_percent": estimated_cost * 0.30,
                "note": (
                    "Estimasi harga. Biaya tambahan pengiriman "
                    "dan jasa pompa dapat berlaku."
                )
            }

    return result


# ============================================================
# COMPANY INFORMATION HANDLER
# ============================================================

def handle_get_company_information(
    info_type: str = "semua"
) -> dict:
    """Mengambil informasi perusahaan."""

    result: dict[str, Any] = {
        "status": "success",
        "info_type": info_type
    }

    if info_type in ("profil", "semua"):
        result["company_profile"] = get_company_info()

    if info_type in ("kontak", "semua"):
        company = get_company_info()

        result["contact"] = {
            "phone": company.get("phone"),
            "whatsapp": company.get("whatsapp"),
            "email": company.get("email"),
            "address": company.get("address"),
            "operational_hours": company.get("operational_hours")
        }

    if info_type in ("pengiriman", "semua"):
        result["delivery_info"] = get_delivery_info()

    if info_type in ("pembayaran", "semua"):
        result["payment_info"] = get_payment_info()

    if info_type in ("faq", "semua"):
        result["faqs"] = get_company_faqs()

    return result


# ============================================================
# ORDER HANDLER - SIMULATION ONLY
# ============================================================

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
    """Membuat simulasi pesanan beton tanpa penyimpanan permanen."""

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
            "status": "simulation",
            "message": (
                "Simulasi pesanan berhasil dibuat. "
                "Pesanan ini hanya untuk demonstrasi, "
                "tidak disimpan secara permanen, dan belum menjadi transaksi resmi."
            ),
            "order": order,
            "next_steps": [
                f"Estimasi total harga: Rp {order['total_price']:,.0f}",
                f"Estimasi DP 30%: Rp {order['down_payment']:,.0f}",
                f"Nomor simulasi: {order['order_id']}",
                "Untuk pemesanan resmi, silakan hubungi admin BetonKu."
            ]
        }

    except ValueError as error:
        return {
            "status": "error",
            "message": str(error)
        }

    except Exception as error:
        print(f"[SIMULATION ORDER ERROR] {error}")

        return {
            "status": "error",
            "message": "Simulasi pesanan gagal diproses."
        }


# ============================================================
# ORDER STATUS HANDLER - SAMPLE DATA
# ============================================================

def handle_check_order_status(order_id: str) -> dict:
    """Memeriksa status pesanan contoh dari JSON."""

    order = get_order_by_id(order_id)

    if not order:
        return {
            "status": "not_found",
            "message": (
                f"Pesanan dengan ID '{order_id}' tidak ditemukan "
                "dalam data pesanan demonstrasi."
            ),
            "suggestion": (
                "Contoh nomor pesanan: BK-2025-001. "
                "Pengecekan hanya menggunakan data contoh."
            )
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
        "data_type": "sample",
        "order_id": order["order_id"],
        "status_label": status_labels.get(
            order["status"],
            order["status"]
        ),
        "order_details": order,
        "notice": (
            "Status ini berasal dari data pesanan contoh "
            "untuk demonstrasi, bukan data transaksi langsung."
        )
    }


# ============================================================
# COMPLAINT HANDLER - SIMULATION ONLY
# ============================================================

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
    """Membuat simulasi pengaduan tanpa penyimpanan permanen."""

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
            "status": "simulation",
            "message": (
                "Simulasi pengaduan berhasil dibuat. "
                "Pengaduan ini tidak dikirim ke admin "
                "dan tidak disimpan secara permanen."
            ),
            "complaint": complaint,
            "next_steps": [
                f"Nomor simulasi pengaduan: {complaint['complaint_id']}",
                "Untuk pengaduan resmi, silakan hubungi admin BetonKu."
            ]
        }

    except Exception as error:
        print(f"[SIMULATION COMPLAINT ERROR] {error}")

        return {
            "status": "error",
            "message": "Simulasi pengaduan gagal diproses."
        }


# ============================================================
# ADMIN HANDOFF HANDLER
# ============================================================

def handle_request_admin_handoff(
    reason: str,
    customer_name: str = "Pelanggan",
    urgency: str = "normal"
) -> dict:
    """Memberikan informasi kontak admin tanpa mengirim notifikasi."""

    urgency_messages = {
        "normal": (
            "Berikut informasi kontak admin BetonKu. "
            "Silakan hubungi admin secara langsung."
        ),
        "segera": (
            "Permintaan Anda membutuhkan penanganan segera. "
            "Silakan hubungi admin BetonKu secara langsung."
        ),
        "darurat": (
            "Permintaan Anda bersifat mendesak. "
            "Segera hubungi admin BetonKu melalui nomor berikut."
        )
    }

    company = get_company_info()

    return {
        "status": "information_only",
        "handoff_requested": False,
        "notification_sent": False,
        "urgency": urgency,
        "message": urgency_messages.get(
            urgency,
            urgency_messages["normal"]
        ),
        "contact_options": {
            "whatsapp": company.get("whatsapp"),
            "phone": company.get("phone"),
            "email": company.get("email"),
            "operational_hours": company.get("operational_hours")
        },
        "reason": reason,
        "customer_name": customer_name,
        "notice": (
            "Sistem demonstrasi ini tidak mengirim notifikasi "
            "atau meneruskan percakapan secara otomatis kepada admin."
        )
    }


# ============================================================
# TOOL DISPATCHER
# ============================================================

def dispatch_tool_call(
    function_name: str,
    arguments: dict
) -> dict:
    """Memetakan nama tool ke handler yang sesuai."""

    handlers = {
        "get_product_catalog": handle_get_product_catalog,
        "get_product_detail": handle_get_product_detail,
        "calculate_concrete_volume": handle_calculate_concrete_volume,
        "get_company_information": handle_get_company_information,
        "create_order_request": handle_create_order_request,
        "check_order_status": handle_check_order_status,
        "submit_complaint": handle_submit_complaint,
        "request_admin_handoff": handle_request_admin_handoff
    }

    handler = handlers.get(function_name)

    if not handler:
        return {
            "status": "error",
            "message": f"Fungsi '{function_name}' tidak dikenali."
        }

    try:
        return handler(**arguments)

    except TypeError as error:
        return {
            "status": "error",
            "message": (
                f"Argumen tidak valid untuk '{function_name}': {str(error)}"
            )
        }

    except Exception as error:
        print(f"[TOOL ERROR] {function_name}: {error}")

        return {
            "status": "error",
            "message": "Terjadi kesalahan saat menjalankan fungsi."
        }
