"""GUARD TEST — the alembic migration chain must produce the SAME schema as
`Base.metadata.create_all`.

This is the root-cause fix for the drift that abandoned the old chain: if a model
changes without a matching migration (or vice versa), the two schema sources
diverge and this test fails in CI — so drift can never be merged silently. It
also legitimizes keeping test fixtures on `create_all` (fast), because parity is
guaranteed here.

Builds one DB via `alembic upgrade head` (subprocess, so DATABASE_URL points at a
throwaway) and one via `create_all`, then compares tables / columns (type,
nullable, default, pk) / foreign keys / indexes+unique — order-insensitive.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine

import app.models  # noqa: F401 — registers all models with Base.metadata
from app.db.base import Base

BACKEND = Path(__file__).resolve().parent.parent


def _introspect(db_path: Path) -> dict:
    con = sqlite3.connect(str(db_path))
    tabs = [
        r[0]
        for r in con.execute(
            "select name from sqlite_master where type='table' "
            "and name not like 'sqlite_%' and name != 'alembic_version'"
        ).fetchall()
    ]
    schema = {}
    for t in tabs:
        cols = frozenset(
            (r[1], r[2].upper(), r[3], (r[4] or ""), r[5])  # name, type, notnull, default, pk
            for r in con.execute(f"PRAGMA table_info('{t}')").fetchall()
        )
        fks = frozenset(
            (r[3], r[2], r[4], r[6])  # from, table, to, on_delete
            for r in con.execute(f"PRAGMA foreign_key_list('{t}')").fetchall()
        )
        idxlist = con.execute(f"PRAGMA index_list('{t}')").fetchall()  # fetchall first (cursor safety)
        idx = frozenset(
            (tuple(sorted(x[2] for x in con.execute(f"PRAGMA index_info('{r[1]}')").fetchall())), r[2])
            for r in idxlist
        )
        schema[t] = (cols, fks, idx)
    con.close()
    return schema


def test_migration_schema_matches_create_all(tmp_path):
    mig_db = tmp_path / "mig.db"
    ca_db = tmp_path / "ca.db"

    # 1) Build via the migration chain (subprocess so env.py reads DATABASE_URL fresh).
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{mig_db}"}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND), env=env, check=True, capture_output=True, text=True,
    )

    # 2) Build via create_all (in-process, sync engine).
    eng = create_engine(f"sqlite:///{ca_db}")
    Base.metadata.create_all(eng)
    eng.dispose()

    mig = _introspect(mig_db)
    ca = _introspect(ca_db)

    # Same table set.
    assert set(mig) == set(ca), (
        f"table set differs — only in migration: {set(mig) - set(ca)}; "
        f"only in create_all: {set(ca) - set(mig)}"
    )
    # Same structure per table (columns/types/nullable/default/pk, FKs, indexes/unique).
    diffs = []
    for t in sorted(mig):
        cm, fm, im = mig[t]
        cc, fc, ic = ca[t]
        if cm != cc:
            diffs.append(f"{t} COLUMNS: mig-ca={cm - cc} ca-mig={cc - cm}")
        if fm != fc:
            diffs.append(f"{t} FKS: mig-ca={fm - fc} ca-mig={fc - fm}")
        if im != ic:
            diffs.append(f"{t} INDEXES/UNIQUE: mig-ca={im - ic} ca-mig={ic - im}")
    assert not diffs, "migration schema != create_all schema:\n" + "\n".join(diffs)
