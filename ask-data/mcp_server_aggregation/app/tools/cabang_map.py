"""
Tool: cabang_map
Return geospatial data per cabang untuk visualisasi peta Jawa Timur.
Output: list of {cabang, cabang_name, kota, lat, lng, total, aktif, dormant, pct_dormant, avg_saldo}
"""
from __future__ import annotations

from typing import Any

from app.impala_client import execute_query, qualified_table

# Master data cabang: kode → (nama_cabang, kota, lat, lng)
CABANG_MASTER: dict[str, tuple[str, str, float, float]] = {
    "001": ("KP Surabaya Basuki Rahmat",    "Surabaya",     -7.2654,  112.7404),
    "002": ("KC Surabaya Gubeng",           "Surabaya",     -7.2654,  112.7404),
    "003": ("KC Surabaya Darmo",            "Surabaya",     -7.2993,  112.7341),
    "004": ("KC Surabaya Tunjungan",        "Surabaya",     -7.2589,  112.7378),
    "005": ("KC Surabaya Kenjeran",         "Surabaya",     -7.2284,  112.7728),
    "006": ("KC Surabaya Wonokromo",        "Surabaya",     -7.3098,  112.7342),
    "007": ("KC Surabaya Rungkut",          "Surabaya",     -7.3285,  112.7884),
    "008": ("KC Surabaya Wiyung",           "Surabaya",     -7.3278,  112.6892),
    "009": ("KC Surabaya Semampir",         "Surabaya",     -7.2253,  112.7452),
    "010": ("KC Surabaya Benowo",           "Surabaya",     -7.2612,  112.6453),
    "011": ("KC Surabaya Lakarsantri",      "Surabaya",     -7.3301,  112.6534),
    "012": ("KC Surabaya Mulyorejo",        "Surabaya",     -7.2573,  112.7813),
    "013": ("KC Surabaya Pakal",            "Surabaya",     -7.2178,  112.6425),
    "014": ("KC Surabaya Bubutan",          "Surabaya",     -7.2468,  112.7346),
    "015": ("KC Surabaya Genteng",          "Surabaya",     -7.2568,  112.7398),
    "016": ("KC Surabaya Tambaksari",       "Surabaya",     -7.2545,  112.7642),
    "017": ("KC Surabaya Tenggilis",        "Surabaya",     -7.3234,  112.7734),
    "018": ("KC Surabaya Sawahan",          "Surabaya",     -7.2823,  112.7289),
    "019": ("KC Surabaya Tegalsari",        "Surabaya",     -7.2768,  112.7312),
    "020": ("KC Surabaya Gayungan",         "Surabaya",     -7.3178,  112.7423),
    "021": ("KC Malang Kota",               "Malang",       -7.9666,  112.6326),
    "022": ("KC Malang Blimbing",           "Malang",       -7.9398,  112.6498),
    "023": ("KC Malang Sukun",              "Malang",       -8.0034,  112.6178),
    "024": ("KC Malang Kedungkandang",      "Malang",       -8.0198,  112.6734),
    "025": ("KC Malang Klojen",             "Malang",       -7.9797,  112.6304),
    "026": ("KC Malang Lowokwaru",          "Malang",       -7.9478,  112.6134),
    "027": ("KC Kabupaten Malang Kepanjen", "Kab. Malang",  -8.1284,  112.5698),
    "028": ("KC Sidoarjo Kota",             "Sidoarjo",     -7.4478,  112.7183),
    "029": ("KC Sidoarjo Waru",             "Sidoarjo",     -7.3678,  112.7234),
    "030": ("KC Sidoarjo Buduran",          "Sidoarjo",     -7.4234,  112.7034),
    "031": ("KC Sidoarjo Gedangan",         "Sidoarjo",     -7.3934,  112.7134),
    "032": ("KC Sidoarjo Taman",            "Sidoarjo",     -7.3834,  112.6734),
    "033": ("KC Mojokerto Kota",            "Mojokerto",    -7.4716,  112.4337),
    "034": ("KC Kab. Mojokerto Sooko",      "Kab. Mojokerto",-7.4534, 112.4534),
    "036": ("KC Gresik Kota",               "Gresik",       -7.1557,  112.6524),
    "037": ("KC Gresik Kebomas",            "Gresik",       -7.1734,  112.6434),
    "038": ("KC Gresik Driyorejo",          "Gresik",       -7.3534,  112.5834),
    "039": ("KC Pasuruan Kota",             "Pasuruan",     -7.6446,  112.9078),
    "040": ("KC Kab. Pasuruan Bangil",      "Kab. Pasuruan",-7.5934,  112.7934),
    "041": ("KC Pasuruan Pandaan",          "Kab. Pasuruan",-7.6734,  112.6934),
    "042": ("KC Probolinggo Kota",          "Probolinggo",  -7.7543,  113.2157),
    "044": ("KC Kab. Probolinggo Kraksaan", "Kab. Probolinggo",-7.7534,113.3934),
    "045": ("KC Lumajang",                  "Lumajang",     -8.1296,  113.2221),
    "046": ("KC Jember Kota",               "Jember",       -8.1724,  113.6995),
    "047": ("KC Jember Patrang",            "Jember",       -8.1534,  113.6534),
    "048": ("KC Jember Sumbersari",         "Jember",       -8.1634,  113.7234),
    "049": ("KC Banyuwangi Kota",           "Banyuwangi",   -8.2195,  114.3693),
    "050": ("KC Banyuwangi Rogojampi",      "Banyuwangi",   -8.2934,  114.2934),
    "051": ("KC Situbondo",                 "Situbondo",    -7.7062,  114.0090),
    "052": ("KC Situbondo Asembagus",       "Situbondo",    -7.6934,  114.1534),
    "053": ("KC Bondowoso",                 "Bondowoso",    -7.9107,  113.8195),
    "055": ("KC Jombang Kota",              "Jombang",      -7.5466,  112.2384),
    "057": ("KC Jombang Mojoagung",         "Jombang",      -7.6134,  112.3134),
    "059": ("KC Blitar Kota",               "Blitar",       -8.0956,  112.1614),
    "060": ("KC Kab. Blitar Kanigoro",      "Kab. Blitar",  -8.1534,  112.1934),
    "061": ("KC Kediri Kota",               "Kediri",       -7.8166,  112.0114),
    "063": ("KC Kab. Kediri Pare",          "Kab. Kediri",  -7.7534,  112.1934),
    "066": ("KC Nganjuk",                   "Nganjuk",      -7.6044,  111.9007),
    "067": ("KC Tulungagung Kota",          "Tulungagung",  -8.0650,  111.9029),
    "068": ("KC Tulungagung Campurdarat",   "Tulungagung",  -8.1134,  111.8934),
    "069": ("KC Trenggalek",                "Trenggalek",   -8.0486,  111.7079),
    "070": ("KC Ponorogo",                  "Ponorogo",     -7.8664,  111.4629),
    "071": ("KC Madiun Kota",               "Madiun",       -7.6298,  111.5232),
    "072": ("KC Kab. Madiun Caruban",       "Kab. Madiun",  -7.6534,  111.5734),
    "073": ("KC Ngawi",                     "Ngawi",        -7.4061,  111.4487),
    "074": ("KC Magetan",                   "Magetan",      -7.6477,  111.3291),
    "075": ("KC Pacitan",                   "Pacitan",      -8.1985,  111.1022),
    "076": ("KC Tuban",                     "Tuban",        -6.8985,  112.0523),
    "078": ("KC Lamongan Kota",             "Lamongan",     -7.1178,  112.4178),
    "079": ("KC Lamongan Babat",            "Lamongan",     -7.1034,  112.2534),
    "080": ("KC Bojonegoro Kota",           "Bojonegoro",   -7.1508,  111.8814),
    "082": ("KC Bojonegoro Cepu",           "Bojonegoro",   -7.1534,  111.5934),
    "083": ("KC Bangkalan",                 "Bangkalan",    -7.0434,  112.7534),
    "084": ("KC Sampang",                   "Sampang",      -7.1834,  113.2534),
    "086": ("KC Pamekasan",                 "Pamekasan",    -7.1573,  113.4695),
    "087": ("KC Sumenep Kota",              "Sumenep",      -7.0156,  113.8620),
    "088": ("KC Sumenep Kepulauan",         "Sumenep",      -7.0734,  113.9234),
    "089": ("KC Batu",                      "Batu",         -7.8685,  112.5268),
    "090": ("KC Jombang Ploso",             "Jombang",      -7.4534,  112.1934),
    "091": ("KC Jombang Ngoro",             "Jombang",      -7.6234,  112.3534),
    "092": ("KC Kediri Pesantren",          "Kediri",       -7.8534,  112.0534),
    "093": ("KC Kediri Mojoroto",           "Kediri",       -7.8134,  111.9834),
    "095": ("KC Pasuruan Gempol",           "Kab. Pasuruan",-7.6134,  112.7134),
    "096": ("KC Pasuruan Beji",             "Kab. Pasuruan",-7.6334,  112.6834),
    "099": ("KC Probolinggo Dringu",        "Kab. Probolinggo",-7.7734,113.2534),
    "100": ("KCP Surabaya Kenjeran",        "Surabaya",     -7.2284,  112.7728),
    "101": ("KCP Surabaya Dukuh Kupang",    "Surabaya",     -7.2934,  112.7134),
    "102": ("KCP Surabaya Lontar",          "Surabaya",     -7.2434,  112.6534),
    "103": ("KCP Surabaya Manukan",         "Surabaya",     -7.2334,  112.6634),
    "104": ("KCP Surabaya Sememi",          "Surabaya",     -7.2534,  112.6434),
    "105": ("KCP Surabaya Lidah Wetan",     "Surabaya",     -7.3134,  112.6734),
    "106": ("KCP Surabaya Keputih",         "Surabaya",     -7.2934,  112.7934),
    "107": ("KCP Surabaya Gunung Anyar",    "Surabaya",     -7.3334,  112.8034),
    "108": ("KCP Sidoarjo Porong",          "Sidoarjo",     -7.5434,  112.6934),
    "109": ("KCP Sidoarjo Krian",           "Sidoarjo",     -7.4034,  112.5934),
    "111": ("KCP Malang Sawojajar",         "Malang",       -8.0034,  112.6534),
    "112": ("KCP Malang Dieng",             "Malang",       -7.9634,  112.5934),
    "113": ("KCP Malang Buring",            "Malang",       -8.0234,  112.6634),
    "115": ("KCP Pasuruan Wonorejo",        "Kab. Pasuruan",-7.6534,  112.8834),
    "116": ("KCP Probolinggo Mayangan",     "Probolinggo",  -7.7334,  113.2134),
    "118": ("KCP Kediri Gampengrejo",       "Kab. Kediri",  -7.7934,  112.0534),
    "119": ("KCP Blitar Sananwetan",        "Blitar",       -8.0734,  112.1734),
    "122": ("KCP Jombang Diwek",            "Jombang",      -7.5934,  112.2534),
    "125": ("KCP Bojonegoro Padangan",      "Bojonegoro",   -7.1534,  111.7034),
    "127": ("KCP Lamongan Paciran",         "Lamongan",     -6.8534,  112.2934),
    "128": ("KCP Tuban Palang",             "Tuban",        -7.0134,  111.9934),
    "129": ("KCP Ngawi Paron",              "Ngawi",        -7.4534,  111.5034),
    "131": ("KCP Madiun Mejayan",           "Kab. Madiun",  -7.6034,  111.6834),
    "132": ("KCP Ponorogo Slahung",         "Ponorogo",     -7.9534,  111.4534),
    "133": ("KCP Trenggalek Kampak",        "Trenggalek",   -8.1034,  111.6734),
    "134": ("KCP Tulungagung Ngunut",       "Tulungagung",  -8.0834,  111.9634),
    "136": ("KCP Lumajang Tempeh",          "Lumajang",     -8.2134,  113.1934),
    "137": ("KCP Jember Ambulu",            "Jember",       -8.3434,  113.6134),
    "138": ("KCP Banyuwangi Genteng",       "Banyuwangi",   -8.3334,  114.1634),
    "139": ("KCP Situbondo Panji",          "Situbondo",    -7.7134,  113.9534),
    "140": ("KCP Bondowoso Wonosari",       "Bondowoso",    -7.8934,  113.8834),
    "142": ("KCP Sumenep Lenteng",          "Sumenep",      -7.0634,  113.7434),
    "143": ("KCP Pamekasan Larangan",       "Pamekasan",    -7.1434,  113.5234),
    "144": ("KCP Sampang Camplong",         "Sampang",      -7.2134,  113.3434),
    "145": ("KCP Bangkalan Kamal",          "Bangkalan",    -7.1134,  112.7934),
    "146": ("KCP Gresik Bungah",            "Gresik",       -7.0534,  112.5734),
    "147": ("KCP Mojokerto Dawarblandong",  "Kab. Mojokerto",-7.4034, 112.4034),
    "148": ("KCP Nganjuk Bagor",            "Nganjuk",      -7.5734,  111.9534),
    "149": ("KCP Magetan Maospati",         "Magetan",      -7.6134,  111.3934),
    "151": ("KCP Pacitan Arjosari",         "Pacitan",      -8.1434,  111.1634),
    "152": ("KCP Batu Junrejo",             "Batu",         -7.8934,  112.5534),
    "154": ("KCP Malang Pakis",             "Kab. Malang",  -8.0134,  112.7334),
    "155": ("KCP Malang Tumpang",           "Kab. Malang",  -7.9934,  112.7734),
    "157": ("KCP Malang Singosari",         "Kab. Malang",  -7.8934,  112.6634),
    "159": ("KCP Malang Lawang",            "Kab. Malang",  -7.8534,  112.6934),
    "160": ("KCP Malang Dampit",            "Kab. Malang",  -8.2134,  112.7834),
    "161": ("KCP Malang Turen",             "Kab. Malang",  -8.1534,  112.6934),
    "162": ("KCP Malang Sumberpucung",      "Kab. Malang",  -8.1734,  112.5534),
    "163": ("KCP Malang Gondanglegi",       "Kab. Malang",  -8.1334,  112.6434),
    "164": ("KCP Malang Wagir",             "Kab. Malang",  -8.0334,  112.5534),
    "165": ("KCP Malang Dau",               "Kab. Malang",  -7.9334,  112.5634),
    "168": ("KCP Jember Tanggul",           "Jember",       -8.1934,  113.4634),
    "169": ("KCP Jember Kencong",           "Jember",       -8.4634,  113.5234),
    "170": ("KCP Jember Wuluhan",           "Jember",       -8.3834,  113.5834),
    "171": ("KCP Jember Bangsalsari",       "Jember",       -8.2634,  113.5934),
    "172": ("KCP Banyuwangi Srono",         "Banyuwangi",   -8.3634,  114.2034),
    "173": ("KCP Banyuwangi Muncar",        "Banyuwangi",   -8.4334,  114.3334),
    "174": ("KCP Banyuwangi Tegaldlimo",    "Banyuwangi",   -8.5134,  114.1034),
    "175": ("KCP Banyuwangi Cluring",       "Banyuwangi",   -8.3834,  114.1834),
    "178": ("KCP Probolinggo Paiton",       "Kab. Probolinggo",-7.7034,113.5134),
    "179": ("KCP Probolinggo Besuk",        "Kab. Probolinggo",-7.8034,113.4034),
    "181": ("KCP Pasuruan Nguling",         "Kab. Pasuruan",-7.7134,  112.9934),
    "182": ("KCP Pasuruan Winongan",        "Kab. Pasuruan",-7.6834,  112.8534),
    "183": ("KCP Pasuruan Lekok",           "Kab. Pasuruan",-7.7434,  112.9634),
    "184": ("KCP Pasuruan Kejayan",         "Kab. Pasuruan",-7.6634,  112.7434),
    "185": ("KCP Sidoarjo Candi",           "Sidoarjo",     -7.4734,  112.6934),
    "186": ("KCP Sidoarjo Tanggulangin",    "Sidoarjo",     -7.5034,  112.7234),
    "188": ("KCP Sidoarjo Tarik",           "Sidoarjo",     -7.5234,  112.5934),
    "189": ("KCP Sidoarjo Balongbendo",     "Sidoarjo",     -7.4934,  112.5634),
    "191": ("KCP Gresik Duduksampeyan",     "Gresik",       -7.1934,  112.5534),
    "192": ("KCP Gresik Menganti",          "Gresik",       -7.2534,  112.6134),
    "193": ("KCP Gresik Manyar",            "Gresik",       -7.1234,  112.6334),
    "195": ("KCP Lamongan Ngimbang",        "Lamongan",     -7.3234,  112.2534),
    "196": ("KCP Lamongan Sekaran",         "Lamongan",     -7.2034,  112.3234),
    "197": ("KCP Lamongan Brondong",        "Lamongan",     -6.9034,  112.2834),
    "200": ("KCP Tuban Jatirogo",           "Tuban",        -6.9534,  111.8534),
    "201": ("KCP Tuban Rengel",             "Tuban",        -7.1034,  111.9034),
    "202": ("KCP Bojonegoro Kalitidu",      "Bojonegoro",   -7.1034,  111.7534),
    "203": ("KCP Bojonegoro Ngraho",        "Bojonegoro",   -7.0534,  111.6034),
    "204": ("KCP Ngawi Geneng",             "Ngawi",        -7.5034,  111.4534),
    "205": ("KCP Madiun Dolopo",            "Kab. Madiun",  -7.7534,  111.5234),
    "206": ("KCP Ponorogo Ngrayun",         "Ponorogo",     -8.0534,  111.4034),
    "610": ("KCS Surabaya Syariah",         "Surabaya",     -7.2654,  112.7404),
    "611": ("KCS Surabaya Dharmawangsa",    "Surabaya",     -7.2834,  112.7534),
    "612": ("KCS Surabaya Wonokromo",       "Surabaya",     -7.3098,  112.7342),
    "613": ("KCS Malang Syariah",           "Malang",       -7.9666,  112.6326),
    "614": ("KCS Sidoarjo Syariah",         "Sidoarjo",     -7.4478,  112.7183),
    "615": ("KCS Kediri Syariah",           "Kediri",       -7.8166,  112.0114),
    "616": ("KCS Jember Syariah",           "Jember",       -8.1724,  113.6995),
    "617": ("KCS Banyuwangi Syariah",       "Banyuwangi",   -8.2195,  114.3693),
    "618": ("KCS Madiun Syariah",           "Madiun",       -7.6298,  111.5232),
    "619": ("KCS Pasuruan Syariah",         "Pasuruan",     -7.6446,  112.9078),
    "620": ("KCS Mojokerto Syariah",        "Mojokerto",    -7.4716,  112.4337),
    "621": ("KCS Gresik Syariah",           "Gresik",       -7.1557,  112.6524),
    "622": ("KCS Tuban Syariah",            "Tuban",        -6.8985,  112.0523),
    "623": ("KCS Lamongan Syariah",         "Lamongan",     -7.1178,  112.4178),
    "630": ("KCS Jombang Syariah",          "Jombang",      -7.5466,  112.2384),
    "640": ("KCS Blitar Syariah",           "Blitar",       -8.0956,  112.1614),
    "701": ("UUS Surabaya Gubeng",          "Surabaya",     -7.2654,  112.7404),
    "705": ("UUS Malang",                   "Malang",       -7.9666,  112.6326),
    "714": ("UUS Sidoarjo",                 "Sidoarjo",     -7.4478,  112.7183),
    "717": ("UUS Kediri",                   "Kediri",       -7.8166,  112.0114),
    "718": ("UUS Jember",                   "Jember",       -8.1724,  113.6995),
    "722": ("UUS Mojokerto",                "Mojokerto",    -7.4716,  112.4337),
    "742": ("UUS Banyuwangi",               "Banyuwangi",   -8.2195,  114.3693),
    "743": ("UUS Madiun",                   "Madiun",       -7.6298,  111.5232),
    "762": ("UUS Bojonegoro",               "Bojonegoro",   -7.1508,  111.8814),
    "790": ("UUS Probolinggo",              "Probolinggo",  -7.7543,  113.2157),
    "792": ("UUS Pasuruan",                 "Pasuruan",     -7.6446,  112.9078),
    "802": ("UUS Gresik",                   "Gresik",       -7.1557,  112.6524),
    "805": ("UUS Tuban",                    "Tuban",        -6.8985,  112.0523),
}

FALLBACK = ("KC Surabaya (Lainnya)", "Surabaya", -7.2654, 112.7404)


def run_cabang_map(
    metric: str = "total",
    limit: int = 50,
) -> dict[str, Any]:
    """
    Return list of cabang dengan data geo + metrics untuk map visualization.
    metric: 'total' | 'dormant' | 'avg_saldo' | 'pct_dormant'
    """
    VALID_ORDER = {
        "total":       "total_rekening DESC",
        "dormant":     "dormant DESC",
        "avg_saldo":   "avg_saldo DESC",
        "pct_dormant": "pct_dormant DESC",
    }
    order_clause = VALID_ORDER.get(metric, VALID_ORDER["total"])
    limit = max(1, min(int(limit), 200))

    table = qualified_table()
    sql = f"""
SELECT
    cabang,
    COUNT(*) AS total_rekening,
    SUM(CASE WHEN status_rekening = 0 THEN 1 ELSE 0 END) AS aktif,
    SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) AS dormant,
    ROUND(SUM(CASE WHEN status_rekening = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct_dormant,
    ROUND(AVG(saldo_t0), 0) AS avg_saldo
FROM {table}
GROUP BY cabang
ORDER BY {order_clause}
LIMIT {limit}
""".strip()

    try:
        raw = execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}

    if "error" in raw:
        return raw

    # Enrich dengan koordinat dari master data
    features = []
    for row in raw.get("rows", []):
        kode = str(row.get("cabang", "")).strip()
        name, kota, lat, lng = CABANG_MASTER.get(kode, FALLBACK)
        features.append({
            "cabang":        kode,
            "cabang_name":   name,
            "kota":          kota,
            "lat":           lat,
            "lng":           lng,
            "total":         int(row.get("total_rekening", 0)),
            "aktif":         int(row.get("aktif", 0)),
            "dormant":       int(row.get("dormant", 0)),
            "pct_dormant":   float(row.get("pct_dormant", 0)),
            "avg_saldo":     float(row.get("avg_saldo", 0)),
        })

    return {
        "visualization": "map",
        "metric":        metric,
        "row_count":     len(features),
        "features":      features,
    }
