from __future__ import annotations

import re

INDONESIAN_MARKERS = (
    "berapa",
    "tolong",
    "halo",
    "hai",
    "selamat",
    "bisa",
    "mohon",
    "jumlah",
    "total",
    "data",
    "nasabah",
    "deposito",
    "kredit",
    "makasih",
    "terima kasih",
    "selamat pagi",
    "selamat siang",
    "selamat sore",
    "selamat malam",
    "bantu saya",
    "bisa dibantu",
    "sampai jumpa",
    "selamat tinggal",
    "ya",
)

GREETING_PATTERNS = (
    r"^\s*(halo|hai|hi|hello)\b",
    r"^\s*selamat\s+(pagi|siang|sore|malam)\b",
    r"^\s*apa\s+kabar\b",
    r"^\s*(bisa bantu apa|siapa kamu)\b",
)

ACKNOWLEDGEMENT_PATTERNS = (
    r"^\s*(makasih|terima kasih|thanks|thank you)(\s+ya)?\s*$",
    r"^\s*(mantap|bagus|keren|sip|oke|ok|baik)(\s+banget)?\s*$",
)

FAREWELL_PATTERNS = (
    r"\b(sampai jumpa|dadah|bye|goodbye)\b",
    r"\b(selamat tinggal)\b",
)

DATA_DOMAIN_MARKERS = (
    "nasabah",
    "deposito",
    "deposit",
    "kredit",
    "credit",
    "loan",
    "pinjaman",
    "saldo",
    "balance",
    "outstanding",
    "principal",
    "collectibility",
    "segmen",
    "segment",
    "customer",
    "product",
    "produk",
    "branch",
    "cabang",
    "status",
    "maturity",
    "jatuh tempo",
    "kota",
    "city",
    "jumlah",
    "total",
    "berapa",
    "berapa banyak",
    "tren",
    "trend",
    "grafik",
    "chart",
    "linechart",
    "line chart",
    "bar chart",
    "pie chart",
    "visualisasi",
    "visualization",
    "per bulan",
    "bulanan",
    "tampilkan",
    "keluarkan",
    "keluarin",
    "keluar kan",
)

VISUALIZATION_FOLLOWUP_PATTERNS = (
    (r"\b(bar chart|barchart)\b", "bar"),
    (r"\b(line chart|linechart)\b", "line"),
    (r"\b(pie chart|piechart|donut chart|donutchart)\b", "pie"),
    (r"\b(table|tabel)\b", "table"),
)

VISUALIZATION_INTENT_PATTERNS = (
    r"\b(ubah|ganti|jadikan|dalam bentuk|tampilkan|show|render)\b",
    r"\b(chart|grafik|visualisasi|table|tabel)\b",
)


def is_indonesian_text(text: str) -> bool:
    lowered = normalize_text(text)
    return any(marker in lowered for marker in INDONESIAN_MARKERS)


def is_greeting_or_smalltalk(text: str) -> bool:
    lowered = normalize_text(text)
    return any(re.search(pattern, lowered) for pattern in GREETING_PATTERNS)


def is_acknowledgement(text: str) -> bool:
    lowered = normalize_text(text)
    return any(re.search(pattern, lowered) for pattern in ACKNOWLEDGEMENT_PATTERNS)


def is_farewell(text: str) -> bool:
    lowered = normalize_text(text)
    return any(re.search(pattern, lowered) for pattern in FAREWELL_PATTERNS)


def looks_like_data_request(text: str) -> bool:
    lowered = normalize_text(text)
    return any(marker in lowered for marker in DATA_DOMAIN_MARKERS)


def extract_visualization_preference(text: str) -> str | None:
    lowered = normalize_text(text)
    for pattern, preferred_type in VISUALIZATION_FOLLOWUP_PATTERNS:
        if re.search(pattern, lowered):
            return preferred_type
    return None


def is_visualization_followup(text: str) -> bool:
    lowered = normalize_text(text)
    preferred_type = extract_visualization_preference(lowered)
    if preferred_type is None:
        return False
    return any(re.search(pattern, lowered) for pattern in VISUALIZATION_INTENT_PATTERNS)


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[!?.,;:]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered)


def build_greeting_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Selamat datang. Saya Data Analyst Assistant Bank Jawa Timur, siap membantu Anda "
            "mengeksplorasi segmentasi nasabah, risiko dormant, rekomendasi kampanye, "
            "dan distribusi saldo dalam bahasa alami. Jika Anda perlu "
            "jawaban yang berasal dari dokumen atau SOP, aktifkan Knowledge Base "
            "melalui menu Settings.\n\n"
            "Kalau mau mulai, Anda bisa tanya hal seperti:\n"
            "1. Berapa jumlah nasabah di tiap segmen?\n"
            "2. Tampilkan distribusi nasabah berdasarkan dormant risk level\n"
            "3. Kampanye apa yang direkomendasikan untuk nasabah dormant risiko tinggi?\n"
            "4. Tampilkan rata-rata saldo deposito per customer segment"
        )

    return (
        "Hello, I am the Data Analyst Assistant for Bank Jawa Timur, "
        "ready to help you explore customer segmentation, dormancy risk, campaign recommendations, "
        "and balance analytics in natural language. "
        "If you need answers grounded in documents or SOPs, enable the Knowledge Base via Settings.\n\n"
        "You can start with questions like:\n"
        "1. How many customers are in each segment?\n"
        "2. Show distribution by dormant risk level\n"
        "3. What campaigns are recommended for high dormancy risk customers?\n"
        "4. Show average deposit balance by customer segment"
    )


def build_acknowledgement_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Sama-sama. Senang bisa membantu. Kalau Anda mau, lanjutkan saja "
            "dengan pertanyaan berikutnya tentang segmentasi nasabah, risiko dormant, kampanye, atau saldo."
        )

    return (
        "Glad to help. If you want, just continue with the next question about "
        "customer segmentation, dormancy risk, campaign recommendations, or balance analytics."
    )


def build_out_of_scope_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Saya paling cocok membantu pertanyaan yang berhubungan dengan segmentasi nasabah, "
            "risiko dormant, rekomendasi kampanye, dan distribusi saldo. "
            "Kalau yang Anda butuhkan berasal dari dokumen atau SOP, "
            "aktifkan Knowledge Base melalui menu Settings."
        )

    return (
        "I am best suited for customer segmentation, dormancy risk, campaign, and balance analytics questions. "
        "If you need answers from documents or SOPs, enable the Knowledge Base via Settings."
    )


def build_farewell_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Siap, sampai jumpa. Kalau nanti Anda ingin lanjut membaca data lagi, "
            "saya siap membantu."
        )

    return "See you. If you want to continue exploring the data later, I will be here to help."


def build_processing_fallback_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Maaf, saya belum bisa memproses pertanyaan itu dengan baik saat ini. "
            "Coba tuliskan pertanyaannya lebih spesifik, misalnya tentang distribusi segmen nasabah, "
            "tingkat risiko dormant, rekomendasi kampanye, saldo deposito, atau adopsi mobile banking. "
            "Jika pertanyaannya membutuhkan dokumen atau SOP, aktifkan Knowledge Base melalui menu Settings."
        )

    return (
        "I am sorry, I could not process that question cleanly just now. "
        "Please try asking in a more specific way, for example about customer segment distribution, "
        "dormancy risk levels, campaign recommendations, deposit balances, or mobile banking adoption. "
        "If the question depends on documents or SOPs, enable the Knowledge Base via Settings."
    )
