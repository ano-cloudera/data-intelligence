"""
Test koneksi Impala — jalankan sebelum deploy MCP server aggregation.

Usage:
    python test_impala_connection.py

Atau override via env vars tanpa ubah file ini:
    IMPALA_HOST=host-lain CDP_USER=user CDP_PASS=pass python test_impala_connection.py

Untuk on-premises dengan port berbeda:
    IMPALA_HOST=impala.internal IMPALA_PORT=28000 CDP_USER=user CDP_PASS=pass python test_impala_connection.py
"""

import os
import sys
import time

# ---------------------------------------------------------------------------
# Konfigurasi — edit di sini atau override via env vars
# ---------------------------------------------------------------------------
IMPALA_HOST      = os.getenv("IMPALA_HOST",      "coordinator-default-impala-aws.dw-xxx.cloudera.site")
IMPALA_PORT      = int(os.getenv("IMPALA_PORT",  "443"))
IMPALA_HTTP_PATH = os.getenv("IMPALA_HTTP_PATH", "cliservice")
CDP_USER         = os.getenv("CDP_USER",         "<cdp-username>")
CDP_PASS         = os.getenv("CDP_PASS",         "<cdp-password>")
DB_NAME          = os.getenv("DB_NAME",          "cai_sdx_se_indonesia")
AGGREGATION_TABLE = os.getenv("AGGREGATION_TABLE", "customer_aggregation")

# SSL & auth — ubah ke False / GSSAPI untuk on-prem Kerberos
USE_SSL          = os.getenv("IMPALA_USE_SSL",   "true").lower() == "true"
AUTH_MECHANISM   = os.getenv("IMPALA_AUTH",      "PLAIN")  # PLAIN (LDAP/Knox) atau GSSAPI (Kerberos)
# ---------------------------------------------------------------------------


def separator(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_placeholder(value: str, name: str) -> None:
    if value.startswith("<") and value.endswith(">"):
        print(f"[ERROR] {name} masih placeholder: '{value}'")
        print("        Set via env var atau edit langsung di file ini.")
        sys.exit(1)


def main() -> None:
    separator("Impala Connection Test")

    # Validasi placeholder
    check_placeholder(IMPALA_HOST, "IMPALA_HOST")
    check_placeholder(CDP_USER,    "CDP_USER")
    check_placeholder(CDP_PASS,    "CDP_PASS")

    print(f"  Host      : {IMPALA_HOST}")
    print(f"  Port      : {IMPALA_PORT}")
    print(f"  HTTP Path : {IMPALA_HTTP_PATH}")
    print(f"  User      : {CDP_USER}")
    print(f"  Database  : {DB_NAME}")
    print(f"  Table     : {AGGREGATION_TABLE}")
    print(f"  SSL       : {USE_SSL}")
    print(f"  Auth      : {AUTH_MECHANISM}")

    # --- Import check ---
    separator("Step 1: Import impyla")
    try:
        from impala.dbapi import connect
        print("[OK] impyla tersedia")
    except ImportError:
        print("[ERROR] impyla tidak terinstall.")
        print("        Jalankan: pip install impyla")
        sys.exit(1)

    # --- Koneksi ---
    separator("Step 2: Buka koneksi")
    t0 = time.time()
    try:
        conn = connect(
            host=IMPALA_HOST,
            port=IMPALA_PORT,
            database=DB_NAME,
            user=CDP_USER,
            password=CDP_PASS,
            use_ssl=USE_SSL,
            auth_mechanism=AUTH_MECHANISM,
            http_path=IMPALA_HTTP_PATH,
            use_http_transport=True,
        )
        elapsed = time.time() - t0
        print(f"[OK] Koneksi berhasil ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[ERROR] Koneksi gagal ({elapsed:.2f}s)")
        print(f"        {type(e).__name__}: {e}")
        print()
        print("Troubleshooting:")
        print("  - Cek IMPALA_HOST & IMPALA_PORT")
        print("  - Cek CDP_USER & CDP_PASS")
        print("  - Untuk on-prem Knox: IMPALA_PORT=28000, IMPALA_USE_SSL=true")
        print("  - Untuk on-prem direct: IMPALA_PORT=21050, IMPALA_USE_SSL=false")
        print("  - Untuk Kerberos: IMPALA_AUTH=GSSAPI")
        sys.exit(1)

    with conn:
        cursor = conn.cursor()

        # --- Ping database ---
        separator("Step 3: Ping database (SELECT 1)")
        try:
            cursor.execute("SELECT 1 AS ping")
            row = cursor.fetchone()
            print(f"[OK] SELECT 1 → {row}")
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        # --- List tables ---
        separator(f"Step 4: Cek database '{DB_NAME}'")
        try:
            cursor.execute(f"SHOW TABLES IN {DB_NAME}")
            tables = [r[0] for r in cursor.fetchall()]
            print(f"[OK] {len(tables)} tabel ditemukan:")
            for t in tables:
                marker = " ← TARGET" if t == AGGREGATION_TABLE else ""
                print(f"     - {t}{marker}")
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        # --- Cek tabel target ---
        separator(f"Step 5: Cek tabel '{AGGREGATION_TABLE}'")
        full_table = f"{DB_NAME}.{AGGREGATION_TABLE}"
        if AGGREGATION_TABLE not in tables:
            print(f"[WARN] Tabel '{AGGREGATION_TABLE}' belum ada di database '{DB_NAME}'.")
            print(f"       Jalankan DDL di ask-data/sql/impala_customer_aggregation_ddl.sql dulu.")
        else:
            try:
                cursor.execute(f"SELECT COUNT(*) AS total FROM {full_table}")
                count = cursor.fetchone()[0]
                print(f"[OK] Tabel ada — total rows: {count}")

                cursor.execute(f"SELECT * FROM {full_table} LIMIT 2")
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                print(f"[OK] Kolom ({len(cols)}): {', '.join(cols)}")
                print(f"[OK] Sample data ({len(rows)} rows):")
                for r in rows:
                    print(f"     {dict(zip(cols, r))}")
            except Exception as e:
                print(f"[ERROR] Query gagal: {e}")
                sys.exit(1)

        cursor.close()

    separator("RESULT")
    print("[OK] Semua test passed — koneksi Impala siap dipakai.")
    print()


if __name__ == "__main__":
    main()
