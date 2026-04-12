# oracle/tasks/verify_gstn.py
"""
Celery tasks for GSTN verification
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery import Task
from tasks.celery_app import celery_app
from services.gstn_client import get_gstn_client
from app.database import get_db_context
from app.models import GeMOrder, GSTNVerification, MSME
from datetime import datetime, timedelta
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def verify_pending_invoices(self):
    """
    Check GSTN for invoices that haven't been verified yet
    Runs every hour
    """
    logger.info("Checking for pending invoice verifications...")
    
    try:
        gstn_client = get_gstn_client(use_mock=True)
        
        with get_db_context() as db:
            # Find orders awaiting delivery confirmation
            pending_orders = db.query(GeMOrder).filter(
                GeMOrder.status.in_(['FUNDED', 'PRODUCTION'])
            ).all()
            
            logger.info(f"Found {len(pending_orders)} orders to check")
            
            verified_count = 0
            
            for order in pending_orders:
                try:
                    # Get MSME for this order
                    msme = db.query(MSME).filter_by(id=order.msme_id).first()
                    
                    if not msme or not msme.gstn:
                        logger.debug(f"Skipping order {order.id} - no MSME or GSTN")
                        continue
                    
                    # Check if we already verified recently (within last 6 hours)
                    recent_check = db.query(GSTNVerification).filter(
                        GSTNVerification.gem_order_id == order.id,
                        GSTNVerification.created_at > datetime.utcnow() - timedelta(hours=6)
                    ).first()
                    
                    if recent_check:
                        logger.debug(f"Order {order.id} already checked recently")
                        continue
                    
                    # Search for invoices
                    from_date = order.order_date.strftime("%Y-%m-%d")
                    to_date = datetime.utcnow().strftime("%Y-%m-%d")
                    
                    # Use asyncio.run for async GSTN client
                    invoices = asyncio.run(gstn_client.get_invoices(
                        gstn=msme.gstn,
                        from_date=from_date,
                        to_date=to_date
                    ))
                    
                    # Look for matching invoice
                    for invoice in invoices:
                        invoice_amount = float(invoice.get('total_amount', 0))
                        
                        # Check if amount matches order (with 5% tolerance)
                        amount_diff = abs(invoice_amount - float(order.order_amount))
                        tolerance = float(order.order_amount) * 0.05
                        
                        if amount_diff <= tolerance:
                            # Invoice found! Create verification record
                            verification = GSTNVerification(
                                gem_order_id=order.id,
                                invoice_number=invoice['invoice_number'],
                                invoice_date=datetime.strptime(invoice['invoice_date'], "%Y-%m-%d"),
                                invoice_amount=invoice_amount,
                                gstn=msme.gstn,
                                verification_status='VERIFIED',
                                api_response=json.dumps(invoice) if invoice else None,
                                verified_at=datetime.utcnow()
                            )
                            
                            db.add(verification)
                            db.flush()  # Get verification ID
                            verified_count += 1
                            
                            logger.info(f"Invoice verified for order {order.gem_order_id}")
                            
                            # Queue delivery confirmation task
                            confirm_delivery_on_chain.delay(str(order.id), str(verification.id))
                            
                            break  # Found matching invoice, stop searching
                
                except Exception as order_error:
                    logger.error(f"Error processing order {order.id}: {order_error}")
                    continue  # Continue with next order
            
            db.commit()
            
            logger.info(f"Verification complete. {verified_count} invoices verified.")
            
            return {
                'status': 'success',
                'checked': len(pending_orders),
                'verified': verified_count
            }
    
    except Exception as e:
        logger.error(f"Error verifying invoices: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True, max_retries=3)
def confirm_delivery_on_chain(self, gem_order_db_id: str, verification_id: str):
    """
    Submit delivery confirmation to blockchain
    
    Args:
        gem_order_db_id: Database ID of GeMOrder
        verification_id: Database ID of GSTNVerification
    """
    logger.info(f"Confirming delivery on-chain for order {gem_order_db_id}")
    
    try:
        from services.blockchain_client import get_blockchain_client
        import hashlib
        
        with get_db_context() as db:
            order = db.query(GeMOrder).filter_by(id=gem_order_db_id).first()
            verification = db.query(GSTNVerification).filter_by(id=verification_id).first()
            
            if not order or not verification:
                logger.error("Order or verification not found")
                return {'status': 'error', 'message': 'Not found'}
            
            if not order.contract_address:
                logger.error(f"Order {order.id} has no contract address")
                return {'status': 'error', 'message': 'No contract address'}
            
            blockchain_client = get_blockchain_client(use_mock=True)
            
            # Create invoice hash
            invoice_data = f"{verification.invoice_number}{verification.invoice_date}{verification.invoice_amount}".encode()
            invoice_hash = hashlib.sha256(invoice_data).digest()
            
            # Sign
            signature = blockchain_client.sign_message(invoice_hash)
            
            # Confirm delivery on blockchain
            result = blockchain_client.confirm_delivery(
                order_contract_address=order.contract_address,
                invoice_hash=invoice_hash,
                oracle_signature=signature
            )
            
            # Update order status
            order.status = 'DELIVERED'
            
            # Record transaction
            from app.models import BlockchainTransaction
            tx = BlockchainTransaction(
                tx_hash=result['transaction_hash'],
                block_number=result['block_number'],
                contract_address=order.contract_address,
                function_name='confirmDelivery',
                gas_used=result['gas_used'],
                status='CONFIRMED'
            )
            db.add(tx)
            
            db.commit()
            
            logger.info(f"Delivery confirmed on-chain: {result['transaction_hash']}")
            
            return {
                'status': 'success',
                'transaction_hash': result['transaction_hash']
            }
    
    except Exception as e:
        logger.error(f"Error confirming delivery: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e, countdown=600)


@celery_app.task
def verify_msme_gstn(msme_id: str, gstn: str):
    """
    Verify MSME's GSTN is valid
    
    Args:
        msme_id: Database ID of MSME
        gstn: GSTN to verify
    """
    logger.info(f"Verifying GSTN {gstn} for MSME {msme_id}")
    
    try:
        gstn_client = get_gstn_client(use_mock=True)
        
        # Verify GSTN
        result = asyncio.run(gstn_client.verify_gstn(gstn))
        
        if result.get('valid'):
            logger.info(f"GSTN {gstn} is valid: {result.get('legal_name')}")
            
            # Update MSME record
            with get_db_context() as db:
                msme = db.query(MSME).filter_by(id=msme_id).first()
                if msme:
                    # Could store additional GSTN details if needed
                    logger.info(f"MSME {msme.company_name} GSTN verified")
                db.commit()
            
            return {
                'status': 'success',
                'valid': True,
                'details': result
            }
        else:
            logger.warning(f"GSTN {gstn} is invalid")
            return {
                'status': 'error',
                'valid': False,
                'error': result.get('error')
            }
    
    except Exception as e:
        logger.error(f"Error verifying GSTN: {e}")
        raise