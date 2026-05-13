import calendar
import csv
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


SEED = 42
CUSTOMER_COUNT = 10_000
DEPOSIT_COUNT = 18_000
CREDIT_COUNT = 12_000
FRAUD_TRANSACTION_COUNT = 24_000
FRAUD_RATIO = 0.40
OUTPUT_DIR = Path("sample")

CITIES = ["Jakarta", "Bandung", "Surabaya", "Semarang", "Medan", "Yogyakarta"]
CITY_TO_BRANCH = {
    "Jakarta": "JKT01",
    "Bandung": "BDG01",
    "Surabaya": "SBY01",
    "Semarang": "SMG01",
    "Medan": "MDN01",
    "Yogyakarta": "YGY01",
}
CITY_DISTANCES = {
    ("Jakarta", "Bandung"): 150.0,
    ("Jakarta", "Surabaya"): 780.0,
    ("Jakarta", "Semarang"): 450.0,
    ("Jakarta", "Medan"): 1420.0,
    ("Jakarta", "Yogyakarta"): 560.0,
    ("Bandung", "Surabaya"): 670.0,
    ("Bandung", "Semarang"): 420.0,
    ("Bandung", "Medan"): 1500.0,
    ("Bandung", "Yogyakarta"): 390.0,
    ("Surabaya", "Semarang"): 350.0,
    ("Surabaya", "Medan"): 1860.0,
    ("Surabaya", "Yogyakarta"): 330.0,
    ("Semarang", "Medan"): 1630.0,
    ("Semarang", "Yogyakarta"): 130.0,
    ("Medan", "Yogyakarta"): 1800.0,
}
SEGMENTS = ["Mass", "Priority", "SME"]
BRANCH_CODES = ["JKT01", "JKT02", "BDG01", "SBY01", "SMG01", "MDN01", "YGY01"]
PRODUCT_TYPES = ["Savings", "Time Deposit"]
STATUSES = ["ACTIVE", "INACTIVE"]
CREDIT_TYPES = ["Mortgage", "Working Capital", "Auto Loan", "Personal Loan", "Credit Card"]
CREDIT_STATUSES = ["ACTIVE", "CLOSED", "RESTRUCTURED"]
COLLECTIBILITY_STATUSES = ["CURRENT", "SPECIAL_MENTION", "SUBSTANDARD", "DOUBTFUL"]

TRANSACTION_TYPES = ["transfer", "cash_out", "bill_payment", "card_payment", "topup"]
CHANNELS = ["mobile_app", "atm", "branch", "internet_banking", "edc"]
DEVICE_OS_BY_CHANNEL = {
    "mobile_app": "Android",
    "internet_banking": "Web",
    "atm": "ATM",
    "branch": "Branch Terminal",
    "edc": "POS",
}
NETWORK_BY_CHANNEL = {
    "mobile_app": ["wifi", "cellular"],
    "internet_banking": ["wifi", "cellular"],
    "atm": ["atm_network"],
    "branch": ["branch_network"],
    "edc": ["merchant_network"],
}
MERCHANT_CATEGORY_BY_TYPE = {
    "transfer": ["peer_transfer", "bank_transfer", "wallet_transfer"],
    "cash_out": ["atm_withdrawal", "cash_pickup"],
    "bill_payment": ["utility", "telecom", "insurance", "education"],
    "card_payment": ["grocery", "travel", "electronics", "fashion", "fnb"],
    "topup": ["e_wallet", "mobile_topup", "game_credit"],
}
BENEFICIARY_BANKS = [
    "BNI",
    "BCA",
    "BRI",
    "Mandiri",
    "CIMB Niaga",
    "Permata",
    "BSI",
    "SeaBank",
    "Jago",
]
FRAUD_REASONS = [
    "new_device_high_amount",
    "impossible_travel",
    "burst_transfer",
    "mule_pattern",
    "account_takeover",
]

NAME_PREFIXES = ["", "", "", "dr.", "drg.", "Ir.", "H.", "Hj.", "KH.", "Tgk.", "Dt.", "R.A.", "R.M.", "Drs."]
FIRST_NAMES = [
    "Ayu", "Salsabila", "Intan", "Rachel", "Nadia", "Olivia", "Julia", "Ani", "Indah", "Maya",
    "Putri", "Kezia", "Gabriella", "Lalita", "Zahra", "Talia", "Rafi", "Irfan", "Bagus", "Mahfud",
    "Lukman", "Hasan", "Dodo", "Catur", "Taufan", "Satya", "Paiman", "Dian", "Restu", "Lanjar",
    "Yessi", "Endah", "Anita", "Hesti", "Shania", "Cindy", "Michelle", "Kamila", "Vera", "Ifa",
]
MIDDLE_NAMES = [
    "Utami", "Laksita", "Prasetya", "Padmasari", "Rahmawati", "Puspasari", "Pradipta", "Wacana",
    "Permata", "Hidayat", "Palastri", "Mandala", "Kurniawan", "Saptono", "Sihombing", "Sinaga",
    "Hutagalung", "Prabowo", "Haryanto", "Sitorus", "Mangunsong", "Sirait", "Nasyiah", "Mayasari",
    "Gunawan", "Prakasa", "Halim", "Nababan", "Thamrin", "Hasanah",
]
LAST_NAMES = [
    "Wijayanti", "Pratama", "Halimah", "Firmansyah", "Haryanti", "Nuraini", "Siregar", "Purnawati",
    "Gunarto", "Kusuma", "Maheswara", "Yulianti", "Wibowo", "Suryatmi", "Suwarno", "Simbolon",
    "Latupono", "Sitompul", "Adriansyah", "Widiastuti", "Narpati", "Kuswoyo", "Pranowo", "Hastuti",
    "Melani", "Anggraini", "Hariyah", "Maryati", "Uyainah", "Prasasta",
]
NAME_SUFFIXES = ["", "", "", "S.E.", "S.H.", "S.T.", "S.Kom", "S.Psi", "M.Kom.", "M.TI.", "M.M.", "S.Farm", "S.Pd", "S.E.I", "M.Ak", "S.Gz", "S.Pt", "M.Farm"]


def format_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def format_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def clean_full_name(value: str) -> str:
    return " ".join(value.replace('"', " ").replace(",", " ").split())


def random_date(start: date, end: date) -> date:
    day_span = (end - start).days
    return start + timedelta(days=random.randint(0, day_span))


def random_datetime(start: datetime, end: datetime) -> datetime:
    second_span = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, second_span))


def date_in_current_week(target_date: date, today: date) -> bool:
    week_start = today - timedelta(days=today.weekday())
    week_days = {(week_start + timedelta(days=offset)).strftime("%m-%d") for offset in range(7)}
    target_day = target_date.strftime("%m-%d")

    if target_day == "02-29" and not calendar.isleap(today.year):
        target_day = "02-28"

    return target_day in week_days


def generate_birth_date(today: date, birthday_this_week: bool) -> date:
    birth_year = random.randint(1960, 2003)
    if birthday_this_week:
        week_start = today - timedelta(days=today.weekday())
        birthday_anchor = week_start + timedelta(days=random.randint(0, 6))
        return birthday_anchor.replace(year=birth_year)

    while True:
        candidate = random_date(date(1960, 1, 1), date(2003, 12, 31))
        if not date_in_current_week(candidate, today):
            return candidate


def generate_join_date(birth_date: date, today: date) -> date:
    eligible_start = max(birth_date + timedelta(days=18 * 365), date(2010, 1, 1))
    eligible_end = today - timedelta(days=1)
    if eligible_start > eligible_end:
        eligible_start = date(2010, 1, 1)
    return random_date(eligible_start, eligible_end)


def choose_segment() -> str:
    return random.choices(SEGMENTS, weights=[0.62, 0.20, 0.18], k=1)[0]


def choose_city() -> str:
    return random.choice(CITIES)


def customer_sampling_weight(segment: str) -> int:
    if segment == "Priority":
        return 5
    if segment == "SME":
        return 3
    return 2


def build_full_name() -> str:
    prefix = random.choice(NAME_PREFIXES)
    pieces = [prefix, random.choice(FIRST_NAMES), random.choice(MIDDLE_NAMES), random.choice(LAST_NAMES)]
    if random.random() < 0.18:
        pieces.insert(2, random.choice(FIRST_NAMES))
    suffix = random.choice(NAME_SUFFIXES)
    if suffix:
        pieces.append(suffix)
    return clean_full_name(" ".join(piece for piece in pieces if piece))


def choose_product_type(segment: str) -> str:
    if segment == "Priority":
        return random.choices(PRODUCT_TYPES, weights=[0.45, 0.55], k=1)[0]
    if segment == "SME":
        return random.choices(PRODUCT_TYPES, weights=[0.60, 0.40], k=1)[0]
    return random.choices(PRODUCT_TYPES, weights=[0.75, 0.25], k=1)[0]


def generate_balance(segment: str, product_type: str) -> int:
    if product_type == "Savings":
        if segment == "Priority":
            return int(random.triangular(10_000_000, 250_000_000, 90_000_000))
        if segment == "SME":
            return int(random.triangular(5_000_000, 120_000_000, 35_000_000))
        return int(random.triangular(1_000_000, 50_000_000, 10_000_000))

    if segment == "Priority":
        return int(random.triangular(150_000_000, 2_000_000_000, 900_000_000))
    if segment == "SME":
        return int(random.triangular(75_000_000, 1_250_000_000, 450_000_000))
    return int(random.triangular(50_000_000, 1_000_000_000, 220_000_000))


def generate_maturity_date(today: date, product_type: str, near_term: bool) -> date:
    if near_term:
        return today + timedelta(days=random.randint(1, 14))

    if product_type == "Time Deposit":
        return today + timedelta(days=random.randint(15, 365))
    return today + timedelta(days=random.randint(30, 730))


def choose_credit_type(segment: str) -> str:
    if segment == "SME":
        return random.choices(CREDIT_TYPES, weights=[0.10, 0.48, 0.08, 0.10, 0.24], k=1)[0]
    if segment == "Priority":
        return random.choices(CREDIT_TYPES, weights=[0.36, 0.14, 0.14, 0.14, 0.22], k=1)[0]
    return random.choices(CREDIT_TYPES, weights=[0.20, 0.08, 0.18, 0.34, 0.20], k=1)[0]


def generate_principal_amount(segment: str, credit_type: str) -> int:
    if credit_type == "Working Capital":
        if segment == "SME":
            return int(random.triangular(200_000_000, 3_000_000_000, 950_000_000))
        if segment == "Priority":
            return int(random.triangular(150_000_000, 1_500_000_000, 500_000_000))
        return int(random.triangular(75_000_000, 600_000_000, 220_000_000))

    if credit_type == "Mortgage":
        if segment == "Priority":
            return int(random.triangular(300_000_000, 2_500_000_000, 1_100_000_000))
        return int(random.triangular(200_000_000, 1_750_000_000, 650_000_000))

    if credit_type == "Auto Loan":
        return int(random.triangular(80_000_000, 650_000_000, 220_000_000))

    if credit_type == "Credit Card":
        if segment == "Priority":
            return int(random.triangular(20_000_000, 250_000_000, 85_000_000))
        return int(random.triangular(5_000_000, 120_000_000, 30_000_000))

    if segment == "Priority":
        return int(random.triangular(30_000_000, 400_000_000, 140_000_000))
    if segment == "SME":
        return int(random.triangular(50_000_000, 750_000_000, 200_000_000))
    return int(random.triangular(15_000_000, 200_000_000, 70_000_000))


def choose_credit_status() -> str:
    return random.choices(CREDIT_STATUSES, weights=[0.79, 0.14, 0.07], k=1)[0]


def generate_interest_rate(credit_type: str, segment: str) -> float:
    if credit_type == "Mortgage":
        base_rate = random.uniform(5.5, 10.5)
    elif credit_type == "Working Capital":
        base_rate = random.uniform(7.5, 13.5)
    elif credit_type == "Auto Loan":
        base_rate = random.uniform(6.0, 11.5)
    elif credit_type == "Credit Card":
        base_rate = random.uniform(18.0, 24.0)
    else:
        base_rate = random.uniform(8.5, 17.5)

    if segment == "Priority":
        base_rate -= 0.6
    elif segment == "SME":
        base_rate += 0.4

    return round(max(base_rate, 4.5), 2)


def choose_collectibility(status: str) -> str:
    if status == "CLOSED":
        return "CURRENT"
    if status == "RESTRUCTURED":
        return random.choices(COLLECTIBILITY_STATUSES, weights=[0.18, 0.42, 0.26, 0.14], k=1)[0]
    return random.choices(COLLECTIBILITY_STATUSES, weights=[0.84, 0.10, 0.04, 0.02], k=1)[0]


def generate_credit_dates(today: date, status: str, credit_type: str) -> tuple[date, date]:
    disbursement_date = random_date(date(2016, 1, 1), today - timedelta(days=30))

    if credit_type == "Mortgage":
        term_days = random.randint(5 * 365, 20 * 365)
    elif credit_type == "Working Capital":
        term_days = random.randint(365, 7 * 365)
    elif credit_type == "Credit Card":
        term_days = random.randint(365, 5 * 365)
    else:
        term_days = random.randint(2 * 365, 8 * 365)

    maturity_date = disbursement_date + timedelta(days=term_days)
    if status == "CLOSED":
        maturity_date = min(maturity_date, today - timedelta(days=random.randint(1, 120)))
    elif maturity_date <= today:
        maturity_date = today + timedelta(days=random.randint(30, 900))

    return disbursement_date, maturity_date


def generate_outstanding_balance(principal_amount: int, status: str, collectibility: str) -> int:
    if status == "CLOSED":
        return int(random.triangular(0, max(1, principal_amount // 25), 0))

    utilization_floor = 0.18
    if collectibility == "SPECIAL_MENTION":
        utilization_floor = 0.25
    elif collectibility == "SUBSTANDARD":
        utilization_floor = 0.32
    elif collectibility == "DOUBTFUL":
        utilization_floor = 0.38

    return int(random.triangular(int(principal_amount * utilization_floor), principal_amount, int(principal_amount * 0.68)))


def generate_customers() -> list[dict[str, str | int]]:
    today = date.today()
    birthday_customer_ids = set(random.sample(range(1, CUSTOMER_COUNT + 1), 8))
    rows: list[dict[str, str | int]] = []

    for customer_id in range(1, CUSTOMER_COUNT + 1):
        birth_date = generate_birth_date(today=today, birthday_this_week=customer_id in birthday_customer_ids)
        join_date = generate_join_date(birth_date=birth_date, today=today)
        rows.append(
            {
                "customer_id": customer_id,
                "full_name": build_full_name(),
                "birth_date": format_date(birth_date),
                "city": choose_city(),
                "segment": choose_segment(),
                "join_date": format_date(join_date),
            }
        )

    return rows


def generate_deposits(customers: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    today = date.today()
    weights = [customer_sampling_weight(str(record["segment"])) for record in customers]
    near_term_indices = set(random.sample(range(DEPOSIT_COUNT), 12))
    rows: list[dict[str, str | int]] = []

    for offset in range(DEPOSIT_COUNT):
        customer = random.choices(customers, weights=weights, k=1)[0]
        customer_id = int(customer["customer_id"])
        segment = str(customer["segment"])
        product_type = choose_product_type(segment)
        if offset in near_term_indices:
            product_type = "Time Deposit"

        if offset < int(DEPOSIT_COUNT * 0.84):
            status = "ACTIVE"
        else:
            status = random.choices(STATUSES, weights=[0.25, 0.75], k=1)[0]

        rows.append(
            {
                "account_id": 1001 + offset,
                "customer_id": customer_id,
                "product_type": product_type,
                "balance": generate_balance(segment=segment, product_type=product_type),
                "maturity_date": format_date(
                    generate_maturity_date(today=today, product_type=product_type, near_term=offset in near_term_indices)
                ),
                "branch_code": random.choice(BRANCH_CODES),
                "status": status,
            }
        )

    return rows


def generate_credits(customers: list[dict[str, str | int]]) -> list[dict[str, str | int | float]]:
    today = date.today()
    weights = [customer_sampling_weight(str(record["segment"])) for record in customers]
    rows: list[dict[str, str | int | float]] = []

    for offset in range(CREDIT_COUNT):
        customer = random.choices(customers, weights=weights, k=1)[0]
        customer_id = int(customer["customer_id"])
        segment = str(customer["segment"])
        credit_type = choose_credit_type(segment)
        status = choose_credit_status()
        principal_amount = generate_principal_amount(segment=segment, credit_type=credit_type)
        collectibility = choose_collectibility(status)
        disbursement_date, maturity_date = generate_credit_dates(today=today, status=status, credit_type=credit_type)

        rows.append(
            {
                "credit_id": 5001 + offset,
                "customer_id": customer_id,
                "credit_type": credit_type,
                "principal_amount": principal_amount,
                "outstanding_balance": generate_outstanding_balance(
                    principal_amount=principal_amount,
                    status=status,
                    collectibility=collectibility,
                ),
                "interest_rate": generate_interest_rate(credit_type=credit_type, segment=segment),
                "disbursement_date": format_date(disbursement_date),
                "maturity_date": format_date(maturity_date),
                "collectibility": collectibility,
                "branch_code": random.choice(BRANCH_CODES),
                "status": status,
            }
        )

    return rows


def choose_transaction_type(is_fraud: bool) -> str:
    if is_fraud:
        return random.choices(
            TRANSACTION_TYPES,
            weights=[0.52, 0.12, 0.06, 0.20, 0.10],
            k=1,
        )[0]
    return random.choices(
        TRANSACTION_TYPES,
        weights=[0.26, 0.15, 0.22, 0.24, 0.13],
        k=1,
    )[0]


def choose_channel(transaction_type: str, is_fraud: bool) -> str:
    if transaction_type == "cash_out":
        return random.choices(CHANNELS, weights=[0.05, 0.80, 0.05, 0.05, 0.05], k=1)[0]
    if transaction_type == "card_payment":
        return random.choices(CHANNELS, weights=[0.12, 0.02, 0.01, 0.10, 0.75], k=1)[0]
    if is_fraud:
        return random.choices(CHANNELS, weights=[0.46, 0.08, 0.03, 0.37, 0.06], k=1)[0]
    return random.choices(CHANNELS, weights=[0.36, 0.10, 0.05, 0.34, 0.15], k=1)[0]


def generate_customer_timestamp(history: list[dict[str, object]], is_fraud: bool) -> datetime:
    end_dt = datetime.combine(date.today(), datetime.min.time()).replace(hour=23, minute=45, second=0)
    start_dt = end_dt - timedelta(days=180)
    if not history:
        return random_datetime(start_dt, end_dt - timedelta(days=60))

    last_ts = history[-1]["timestamp"]
    if not isinstance(last_ts, datetime):
        raise TypeError("history timestamp must be datetime")

    if is_fraud and random.random() < 0.30:
        candidate = last_ts + timedelta(minutes=random.randint(2, 110))
    else:
        candidate = last_ts + timedelta(
            hours=random.randint(6, 72),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

    return min(candidate, end_dt)


def choose_destination_city(home_city: str, is_fraud: bool, fraud_reason: str) -> str:
    if fraud_reason == "impossible_travel":
        far_cities = [city for city in CITIES if city != home_city]
        return max(far_cities, key=lambda city: estimate_distance_km(home_city, city))

    if is_fraud and random.random() < 0.45:
        candidates = [city for city in CITIES if city != home_city]
        return random.choice(candidates)

    if random.random() < 0.82:
        return home_city

    candidates = [city for city in CITIES if city != home_city]
    return random.choice(candidates)


def estimate_distance_km(origin_city: str, destination_city: str) -> float:
    if origin_city == destination_city:
        return round(random.uniform(1.0, 24.0), 2)

    key = tuple(sorted((origin_city, destination_city)))
    base_distance = CITY_DISTANCES.get(key, 650.0)
    return round(base_distance + random.uniform(-25.0, 40.0), 2)


def choose_beneficiary_bank(is_fraud: bool) -> str:
    if is_fraud:
        return random.choices(BENEFICIARY_BANKS, weights=[0.07, 0.15, 0.10, 0.14, 0.12, 0.08, 0.10, 0.12, 0.12], k=1)[0]
    return random.choices(BENEFICIARY_BANKS, weights=[0.28, 0.10, 0.10, 0.12, 0.08, 0.06, 0.06, 0.10, 0.10], k=1)[0]


def build_device_id(customer_id: int, channel: str, ordinal: int) -> str:
    return f"{channel[:3].upper()}-{customer_id:05d}-{ordinal:02d}"


def build_ip_address(home_city: str, is_foreign_ip: bool) -> str:
    if is_foreign_ip:
        first_octet = random.choice([43, 58, 103, 118, 172, 185, 203])
        return f"{first_octet}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    city_prefix = {
        "Jakarta": 36,
        "Bandung": 114,
        "Surabaya": 120,
        "Semarang": 125,
        "Medan": 139,
        "Yogyakarta": 180,
    }
    first_octet = city_prefix.get(home_city, 36)
    return f"{first_octet}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def choose_amount(segment: str, transaction_type: str, is_fraud: bool, fraud_reason: str) -> int:
    normal_ranges = {
        "transfer": {
            "Mass": (150_000, 18_000_000, 2_200_000),
            "Priority": (500_000, 95_000_000, 12_500_000),
            "SME": (1_000_000, 250_000_000, 28_000_000),
        },
        "cash_out": {
            "Mass": (50_000, 6_000_000, 900_000),
            "Priority": (100_000, 20_000_000, 2_500_000),
            "SME": (100_000, 35_000_000, 3_600_000),
        },
        "bill_payment": {
            "Mass": (35_000, 2_500_000, 450_000),
            "Priority": (50_000, 5_000_000, 700_000),
            "SME": (75_000, 12_000_000, 1_400_000),
        },
        "card_payment": {
            "Mass": (40_000, 8_000_000, 850_000),
            "Priority": (60_000, 18_000_000, 1_500_000),
            "SME": (80_000, 25_000_000, 2_000_000),
        },
        "topup": {
            "Mass": (20_000, 1_500_000, 250_000),
            "Priority": (20_000, 3_500_000, 350_000),
            "SME": (20_000, 5_000_000, 500_000),
        },
    }
    low, high, mode = normal_ranges[transaction_type][segment]

    if is_fraud:
        multiplier_low = 3.2
        multiplier_high = 8.5
        if fraud_reason == "mule_pattern":
            multiplier_low = 1.8
            multiplier_high = 4.2
        elif fraud_reason == "account_takeover":
            multiplier_low = 4.0
            multiplier_high = 10.0
        elif fraud_reason == "burst_transfer":
            multiplier_low = 2.2
            multiplier_high = 5.0

        low = int(low * multiplier_low)
        high = int(high * multiplier_high)
        mode = int(mode * ((multiplier_low + multiplier_high) / 2))

    amount = int(random.triangular(low, high, mode))
    if (is_fraud and random.random() < 0.55) or (not is_fraud and random.random() < 0.12):
        amount = max(50_000, round(amount / 500_000) * 500_000)
    return amount


def summarize_recent_history(history: list[dict[str, object]], current_ts: datetime) -> tuple[int, int, int, int, float]:
    count_1d = 0
    count_7d = 0
    amount_1d = 0
    amount_7d = 0
    amount_30d_values: list[int] = []

    for event in reversed(history):
        event_ts = event["timestamp"]
        event_amount = event["amount"]
        if not isinstance(event_ts, datetime) or not isinstance(event_amount, int):
            raise TypeError("history rows must contain timestamp datetime and amount int")

        delta = current_ts - event_ts
        if delta <= timedelta(days=30):
            amount_30d_values.append(event_amount)
        if delta <= timedelta(days=7):
            count_7d += 1
            amount_7d += event_amount
        else:
            break
        if delta <= timedelta(days=1):
            count_1d += 1
            amount_1d += event_amount

    avg_30d = sum(amount_30d_values) / len(amount_30d_values) if amount_30d_values else 0.0
    return count_1d, count_7d, amount_1d, amount_7d, avg_30d


def compute_days_since_last_txn(history: list[dict[str, object]], current_ts: datetime) -> int:
    if not history:
        return 999
    last_ts = history[-1]["timestamp"]
    if not isinstance(last_ts, datetime):
        raise TypeError("history timestamp must be datetime")
    return max(0, (current_ts.date() - last_ts.date()).days)


def compute_customer_age(birth_date: date, transaction_date: date) -> int:
    age = transaction_date.year - birth_date.year
    before_birthday = (transaction_date.month, transaction_date.day) < (birth_date.month, birth_date.day)
    return age - int(before_birthday)


def choose_merchant_category(transaction_type: str) -> str:
    return random.choice(MERCHANT_CATEGORY_BY_TYPE[transaction_type])


def build_merchant_name(category: str, beneficiary_bank: str, transaction_type: str) -> str:
    if transaction_type == "transfer":
        return f"{beneficiary_bank} Transfer Hub"
    if category == "utility":
        return random.choice(["PLN Biller", "PAM Utility", "Gas Nusantara"])
    if category == "telecom":
        return random.choice(["Telkomsel Payment", "Indosat Billing", "XL Reload"])
    if category == "insurance":
        return random.choice(["BNI Life", "Asuransi Sehat", "Proteksi Keluarga"])
    if category == "education":
        return random.choice(["Campus Payment", "School Tuition", "Learning Center"])
    if category == "grocery":
        return random.choice(["FreshMart", "Hypermart", "Daily Needs"])
    if category == "travel":
        return random.choice(["Traveloka Merchant", "SkyFly", "Rail Ticket"])
    if category == "electronics":
        return random.choice(["ElectroHub", "Gadget Point", "Digital Square"])
    if category == "fashion":
        return random.choice(["Urban Style", "Fashion Lane", "Kanvas Wear"])
    if category == "fnb":
        return random.choice(["Coffee Stop", "Rasa Nusantara", "Food Avenue"])
    if category == "e_wallet":
        return random.choice(["GoPay Topup", "OVO Reload", "DANA Topup"])
    if category == "mobile_topup":
        return random.choice(["Pulsa Instan", "Data Package Center", "Quick Reload"])
    if category == "game_credit":
        return random.choice(["Game Vault", "Topup Arena", "Playpoint"])
    if category == "atm_withdrawal":
        return "ATM Cash Withdrawal"
    if category == "cash_pickup":
        return "Cash Pickup Counter"
    return "General Merchant"


def compute_velocity_risk_score(
    is_fraud: bool,
    count_1d: int,
    count_7d: int,
    amount_ratio: float,
    failed_login_count_24h: int,
    is_night_txn: int,
) -> float:
    score = 15.0 + (count_1d * 7.5) + (count_7d * 1.2) + (min(amount_ratio, 10.0) * 4.0)
    score += failed_login_count_24h * 3.5
    score += is_night_txn * 5.0
    if is_fraud:
        score += 16.0
    return round(min(score, 100.0), 2)


def compute_behavioral_risk_score(
    is_fraud: bool,
    is_new_device: int,
    is_foreign_ip: int,
    is_new_beneficiary: int,
    distance_from_home_km: float,
    amount_ratio: float,
) -> float:
    score = 12.0
    score += is_new_device * 18.0
    score += is_foreign_ip * 20.0
    score += is_new_beneficiary * 16.0
    score += min(distance_from_home_km / 55.0, 22.0)
    score += min(amount_ratio, 10.0) * 3.0
    if is_fraud:
        score += 12.0
    return round(min(score, 100.0), 2)


def choose_fraud_reason() -> str:
    return random.choices(
        FRAUD_REASONS,
        weights=[0.28, 0.18, 0.22, 0.16, 0.16],
        k=1,
    )[0]


def build_customer_reference(customers: list[dict[str, str | int]]) -> dict[int, dict[str, object]]:
    reference: dict[int, dict[str, object]] = {}
    for row in customers:
        customer_id = int(row["customer_id"])
        city = str(row["city"])
        reference[customer_id] = {
            "customer_id": customer_id,
            "city": city,
            "segment": str(row["segment"]),
            "birth_date": parse_date(str(row["birth_date"])),
            "join_date": parse_date(str(row["join_date"])),
            "home_branch_code": CITY_TO_BRANCH.get(city, random.choice(BRANCH_CODES)),
        }
    return reference


def build_deposit_reference(deposits: list[dict[str, str | int]]) -> dict[int, list[int]]:
    mapping: dict[int, list[int]] = defaultdict(list)
    for row in deposits:
        mapping[int(row["customer_id"])].append(int(row["account_id"]))
    return mapping


def generate_fraud_transactions(
    customers: list[dict[str, str | int]],
    deposits: list[dict[str, str | int]],
) -> list[dict[str, str | int | float]]:
    customer_reference = build_customer_reference(customers)
    deposit_reference = build_deposit_reference(deposits)
    history_by_customer: dict[int, list[dict[str, object]]] = defaultdict(list)
    device_registry: dict[int, list[str]] = defaultdict(list)
    beneficiary_registry: dict[int, list[str]] = defaultdict(list)

    rows: list[dict[str, str | int | float]] = []
    weights = [customer_sampling_weight(str(record["segment"])) for record in customers]
    fraud_row_count = int(FRAUD_TRANSACTION_COUNT * FRAUD_RATIO)
    fraud_indices = set(random.sample(range(FRAUD_TRANSACTION_COUNT), fraud_row_count))

    for offset in range(FRAUD_TRANSACTION_COUNT):
        customer = random.choices(customers, weights=weights, k=1)[0]
        customer_id = int(customer["customer_id"])
        customer_profile = customer_reference[customer_id]
        customer_history = history_by_customer[customer_id]
        is_fraud = offset in fraud_indices
        fraud_reason = choose_fraud_reason() if is_fraud else "legitimate_activity"

        transaction_type = choose_transaction_type(is_fraud)
        channel = choose_channel(transaction_type, is_fraud)
        transaction_ts = generate_customer_timestamp(customer_history, is_fraud)
        transaction_dt = transaction_ts.date()

        count_1d, count_7d, amount_1d, amount_7d, avg_30d = summarize_recent_history(customer_history, transaction_ts)
        days_since_last_txn = compute_days_since_last_txn(customer_history, transaction_ts)
        amount = choose_amount(str(customer_profile["segment"]), transaction_type, is_fraud, fraud_reason)
        avg_reference = avg_30d if avg_30d > 0 else max(amount / random.uniform(0.85, 1.25), 50_000.0)
        if is_fraud and fraud_reason in {"new_device_high_amount", "account_takeover"}:
            avg_reference = max(avg_reference, amount / random.uniform(3.0, 7.5))
        amount_ratio = round(amount / max(avg_reference, 1.0), 2)

        existing_devices = device_registry[customer_id]
        if existing_devices and ((not is_fraud and random.random() < 0.95) or (is_fraud and random.random() < 0.38)):
            device_id = random.choice(existing_devices)
            is_new_device = 0
        else:
            device_id = build_device_id(customer_id, channel, len(existing_devices) + 1)
            existing_devices.append(device_id)
            is_new_device = 1

        if is_fraud:
            is_foreign_ip = 1 if fraud_reason in {"impossible_travel", "account_takeover"} or random.random() < 0.58 else 0
        else:
            is_foreign_ip = 1 if random.random() < 0.03 else 0
        ip_address = build_ip_address(str(customer_profile["city"]), bool(is_foreign_ip))

        beneficiary_bank = choose_beneficiary_bank(is_fraud)
        known_beneficiaries = beneficiary_registry[customer_id]
        if known_beneficiaries and ((not is_fraud and random.random() < 0.78) or (is_fraud and random.random() < 0.22)):
            beneficiary_name = random.choice(known_beneficiaries)
            is_new_beneficiary = 0
        else:
            beneficiary_name = f"{beneficiary_bank} {random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"
            known_beneficiaries.append(beneficiary_name)
            is_new_beneficiary = 1

        if is_fraud:
            beneficiary_account_age_days = random.randint(0, 40) if is_new_beneficiary else random.randint(10, 120)
        else:
            beneficiary_account_age_days = random.randint(45, 1500) if not is_new_beneficiary else random.randint(15, 300)

        destination_city = choose_destination_city(str(customer_profile["city"]), is_fraud, fraud_reason)
        distance_from_home_km = estimate_distance_km(str(customer_profile["city"]), destination_city)

        if is_fraud and fraud_reason in {"new_device_high_amount", "account_takeover"}:
            failed_login_count_24h = random.randint(3, 9)
        elif is_fraud and fraud_reason == "burst_transfer":
            failed_login_count_24h = random.randint(1, 4)
        else:
            failed_login_count_24h = random.randint(0, 2)

        if is_fraud and fraud_reason in {"new_device_high_amount", "account_takeover", "burst_transfer"}:
            transaction_ts = transaction_ts.replace(hour=random.randint(0, 4), minute=random.randint(0, 59), second=random.randint(0, 59))
        is_night_txn = 1 if transaction_ts.hour < 6 else 0
        is_weekend_txn = 1 if transaction_ts.weekday() >= 5 else 0
        is_round_amount = 1 if amount % 500_000 == 0 else 0

        if channel == "mobile_app":
            device_os = random.choices(["Android", "iOS"], weights=[0.72, 0.28], k=1)[0]
        else:
            device_os = DEVICE_OS_BY_CHANNEL[channel]
        network_type = random.choice(NETWORK_BY_CHANNEL[channel])

        merchant_category = choose_merchant_category(transaction_type)
        merchant_name = build_merchant_name(merchant_category, beneficiary_bank, transaction_type)
        account_id_candidates = deposit_reference.get(customer_id)
        account_id = random.choice(account_id_candidates) if account_id_candidates else 900000 + customer_id
        txn_count_1d = count_1d + 1
        txn_count_7d = count_7d + 1
        txn_amount_1d = amount_1d + amount
        txn_amount_7d = amount_7d + amount
        customer_age = compute_customer_age(customer_profile["birth_date"], transaction_dt)
        account_tenure_days = max(1, (transaction_dt - customer_profile["join_date"]).days)
        velocity_risk_score = compute_velocity_risk_score(
            is_fraud=is_fraud,
            count_1d=txn_count_1d,
            count_7d=txn_count_7d,
            amount_ratio=amount_ratio,
            failed_login_count_24h=failed_login_count_24h,
            is_night_txn=is_night_txn,
        )
        behavioral_risk_score = compute_behavioral_risk_score(
            is_fraud=is_fraud,
            is_new_device=is_new_device,
            is_foreign_ip=is_foreign_ip,
            is_new_beneficiary=is_new_beneficiary,
            distance_from_home_km=distance_from_home_km,
            amount_ratio=amount_ratio,
        )

        row = {
            "transaction_id": 900001 + offset,
            "customer_id": customer_id,
            "account_id": account_id,
            "transaction_timestamp": format_timestamp(transaction_ts),
            "transaction_date": format_date(transaction_dt),
            "transaction_type": transaction_type,
            "channel": channel,
            "amount": amount,
            "currency_code": "IDR",
            "merchant_category": merchant_category,
            "merchant_name": merchant_name,
            "origin_city": str(customer_profile["city"]),
            "destination_city": destination_city,
            "origin_branch_code": str(customer_profile["home_branch_code"]),
            "device_id": device_id,
            "device_os": device_os,
            "ip_address": ip_address,
            "network_type": network_type,
            "is_new_device": is_new_device,
            "is_foreign_ip": is_foreign_ip,
            "customer_segment": str(customer_profile["segment"]),
            "customer_age": customer_age,
            "account_tenure_days": account_tenure_days,
            "days_since_last_txn": days_since_last_txn,
            "txn_count_1d": txn_count_1d,
            "txn_count_7d": txn_count_7d,
            "txn_amount_1d": txn_amount_1d,
            "txn_amount_7d": txn_amount_7d,
            "avg_txn_amount_30d": round(avg_reference, 2),
            "amount_vs_avg_30d_ratio": amount_ratio,
            "is_round_amount": is_round_amount,
            "is_night_txn": is_night_txn,
            "is_weekend_txn": is_weekend_txn,
            "failed_login_count_24h": failed_login_count_24h,
            "beneficiary_bank": beneficiary_bank,
            "beneficiary_account_age_days": beneficiary_account_age_days,
            "is_new_beneficiary": is_new_beneficiary,
            "distance_from_home_km": distance_from_home_km,
            "velocity_risk_score": velocity_risk_score,
            "behavioral_risk_score": behavioral_risk_score,
            "fraud_flag": int(is_fraud),
            "fraud_reason": fraud_reason,
        }
        rows.append(row)
        customer_history.append({"timestamp": transaction_ts, "amount": amount})
        customer_history.sort(key=lambda item: item["timestamp"])

    rows.sort(key=lambda item: str(item["transaction_timestamp"]))
    for index, row in enumerate(rows):
        row["transaction_id"] = 900001 + index
    return rows


def validate_join(customers: list[dict[str, str | int]], child_rows: list[dict[str, str | int | float]], child_name: str) -> bool:
    customer_ids = {int(row["customer_id"]) for row in customers}
    child_customer_ids = {int(row["customer_id"]) for row in child_rows}
    orphan_ids = sorted(child_customer_ids - customer_ids)
    is_valid = len(orphan_ids) == 0

    print(f"\nJoin validation for {child_name}")
    print(f"- all {child_name}.customer_id values exist in customers.customer_id: {is_valid}")
    print(f"- customers and {child_name} are safe to join on customer_id: {is_valid}")
    if not is_valid:
        print(f"- orphan customer_id values: {orphan_ids}")

    return is_valid


def count_birthdays_this_week(customers: list[dict[str, str | int]]) -> int:
    today = date.today()
    return sum(
        date_in_current_week(datetime.strptime(str(row["birth_date"]), "%Y-%m-%d").date(), today)
        for row in customers
    )


def count_maturing_next_14_days(deposits: list[dict[str, str | int]]) -> int:
    today = date.today()
    end_date = today + timedelta(days=14)
    return sum(
        today <= datetime.strptime(str(row["maturity_date"]), "%Y-%m-%d").date() <= end_date
        for row in deposits
    )


def summarize_credit_quality(credits: list[dict[str, str | int | float]]) -> dict[str, int]:
    return {
        "active_credits": sum(row["status"] == "ACTIVE" for row in credits),
        "restructured_credits": sum(row["status"] == "RESTRUCTURED" for row in credits),
        "closed_credits": sum(row["status"] == "CLOSED" for row in credits),
        "non_current_credits": sum(
            row["collectibility"] in {"SPECIAL_MENTION", "SUBSTANDARD", "DOUBTFUL"} for row in credits
        ),
    }


def summarize_fraud_transactions(transactions: list[dict[str, str | int | float]]) -> dict[str, float]:
    fraud_count = sum(int(row["fraud_flag"]) for row in transactions)
    total_amount = sum(int(row["amount"]) for row in transactions)
    fraud_amount = sum(int(row["amount"]) for row in transactions if int(row["fraud_flag"]) == 1)
    return {
        "total_transactions": len(transactions),
        "fraud_transactions": fraud_count,
        "non_fraud_transactions": len(transactions) - fraud_count,
        "fraud_ratio": round(fraud_count / len(transactions), 4) if transactions else 0.0,
        "fraud_amount_ratio": round(fraud_amount / total_amount, 4) if total_amount else 0.0,
    }


def write_csv(path: Path, rows: list[dict[str, str | int | float]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write CSV for empty dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_preview(title: str, rows: list[dict[str, str | int | float]], limit: int = 5) -> None:
    print(f"\n{title} preview")
    for row in rows[:limit]:
        print(row)


def main() -> None:
    random.seed(SEED)

    customers = generate_customers()
    deposits = generate_deposits(customers)
    credits = generate_credits(customers)
    fraud_transactions = generate_fraud_transactions(customers, deposits)

    deposits_join_valid = validate_join(customers, deposits, "deposits")
    credits_join_valid = validate_join(customers, credits, "credits")
    fraud_join_valid = validate_join(customers, fraud_transactions, "fraud_transactions")
    if not deposits_join_valid:
        raise ValueError("Generated deposits contain invalid customer_id values.")
    if not credits_join_valid:
        raise ValueError("Generated credits contain invalid customer_id values.")
    if not fraud_join_valid:
        raise ValueError("Generated fraud transactions contain invalid customer_id values.")

    write_csv(OUTPUT_DIR / "customers.csv", customers)
    write_csv(OUTPUT_DIR / "deposits.csv", deposits)
    write_csv(OUTPUT_DIR / "credits.csv", credits)
    write_csv(OUTPUT_DIR / "fraud_transactions.csv", fraud_transactions)

    total_active = sum(row["status"] == "ACTIVE" for row in deposits)
    total_inactive = sum(row["status"] == "INACTIVE" for row in deposits)
    maturing_next_14_days = count_maturing_next_14_days(deposits)
    birthdays_this_week = count_birthdays_this_week(customers)
    credit_quality_metrics = summarize_credit_quality(credits)
    fraud_metrics = summarize_fraud_transactions(fraud_transactions)

    print_preview("sample/customers.csv", customers)
    print_preview("sample/deposits.csv", deposits)
    print_preview("sample/credits.csv", credits)
    print_preview("sample/fraud_transactions.csv", fraud_transactions)

    print("\nSummary metrics")
    print(f"- total customers: {len(customers)}")
    print(f"- total deposits: {len(deposits)}")
    print(f"- total credits: {len(credits)}")
    print(f"- total fraud transactions: {fraud_metrics['total_transactions']}")
    print(f"- total fraudulent transactions: {fraud_metrics['fraud_transactions']}")
    print(f"- total non-fraud transactions: {fraud_metrics['non_fraud_transactions']}")
    print(f"- fraud transaction ratio: {fraud_metrics['fraud_ratio']}")
    print(f"- fraud amount ratio: {fraud_metrics['fraud_amount_ratio']}")
    print(f"- total active deposits: {total_active}")
    print(f"- total inactive deposits: {total_inactive}")
    print(f"- total deposits maturing in the next 14 days: {maturing_next_14_days}")
    print(f"- total customers with birthdays in the current week: {birthdays_this_week}")
    print(f"- total active credits: {credit_quality_metrics['active_credits']}")
    print(f"- total restructured credits: {credit_quality_metrics['restructured_credits']}")
    print(f"- total closed credits: {credit_quality_metrics['closed_credits']}")
    print(f"- total non-current credits: {credit_quality_metrics['non_current_credits']}")


if __name__ == "__main__":
    main()
