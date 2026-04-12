# oracle/app/api/routes/msme.py
"""
API routes for MSME operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models import MSME, User

router = APIRouter()


# ============================================
# SCHEMAS
# ============================================

class MSMECreate(BaseModel):
    """Schema for creating MSME"""
    wallet_address: str = Field(..., min_length=42, max_length=42)
    company_name: str = Field(..., min_length=1, max_length=255)
    gstn: str = Field(..., min_length=15, max_length=15)
    pan: str = Field(..., min_length=10, max_length=10)
    email: Optional[str] = None


# ============================================
# ENDPOINTS
# ============================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_msme(msme_data: MSMECreate, db: Session = Depends(get_db)):
    """Register a new MSME"""
    
    # Check if wallet already registered
    existing_user = db.query(User).filter_by(wallet_address=msme_data.wallet_address).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet address already registered"
        )
    
    # Check if email already exists (if provided)
    if msme_data.email:
        existing_email = db.query(User).filter_by(email=msme_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if GSTN already registered
    existing_gstn = db.query(MSME).filter_by(gstn=msme_data.gstn).first()
    if existing_gstn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSTN already registered"
        )
    
    try:
        # Create user
        user = User(
            wallet_address=msme_data.wallet_address,
            user_type="MSME",
            email=msme_data.email
        )
        db.add(user)
        db.flush()
        
        # Create MSME
        msme = MSME(
            user_id=user.id,
            company_name=msme_data.company_name,
            gstn=msme_data.gstn,
            pan=msme_data.pan,
            reputation_score=500
        )
        db.add(msme)
        db.commit()
        db.refresh(msme)
        
        return {
            "id": str(msme.id),
            "company_name": msme.company_name,
            "gstn": msme.gstn,
            "reputation_score": msme.reputation_score
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/wallet/{wallet_address}")
async def get_msme_by_wallet(wallet_address: str, db: Session = Depends(get_db)):
    """Get MSME by wallet address"""
    user = db.query(User).filter_by(wallet_address=wallet_address, user_type="MSME").first()
    
    if not user:
        raise HTTPException(status_code=404, detail="MSME not found")
    
    msme = db.query(MSME).filter_by(user_id=user.id).first()
    
    if not msme:
        raise HTTPException(status_code=404, detail="MSME profile not found")
    
    return {
        "id": str(msme.id),
        "company_name": msme.company_name,
        "gstn": msme.gstn,
        "reputation_score": msme.reputation_score
    }
@router.get("/{msme_id}")
async def get_msme(msme_id: str, db: Session = Depends(get_db)):
    """Get MSME by ID"""
    msme = db.query(MSME).filter_by(id=msme_id).first()
    
    if not msme:
        raise HTTPException(status_code=404, detail="MSME not found")
    
    return {
        "id": str(msme.id),
        "company_name": msme.company_name,
        "gstn": msme.gstn,
        "reputation_score": msme.reputation_score
    }