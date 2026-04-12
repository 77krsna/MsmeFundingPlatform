# oracle/app/api/routes/orders.py
"""
API routes for orders
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import GeMOrder, MSME, GSTNVerification, BlockchainTransaction
from pydantic import BaseModel, Field

router = APIRouter()


# ============================================
# PYDANTIC SCHEMAS
# ============================================

class OrderResponse(BaseModel):
    """Order response schema"""
    id: str
    gem_order_id: str
    contract_address: Optional[str] = None
    order_amount: float
    order_date: datetime
    delivery_deadline: datetime
    buyer_organization: Optional[str] = None
    product_category: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Paginated order list response"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


# ============================================
# ENDPOINTS
# ============================================

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all orders with pagination
    """
    query = db.query(GeMOrder)
    
    # Filter by status if provided
    if status:
        query = query.filter(GeMOrder.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    orders = query.order_by(desc(GeMOrder.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response format
    order_list = []
    for order in orders:
        order_list.append({
            "id": str(order.id),
            "gem_order_id": order.gem_order_id,
            "contract_address": order.contract_address,
            "order_amount": float(order.order_amount),
            "order_date": order.order_date,
            "delivery_deadline": order.delivery_deadline,
            "buyer_organization": order.buyer_organization,
            "product_category": order.product_category,
            "status": order.status,
            "created_at": order.created_at
        })
    
    return {
        "orders": order_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/stats/summary")
async def order_statistics(db: Session = Depends(get_db)):
    """Get order statistics"""
    total = db.query(GeMOrder).count()
    
    by_status = {}
    statuses = ['DETECTED', 'CONTRACT_CREATED', 'FUNDED', 'DELIVERED', 'REPAID', 'DEFAULTED']
    
    for status_val in statuses:
        count = db.query(GeMOrder).filter_by(status=status_val).count()
        by_status[status_val] = count
    
    # Calculate total volume
    total_volume = db.query(func.sum(GeMOrder.order_amount)).scalar() or 0
    
    return {
        "total_orders": total,
        "by_status": by_status,
        "total_volume": float(total_volume)
    }


@router.get("/{order_id}")
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get specific order details"""
    from sqlalchemy import or_
    
    # First try as gem_order_id (string), then as UUID
    order = db.query(GeMOrder).filter(
        GeMOrder.gem_order_id == order_id
    ).first()
    
    # If not found and order_id looks like UUID, try UUID search
    if not order:
        try:
            import uuid
            uuid_obj = uuid.UUID(order_id)
            order = db.query(GeMOrder).filter(
                GeMOrder.id == uuid_obj
            ).first()
        except (ValueError, AttributeError):
            pass
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": str(order.id),
        "gem_order_id": order.gem_order_id,
        "contract_address": order.contract_address,
        "order_amount": float(order.order_amount),
        "order_date": order.order_date,
        "delivery_deadline": order.delivery_deadline,
        "buyer_organization": order.buyer_organization,
        "product_category": order.product_category,
        "status": order.status,
        "created_at": order.created_at
    }