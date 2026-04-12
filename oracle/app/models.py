# oracle/app/models.py
"""
Database models - Simplified version for testing
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User accounts"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address = Column(String(42), unique=True, nullable=False)
    user_type = Column(String(20), nullable=False)  # MSME, INVESTOR, ADMIN
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.wallet_address}>"


class MSME(Base):
    """MSME companies"""
    __tablename__ = "msmes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    company_name = Column(String(255), nullable=False)
    gstn = Column(String(15), unique=True, nullable=False)
    pan = Column(String(10), nullable=False)
    virtual_account_id = Column(String(50), unique=True)
    reputation_score = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MSME {self.company_name}>"


class GeMOrder(Base):
    """Government orders from GeM portal"""
    __tablename__ = "gem_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gem_order_id = Column(String(50), unique=True, nullable=False)
    contract_address = Column(String(42), unique=True)
    msme_id = Column(UUID(as_uuid=True), ForeignKey("msmes.id"))
    
    order_amount = Column(Numeric(18, 2), nullable=False)
    order_date = Column(DateTime, nullable=False)
    delivery_deadline = Column(DateTime, nullable=False)
    buyer_organization = Column(String(255))
    product_category = Column(String(100))
    
    status = Column(String(30), default="DETECTED")
    contract_created_at = Column(DateTime)
    raw_gem_data = Column(Text)  # JSON as text
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<GeMOrder {self.gem_order_id}>"


class GSTNVerification(Base):
    """GSTN invoice verifications"""
    __tablename__ = "gstn_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gem_order_id = Column(UUID(as_uuid=True), ForeignKey("gem_orders.id"))
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    invoice_amount = Column(Numeric(18, 2), nullable=False)
    gstn = Column(String(15), nullable=False)
    verification_status = Column(String(20))  # PENDING, VERIFIED, MISMATCH
    api_response = Column(Text)  # JSON stored as text
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<GSTNVerification {self.invoice_number}>"


class BlockchainTransaction(Base):
    """Blockchain transactions"""
    __tablename__ = "blockchain_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_hash = Column(String(66), unique=True, nullable=False)
    block_number = Column(Integer)
    contract_address = Column(String(42))
    function_name = Column(String(100))
    gas_used = Column(Integer)
    status = Column(String(20))  # PENDING, CONFIRMED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BlockchainTransaction {self.tx_hash[:10]}...>"


class OracleJob(Base):
    """Background jobs for oracle"""
    __tablename__ = "oracle_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default="QUEUED")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OracleJob {self.job_type}>"


class VirtualAccountTransaction(Base):
    """Virtual account transactions"""
    __tablename__ = "virtual_account_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    virtual_account_id = Column(String(50), nullable=False)
    gem_order_id = Column(UUID(as_uuid=True), ForeignKey("gem_orders.id"))
    transaction_type = Column(String(20))  # CREDIT, DEBIT
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(10), default="INR")
    external_reference = Column(String(100))
    description = Column(Text)
    reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VirtualAccountTransaction {self.amount} {self.currency}>"


# Print confirmation when module is imported
print("✅ Models module loaded successfully")
print(f"   Found {len(Base.metadata.tables)} table definitions")