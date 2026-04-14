# oracle/app/api/routes/investors.py
"""
API routes for investor operations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import GeMOrder

router = APIRouter()


@router.get("/opportunities")
async def list_investment_opportunities(db: Session = Depends(get_db)):
    """List available investment opportunities"""
    
    # Use status values that actually exist in database
    orders = db.query(GeMOrder).filter(
        GeMOrder.status.in_(['CONTRACT_CREATED', 'DETECTED', 'FUNDED'])
    ).limit(20).all()
    
    opportunities = []
    for order in orders:
        opportunities.append({
            "order_id": str(order.id),
            "gem_order_id": order.gem_order_id,
            "order_amount": float(order.order_amount),
            "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None,
            "buyer_organization": order.buyer_organization or "Government Department",
            "product_category": order.product_category or "General",
            "status": order.status,
            "risk_score": 5.0,
            "estimated_return": 10.0
        })
    
    return opportunities


@router.get("/portfolio/{wallet_address}")
async def get_investor_portfolio(wallet_address: str):
    """Get investor's portfolio"""
    
    return {
        "wallet_address": wallet_address,
        "total_invested": 0.0,
        "total_returns": 0.0,
        "active_investments": 0,
        "investments": []
    }
from pydantic import BaseModel
from typing import Optional
import os, requests
from sqlalchemy import text
from datetime import datetime

RPC_URL = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:8545")

def _rpc(method: str, params=None):
    payload = {"jsonrpc":"2.0","id":1,"method":method,"params":params or []}
    r = requests.post(RPC_URL, json=payload, timeout=10)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]

class InvestRequest(BaseModel):
    order_id: str          # UUID string from opportunities list
    eth_wei: int = 1
    investor_wallet: Optional[str] = None

@router.post("/invest")
def invest(req: InvestRequest, db: Session = Depends(get_db)):
    # 1) load order by UUID (your opportunities returns order_id UUID)
    row = db.execute(
        text("SELECT id, status FROM gem_orders WHERE id::text=:id"),
        {"id": req.order_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Order not found")

    order_uuid, status = row

    # Don't allow investing again if already funded/repaid/defaulted
    if status in ("FUNDED", "REPAID", "DEFAULTED"):
        raise HTTPException(status_code=409, detail=f"Order already {status}")

    # 2) Real tx on Hardhat (proof of blockchain)
    accounts = _rpc("eth_accounts")
    if len(accounts) < 2:
        raise HTTPException(status_code=500, detail="Hardhat accounts not available")

    tx_hash = _rpc("eth_sendTransaction", [{
        "from": accounts[0],
        "to": accounts[1],
        "value": hex(int(req.eth_wei))
    }])

    # 3) Store tx hash (best-effort; only if columns exist)
    cols = {r[0] for r in db.execute(text("""
      SELECT column_name FROM information_schema.columns
      WHERE table_name='blockchain_transactions'
    """)).fetchall()}

    insert_data = {}
    if "tx_hash" in cols: insert_data["tx_hash"] = tx_hash
    if "order_id" in cols: insert_data["order_id"] = order_uuid
    if "created_at" in cols: insert_data["created_at"] = datetime.utcnow()
    if "investor_wallet" in cols and req.investor_wallet:
        insert_data["investor_wallet"] = req.investor_wallet

    if insert_data:
        keys = ", ".join(insert_data.keys())
        vals = ", ".join([f":{k}" for k in insert_data.keys()])
        db.execute(text(f"INSERT INTO blockchain_transactions ({keys}) VALUES ({vals})"), insert_data)

    # 4) Update status to FUNDED so UI changes
    db.execute(text("UPDATE gem_orders SET status='FUNDED' WHERE id=:id"), {"id": order_uuid})
    db.commit()

    return {"ok": True, "tx_hash": tx_hash, "new_status": "FUNDED", "order_id": str(order_uuid)}