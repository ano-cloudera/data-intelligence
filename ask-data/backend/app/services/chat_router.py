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
            "Selamat datang. Saya Data Analyst Assistant, siap membantu Anda "
            "mengeksplorasi pertanyaan seputar credit risk, outstanding exposure, "
            "kualitas portofolio kredit, konsentrasi deposito, dan segmentasi nasabah "
            "dengan cara yang lebih cepat dan lebih mudah dipahami. Jika Anda perlu "
            "jawaban yang berasal dari dokumen, SOP, atau knowledge base, aktifkan "
            "dulu RAG Studio dari aplikasi.\n\n"
            "Kalau mau mulai, Anda bisa tanya hal seperti:\n"
            "1. Berapa total outstanding kredit saat ini?\n"
            "2. Siapa nasabah dengan outstanding kredit tertinggi?\n"
            "3. Bagaimana tren outstanding kredit per bulan?\n"
            "4. Bagaimana distribusi portofolio berdasarkan segmen atau kota?"
        )

    return (
        "Hello, it is great to meet you. I am the Data Analyst Assistant, "
        "ready to help you explore credit risk, outstanding exposure, portfolio quality, "
        "deposit concentration, and supporting customer analysis in a clear and practical way. "
        "If you need answers grounded in documents or knowledge-base content, enable RAG Studio first.\n\n"
        "You can start with questions like:\n"
        "1. What is the total outstanding credit right now?\n"
        "2. Who has the highest outstanding credit?\n"
        "3. How is outstanding credit trending by month?\n"
        "4. Which segments or cities hold the largest portfolio exposure?"
    )


def build_acknowledgement_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Sama-sama. Senang bisa membantu. Kalau Anda mau, lanjutkan saja "
            "dengan pertanyaan berikutnya tentang nasabah, deposito, kredit, fraud, segmen, atau cabang."
        )

    return (
        "Glad to help. If you want, just continue with the next question about "
        "deposit balances, credit exposure, suspicious transactions, customers, segments, or branches."
    )


def build_out_of_scope_answer(question: str) -> str:
    if is_indonesian_text(question):
        return (
            "Saya paling cocok membantu pertanyaan yang berhubungan dengan data "
            "deposito, kredit, dan konteks nasabah yang mendukung analisis itu. "
            "Kalau yang Anda butuhkan berasal dari dokumen atau knowledge base, "
            "aktifkan RAG Studio terlebih dahulu."
        )

    return (
        "I am best suited for deposit, credit, and supporting customer-analysis questions. "
        "If you need answers from documents or a knowledge base, enable RAG Studio first."
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
            "Coba tuliskan pertanyaannya lebih spesifik, misalnya tentang total saldo deposito, "
            "outstanding kredit, komposisi portofolio, nasabah terbesar, atau tren kredit. "
            "Jika pertanyaannya butuh dokumen atau SOP, aktifkan RAG Studio terlebih dahulu."
        )

    return (
        "I am sorry, I could not process that question cleanly just now. "
        "Please try asking in a more specific way, for example about total deposit balance, "
        "outstanding credit, portfolio composition, top debtors, or branch-level credit trends. "
        "If the question depends on documents or SOPs, enable RAG Studio first."
    )
