"""
SQLite compatibility patch for ChromaDB on CAI (Cloudera AI Workbench).

CAI sessions run Python 3.10 with an older SQLite (<3.35.0).
ChromaDB requires SQLite >= 3.35.0. This module replaces the built-in
sqlite3 with pysqlite3-binary before chromadb is imported.

Import this module at the top of any file that uses chromadb.
"""
from __future__ import annotations

import sys


def patch_sqlite() -> None:
    try:
        import pysqlite3  # type: ignore
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass  # pysqlite3 not installed — proceed with system sqlite3
