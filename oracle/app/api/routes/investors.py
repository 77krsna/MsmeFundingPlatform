# oracle/app/api/routes/investors.py
"""
API routes for investor operations
"""

from fastapi import APIRouter, Depends
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