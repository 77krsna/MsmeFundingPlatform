# oracle/tasks/process_orders.py
"""
Celery tasks for processing orders and payments
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tasks.celery_app import celery_app
from app.database import get_db_context
from app.models import GeMOrder, VirtualAccountTransaction, MSME, OracleJob
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def check_delivery_status():
    """
    Check delivery status for all active orders
    Runs daily at 9 AM
    """
    logger.info("Checking delivery status for active orders...")
    
    try:
        with get_db_context() as db:
            # Find orders past deadline
            overdue_orders = db.query(GeMOrder).filter(
                GeMOrder.status.in_(['FUNDED', 'PRODUCTION']),
                GeMOrder.delivery_deadline < datetime.utcnow()
            ).all()
            
            logger.info(f"Found {len(overdue_orders)} overdue orders")
            
            defaulted_count = 0
            
            for order in overdue_orders:
                logger.warning(f"Order {order.gem_order_id} is overdue!")
                
                # Mark as defaulted if significantly overdue (30 days)
                if order.delivery_deadline < datetime.utcnow() - timedelta(days=30):
                    order.status = 'DEFAULTED'
                    logger.error(f"Marking order {order.gem_order_id} as DEFAULTED")
                    defaulted_count += 1
                    
                    # TODO: Trigger liquidation process
                    # trigger_liquidation.delay(str(order.id))
            
            db.commit()
            
            return {
                'status': 'success',
                'overdue_count': len(overdue_orders),
                'defaulted_count': defaulted_count
            }
    
    except Exception as e:
        logger.error(f"Error checking delivery status: {e}")
        raise


@celery_app.task
def reconcile_payments():
    """
    Reconcile virtual account payments with orders
    Runs twice daily
    """
    logger.info("Reconciling payments...")
    
    try:
        with get_db_context() as db:
            # Find unreconciled transactions
            unreconciled = db.query(VirtualAccountTransaction).filter_by(
                reconciled=False,
                transaction_type='CREDIT'  # Only credits (payments received)
            ).all()
            
            logger.info(f"Found {len(unreconciled)} unreconciled transactions")
            
            reconciled_count = 0
            
            for transaction in unreconciled:
                # Try to match with an order
                # Find order by virtual account ID
                order = db.query(GeMOrder).join(MSME).filter(
                    MSME.virtual_account_id == transaction.virtual_account_id,
                    GeMOrder.status.in_(['DELIVERED', 'DISBURSED_T3'])
                ).first()
                
                if order:
                    # Link transaction to order
                    transaction.gem_order_id = order.id
                    transaction.reconciled = True
                    transaction.reconciled_at = datetime.utcnow()
                    
                    # Update order status
                    order.status = 'PAYMENT_RECEIVED'
                    
                    reconciled_count += 1
                    logger.info(f"Reconciled payment for order {order.gem_order_id}")
                    
                    # Queue repayment task
                    process_investor_repayment.delay(str(order.id))
            
            db.commit()
            
            return {
                'status': 'success',
                'total_unreconciled': len(unreconciled),
                'reconciled': reconciled_count
            }
    
    except Exception as e:
        logger.error(f"Error reconciling payments: {e}")
        raise


@celery_app.task
def process_investor_repayment(gem_order_db_id: str):
    """
    Process repayment to investors
    
    Args:
        gem_order_db_id: Database ID of GeMOrder
    """
    logger.info(f"Processing investor repayment for order {gem_order_db_id}")
    
    try:
        from services.blockchain_client import get_blockchain_client
        
        with get_db_context() as db:
            order = db.query(GeMOrder).filter_by(id=gem_order_db_id).first()
            
            if not order:
                logger.error("Order not found")
                return {'status': 'error', 'message': 'Order not found'}
            
            # In a real implementation, this would:
            # 1. Get list of investors from blockchain
            # 2. Calculate principal + interest for each investor
            # 3. Transfer funds from virtual account to investors
            # 4. Update blockchain contract state
            # 5. Mark investments as repaid in database
            
            logger.info(f"Repayment processed for order {order.gem_order_id}")
            
            order.status = 'REPAID'
            db.commit()
            
            return {'status': 'success'}
    
    except Exception as e:
        logger.error(f"Error processing repayment: {e}")
        raise


@celery_app.task
def cleanup_old_jobs():
    """
    Clean up old job records
    Runs daily
    """
    logger.info("Cleaning up old job records...")
    
    try:
        with get_db_context() as db:
            # Delete jobs older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            deleted = db.query(OracleJob).filter(
                OracleJob.created_at < cutoff_date,
                OracleJob.status.in_(['COMPLETED', 'FAILED'])
            ).delete()
            
            db.commit()
            
            logger.info(f"Deleted {deleted} old job records")
            
            return {'status': 'success', 'deleted': deleted}
    
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        raise