import os
import re
import time
import json
import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from faker import Faker

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text
from sqlalchemy.orm import Session

# SQLAlchemy column types for reliable detection
from sqlalchemy.sql.sqltypes import DateTime, Date, JSON as SAJSON


load_dotenv()
fake = Faker("en_IN")

ORDER_FLOW = ["DETECTED", "CONTRACT_CREATED", "FUNDED", "DELIVERED", "REPAID", "DEFAULTED"]


def utcnow_naive() -> datetime:
    """Return UTC now as naive datetime (Postgres often expects naive in many configs)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def rand_str(n: int = 12) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def rand_eth_address() -> str:
    return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(40))


def looks_like_uuid(s: str) -> bool:
    try:
        uuid.UUID(str(s))
        return True
    except Exception:
        return False


def get_models():
    """
    Import your app SessionLocal and models.
    NOTE: this file must be run as a module from oracle root:
      python -m synthetic.synthetic_generator ...
    """
    from app.database import SessionLocal  # type: ignore
    import app.models as models  # type: ignore
    import inspect as pyinspect

    tab_to_model = {}
    for _, obj in pyinspect.getmembers(models):
        if hasattr(obj, "__tablename__"):
            tab_to_model[obj.__tablename__] = obj

    return SessionLocal, tab_to_model


def detect_column_python_type(col) -> Optional[type]:
    try:
        return col.type.python_type  # may raise NotImplementedError
    except Exception:
        return None


def guess_datetime_for(name: str) -> datetime:
    n = name.lower()
    now = utcnow_naive()

    if "deadline" in n:
        return now + timedelta(days=random.randint(3, 30))

    # order_date, invoice_date, etc.
    if "date" in n:
        return now - timedelta(days=random.randint(0, 10))

    # created_at, updated_at, *_at, timestamp
    return now


def guess_value(col, col_name: str) -> Any:
    """
    Guess a reasonable value for a column using both name + SQLAlchemy type.
    """
    n = col_name.lower()
    coltype = col.type
    pytype = detect_column_python_type(col)

    # Strong type-based handling first
    if isinstance(coltype, (DateTime, Date)):
        return guess_datetime_for(col_name)

    if isinstance(coltype, SAJSON):
        return {"demo": True, "generated_at": utcnow_naive().isoformat(), "key": rand_str(8)}

    # Name-based handling (works even if type is not introspectable)
    if n.endswith("_at") or "timestamp" in n or "deadline" in n or "date" in n:
        return guess_datetime_for(col_name)

    if "address" in n and ("contract" in n or "wallet" in n or "eth" in n or "web3" in n):
        return rand_eth_address()

    if "email" in n:
        return f"{fake.user_name()}.{int(time.time())}@demo.local"

    if "phone" in n or "mobile" in n:
        return fake.msisdn()[:10]

    if "name" in n:
        if "company" in n or "business" in n or "org" in n or "organization" in n:
            return fake.company()
        return fake.name()

    if "gst" in n:
        # demo-like GST number, not necessarily valid
        return "27" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(13))

    if "pan" in n:
        return "".join(random.choice(string.ascii_uppercase) for _ in range(5)) + \
               "".join(random.choice(string.digits) for _ in range(4)) + \
               random.choice(string.ascii_uppercase)

    if "status" in n:
        return random.choice(ORDER_FLOW)

    if "amount" in n or "volume" in n or "value" in n or "price" in n:
        return round(random.uniform(10000, 500000), 2)

    if n.endswith("_id"):
        # Often UUID FK; let FK resolver try first elsewhere; fallback here.
        return uuid.uuid4()

    # Fallback by python type
    if pytype is int:
        return random.randint(1, 999999)
    if pytype is float:
        return round(random.uniform(1, 999999), 2)
    if pytype is bool:
        return random.choice([True, False])

    # Default string
    return fake.word()[:40]


def choose_fk_value(session: Session, fk) -> Optional[Any]:
    """
    Try to pick an existing row id from the referenced table for a FK.
    Works for UUID/int PK patterns.
    """
    try:
        target_col = fk.column
        target_table = target_col.table.name
        target_pk = target_col.name

        row = session.execute(
            text(f"SELECT {target_pk} FROM {target_table} ORDER BY random() LIMIT 1")
        ).fetchone()

        return row[0] if row else None
    except Exception:
        return None


def ensure_row(session: Session, Model, overrides: Dict[str, Any]) -> Any:
    """
    Create one row for Model, filling required (non-nullable) columns with sensible defaults.
    Respects overrides.
    """
    mapper = sa_inspect(Model)
    obj = Model()

    # Build a quick set of column names
    for col in mapper.columns:
        key = col.key

        # Explicit overrides win
        if key in overrides:
            setattr(obj, key, overrides[key])
            continue

        # Skip primary key (usually default uuid4/autoincrement)
        if col.primary_key:
            continue

        # If column has python-side default or server default, we can skip
        if col.default is not None or col.server_default is not None:
            continue

        # Nullable columns can be skipped safely
        if col.nullable:
            continue

        # Foreign key handling: try pick existing
        if col.foreign_keys:
            picked = None
            for fk in col.foreign_keys:
                picked = choose_fk_value(session, fk)
                if picked is not None:
                    break
            if picked is not None:
                setattr(obj, key, picked)
                continue

        # Required field: guess value
        setattr(obj, key, guess_value(col, key))

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def advance_some_orders(session: Session):
    """
    Advance gem_orders status for a few rows each run.
    Supports status column names: status or order_status.
    """
    try:
        cols = session.execute(text("""
          SELECT column_name
          FROM information_schema.columns
          WHERE table_name='gem_orders'
        """)).fetchall()
        colnames = {c[0] for c in cols}

        status_col = None
        if "status" in colnames:
            status_col = "status"
        elif "order_status" in colnames:
            status_col = "order_status"

        if not status_col:
            return

        rows = session.execute(text(f"""
          SELECT id, {status_col}
          FROM gem_orders
          ORDER BY random()
          LIMIT 5
        """)).fetchall()

        for oid, st in rows:
            if st in ORDER_FLOW:
                i = ORDER_FLOW.index(st)
                new_status = ORDER_FLOW[min(i + 1, len(ORDER_FLOW) - 1)]
            else:
                new_status = random.choice(ORDER_FLOW)

            session.execute(
                text(f"UPDATE gem_orders SET {status_col}=:s WHERE id=:id"),
                {"s": new_status, "id": oid},
            )

        session.commit()
    except Exception:
        session.rollback()


def ensure_core_entities(session: Session, tab_to_model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure base entities exist: users, msmes.
    Returns created/selected entities for linking.
    """
    User = tab_to_model.get("users")
    MSME = tab_to_model.get("msmes")

    created = {"user_msme": None, "user_investor": None, "msme": None}

    # Create a couple users
    if User:
        user_cols = {c.key for c in sa_inspect(User).columns}

        msme_over = {}
        inv_over = {}
        if "role" in user_cols:
            msme_over["role"] = "MSME"
            inv_over["role"] = "INVESTOR"

        created["user_msme"] = ensure_row(session, User, msme_over)
        created["user_investor"] = ensure_row(session, User, inv_over)

    # Create MSME row and link to user if possible
    if MSME:
        msme_cols = {c.key for c in sa_inspect(MSME).columns}
        msme_over = {}

        if "user_id" in msme_cols and created["user_msme"] is not None and hasattr(created["user_msme"], "id"):
            msme_over["user_id"] = created["user_msme"].id

        created["msme"] = ensure_row(session, MSME, msme_over)

    return created


def create_demo_cycle(verbose: bool = True):
    SessionLocal, tab_to_model = get_models()

    Order = tab_to_model.get("gem_orders")
    GSTV = tab_to_model.get("gstn_verifications")
    OJob = tab_to_model.get("oracle_jobs")
    VATx = tab_to_model.get("virtual_account_transactions")
    BTx = tab_to_model.get("blockchain_transactions")

    with SessionLocal() as session:
        # Base entities
        core = ensure_core_entities(session, tab_to_model)

        # Orders
        if Order:
            order_cols = {c.key for c in sa_inspect(Order).columns}
            for _ in range(random.randint(1, 3)):
                over = {}

                # Use status flow starting point
                if "status" in order_cols:
                    over["status"] = "DETECTED"
                elif "order_status" in order_cols:
                    over["order_status"] = "DETECTED"

                # Link to MSME if possible
                if "msme_id" in order_cols and core["msme"] is not None and hasattr(core["msme"], "id"):
                    over["msme_id"] = core["msme"].id

                # Link investor if column exists
                if "investor_id" in order_cols and core["user_investor"] is not None and hasattr(core["user_investor"], "id"):
                    over["investor_id"] = core["user_investor"].id

                # Make sure order_date/deadline are proper datetimes if such columns exist
                if "order_date" in order_cols:
                    over["order_date"] = utcnow_naive() - timedelta(days=random.randint(0, 7))
                if "delivery_deadline" in order_cols:
                    over["delivery_deadline"] = utcnow_naive() + timedelta(days=random.randint(5, 25))

                # Some realistic-ish values
                if "order_amount" in order_cols:
                    over["order_amount"] = round(random.uniform(20000, 250000), 2)
                if "gem_order_id" in order_cols:
                    over["gem_order_id"] = f"GEM-{int(time.time())}-{random.randint(100,999)}"

                ensure_row(session, Order, over)

        # GST verification row
        if GSTV:
            gcols = {c.key for c in sa_inspect(GSTV).columns}
            over = {}
            if "msme_id" in gcols and core["msme"] is not None and hasattr(core["msme"], "id"):
                over["msme_id"] = core["msme"].id
            ensure_row(session, GSTV, over)

        # Oracle jobs
        if OJob:
            ensure_row(session, OJob, {})

        # Virtual account transactions
        if VATx:
            ensure_row(session, VATx, {})

        # Blockchain transactions
        if BTx:
            bcols = {c.key for c in sa_inspect(BTx).columns}
            over = {}
            if "tx_hash" in bcols:
                over["tx_hash"] = "0x" + rand_str(64).lower()
            if "contract_address" in bcols:
                over["contract_address"] = rand_eth_address()
            ensure_row(session, BTx, over)

        # Advance some orders each cycle
        advance_some_orders(session)

        # Print stats
        if verbose:
            stats = {}
            for t in ["users", "msmes", "gem_orders", "blockchain_transactions", "virtual_account_transactions", "gstn_verifications", "oracle_jobs"]:
                try:
                    stats[t] = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                except Exception:
                    pass
            print(f"[{datetime.now().strftime('%H:%M:%S')}] " +
                  " ".join([f"{k}={v}" for k, v in stats.items()]))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=int, default=60, help="seconds between cycles")
    p.add_argument("--once", action="store_true")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if args.once:
        create_demo_cycle(verbose=(not args.quiet))
        return

    while True:
        try:
            create_demo_cycle(verbose=(not args.quiet))
        except Exception as e:
            # Keep running even if one cycle fails
            print("ERROR:", e)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()