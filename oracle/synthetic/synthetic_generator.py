import os
import time
import random
import string
import uuid
import decimal
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from faker import Faker

from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import DateTime, Date, JSON as SAJSON

load_dotenv()
fake = Faker("en_IN")

ORDER_FLOW = ["DETECTED", "CONTRACT_CREATED", "FUNDED", "DELIVERED", "REPAID", "DEFAULTED"]


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def rand_str(n: int = 12) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def rand_eth_address() -> str:
    return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(40))


def get_models():
    from app.database import SessionLocal  # type: ignore
    import app.models as models  # type: ignore
    import inspect as pyinspect

    tab_to_model = {}
    for _, obj in pyinspect.getmembers(models):
        if hasattr(obj, "__tablename__"):
            tab_to_model[obj.__tablename__] = obj
    return SessionLocal, tab_to_model


def pytype_of(col) -> Optional[type]:
    try:
        return col.type.python_type
    except Exception:
        return None


def guess_dt(col_name: str) -> datetime:
    n = col_name.lower()
    now = utcnow_naive()
    if "deadline" in n:
        return now + timedelta(days=random.randint(3, 30))
    if "date" in n:
        return now - timedelta(days=random.randint(0, 10))
    return now


def guess_value(col, col_name: str) -> Any:
    n = col_name.lower()
    t = col.type
    p = pytype_of(col)

    # Strong type-based
    if isinstance(t, (DateTime, Date)):
        return guess_dt(col_name)

    if isinstance(t, SAJSON):
        return {"demo": True, "generated_at": utcnow_naive().isoformat(), "ref": rand_str(8)}

    if p is uuid.UUID:
        return uuid.uuid4()

    if p is decimal.Decimal:
        return decimal.Decimal(str(round(random.uniform(10000, 500000), 2)))

    # Name-based
    if n.endswith("_at") or "timestamp" in n or "deadline" in n or "date" in n:
        return guess_dt(col_name)

    if "contract_address" in n or ("address" in n and ("wallet" in n or "eth" in n)):
        return rand_eth_address()

    if "tx_hash" in n or "transaction_hash" in n:
        return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))

    if "email" in n:
        return f"{fake.user_name()}.{int(time.time())}@demo.local"

    if "phone" in n or "mobile" in n:
        return fake.msisdn()[:10]

    if "gst" in n:
        return "27" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(13))

    if "pan" in n:
        return "".join(random.choice(string.ascii_uppercase) for _ in range(5)) + \
               "".join(random.choice(string.digits) for _ in range(4)) + \
               random.choice(string.ascii_uppercase)

    if "status" in n:
        return random.choice(ORDER_FLOW)

    if "amount" in n or "value" in n or "volume" in n or "price" in n:
        return round(random.uniform(10000, 500000), 2)

    if "name" in n:
        if "org" in n or "organization" in n or "company" in n or "business" in n:
            return fake.company()
        return fake.name()

    # Fallback by python type
    if p is int:
        return random.randint(1, 999999)
    if p is float:
        return round(random.uniform(1, 999999), 2)
    if p is bool:
        return random.choice([True, False])

    return fake.word()[:40]


def choose_fk_value(session: Session, fk) -> Optional[Any]:
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
    mapper = sa_inspect(Model)
    obj = Model()

    for col in mapper.columns:
        key = col.key

        if key in overrides:
            setattr(obj, key, overrides[key])
            continue

        if col.primary_key:
            continue

        if col.default is not None or col.server_default is not None:
            continue

        if col.nullable:
            continue

        # Foreign key: pick existing
        if col.foreign_keys:
            picked = None
            for fk in col.foreign_keys:
                picked = choose_fk_value(session, fk)
                if picked is not None:
                    break
            if picked is not None:
                setattr(obj, key, picked)
                continue

        setattr(obj, key, guess_value(col, key))

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def advance_some_orders(session: Session):
    try:
        cols = session.execute(text("""
          SELECT column_name
          FROM information_schema.columns
          WHERE table_name='gem_orders'
        """)).fetchall()
        colnames = {c[0] for c in cols}

        status_col = "status" if "status" in colnames else ("order_status" if "order_status" in colnames else None)
        if not status_col:
            return

        rows = session.execute(text(f"""
          SELECT id, {status_col}
          FROM gem_orders
          ORDER BY random()
          LIMIT 8
        """)).fetchall()

        for oid, st in rows:
            if st in ORDER_FLOW:
                i = ORDER_FLOW.index(st)
                new_status = ORDER_FLOW[min(i + 1, len(ORDER_FLOW) - 1)]
                # add some randomness so not all orders end same
                if new_status == "REPAID" and random.random() < 0.2:
                    new_status = "DEFAULTED"
            else:
                new_status = random.choice(ORDER_FLOW)

            session.execute(text(f"UPDATE gem_orders SET {status_col}=:s WHERE id=:id"), {"s": new_status, "id": oid})
        session.commit()
    except Exception:
        session.rollback()


def create_demo_cycle(verbose: bool = True):
    SessionLocal, tab_to_model = get_models()

    User = tab_to_model.get("users")
    MSME = tab_to_model.get("msmes")
    Order = tab_to_model.get("gem_orders")
    VATx = tab_to_model.get("virtual_account_transactions")
    BTx = tab_to_model.get("blockchain_transactions")
    GSTV = tab_to_model.get("gstn_verifications")
    OJob = tab_to_model.get("oracle_jobs")

    with SessionLocal() as session:
        core = {"user_msme": None, "user_investor": None, "msme": None}

        if User:
            user_cols = {c.key for c in sa_inspect(User).columns}
            msme_over = {"role": "MSME"} if "role" in user_cols else {}
            inv_over = {"role": "INVESTOR"} if "role" in user_cols else {}
            core["user_msme"] = ensure_row(session, User, msme_over)
            core["user_investor"] = ensure_row(session, User, inv_over)

        if MSME:
            msme_cols = {c.key for c in sa_inspect(MSME).columns}
            over = {}
            if "user_id" in msme_cols and core["user_msme"] is not None and hasattr(core["user_msme"], "id"):
                over["user_id"] = core["user_msme"].id
            core["msme"] = ensure_row(session, MSME, over)

        if Order:
            order_cols = {c.key for c in sa_inspect(Order).columns}
            for _ in range(random.randint(2, 5)):
                over = {}

                if "status" in order_cols:
                    over["status"] = "DETECTED"
                elif "order_status" in order_cols:
                    over["order_status"] = "DETECTED"

                if "msme_id" in order_cols and core["msme"] is not None and hasattr(core["msme"], "id"):
                    over["msme_id"] = core["msme"].id

                if "investor_id" in order_cols and core["user_investor"] is not None and hasattr(core["user_investor"], "id"):
                    over["investor_id"] = core["user_investor"].id

                if "gem_order_id" in order_cols:
                    over["gem_order_id"] = f"GEM-{int(time.time())}-{random.randint(100,999)}"

                if "order_amount" in order_cols:
                    over["order_amount"] = round(random.uniform(20000, 300000), 2)

                if "order_date" in order_cols:
                    over["order_date"] = utcnow_naive() - timedelta(days=random.randint(0, 10))

                if "delivery_deadline" in order_cols:
                    over["delivery_deadline"] = utcnow_naive() + timedelta(days=random.randint(5, 30))

                ensure_row(session, Order, over)

        if VATx:
            for _ in range(random.randint(1, 3)):
                ensure_row(session, VATx, {})

        if BTx:
            for _ in range(random.randint(1, 3)):
                ensure_row(session, BTx, {})

        if GSTV and random.random() < 0.5:
            ensure_row(session, GSTV, {})

        if OJob and random.random() < 0.5:
            ensure_row(session, OJob, {})

        advance_some_orders(session)

        if verbose:
            stats = {}
            for t in ["users", "msmes", "gem_orders", "virtual_account_transactions", "blockchain_transactions"]:
                try:
                    stats[t] = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                except Exception:
                    pass
            print(f"[{datetime.now().strftime('%H:%M:%S')}] " + " ".join([f"{k}={v}" for k, v in stats.items()]))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=int, default=60)
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
            print("ERROR:", e)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
