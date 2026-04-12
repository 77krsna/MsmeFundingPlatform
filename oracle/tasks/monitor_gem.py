# oracle/tasks/monitor_gem.py
"""
Celery tasks for monitoring GeM portal
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery import Task
from tasks.celery_app import celery_app
from services.gem_scraper import get_scraper
from services.blockchain_client import get_blockchain_client
from app.database import get_db_context
from app.models import GeMOrder, MSME, OracleJob
from datetime import datetime, time
import logging
import json

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def scrape_gem_orders(self):
    """
    Scrape GeM portal for new orders
    Runs every 15 minutes
    """
    logger.info("Starting GeM portal scraping...")
    
    try:
        # Initialize scraper
        with get_scraper(use_mock=True) as scraper:
            # Scrape recent orders (last 7 days, minimum ₹1 lakh)
            orders = scraper.scrape_recent_orders(
                days_back=7,
                min_amount=100000
            )
            
            logger.info(f"Scraped {len(orders)} orders from GeM portal")
            
            # Process each order
            new_orders_count = 0
            
            with get_db_context() as db:
                for order in orders:
                    try:
                        # Check if order already exists
                        existing = db.query(GeMOrder).filter_by(
                            gem_order_id=order.gem_order_id
                        ).first()
                        
                        if existing:
                            logger.debug(f"Order {order.gem_order_id} already exists")
                            continue
                        
                        # Create new order record
                        new_order = GeMOrder(
                            gem_order_id=order.gem_order_id,
                            order_amount=order.order_amount,
                            order_date=datetime.strptime(order.order_date, "%Y-%m-%d"),
                            delivery_deadline=datetime.strptime(order.delivery_deadline, "%Y-%m-%d"),
                            buyer_organization=order.buyer_organization,
                            product_category=order.product_category,
                            status='DETECTED',
                            raw_gem_data=json.dumps(order.raw_data) if order.raw_data else None
                        )
                        
                        db.add(new_order)
                        db.flush()  # ✅ Flush to get the ID from database
                        new_orders_count += 1
                        
                        logger.info(f"New order detected: {order.gem_order_id} (ID: {new_order.id})")
                        
                        # Queue task to create smart contract (now ID exists)
                        if new_order.id:
                            create_order_contract.delay(str(new_order.id))
                        else:
                            logger.error(f"Failed to get ID for order {order.gem_order_id}")
                    
                    except Exception as order_error:
                        logger.error(f"Error processing order {order.gem_order_id}: {order_error}")
                        continue
                
                db.commit()
            
            logger.info(f"Scraping complete. {new_orders_count} new orders added.")
            
            return {
                'status': 'success',
                'total_scraped': len(orders),
                'new_orders': new_orders_count
            }
    
    except Exception as e:
        logger.error(f"Error scraping GeM portal: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@celery_app.task(bind=True, max_retries=3)
def create_order_contract(self, gem_order_db_id: str):
    """
    Create smart contract for a GeM order
    
    Args:
        gem_order_db_id: Database ID of GeMOrder
    """
    logger.info(f"Creating smart contract for order {gem_order_db_id}")
    
    # Validate UUID
    if not gem_order_db_id or gem_order_db_id == 'None':
        logger.error(f"Invalid order ID: {gem_order_db_id}")
        return {'status': 'error', 'message': 'Invalid order ID'}
    
    try:
        with get_db_context() as db:
            # Get order from database
            order = db.query(GeMOrder).filter_by(id=gem_order_db_id).first()
            
            if not order:
                logger.error(f"Order not found: {gem_order_db_id}")
                return {'status': 'error', 'message': 'Order not found'}
            
            # Initialize blockchain client
            blockchain_client = get_blockchain_client(use_mock=True)
            
            # Prepare contract creation parameters
            order_amount_wei = int(order.order_amount * 10**18)  # Convert to wei
            
            # Convert date to datetime if necessary
            if hasattr(order.delivery_deadline, 'timestamp'):
                delivery_timestamp = int(order.delivery_deadline.timestamp())
            else:
                # If it's a date object, convert to datetime
                delivery_dt = datetime.combine(order.delivery_deadline, time.min)
                delivery_timestamp = int(delivery_dt.timestamp())
            
            # Sign the order data
            message = f"{order.gem_order_id}{order_amount_wei}{delivery_timestamp}".encode()
            signature = blockchain_client.sign_message(message)
            
            # Create contract on blockchain
            result = blockchain_client.create_order_contract(
                gem_order_id=order.gem_order_id,
                order_amount=order_amount_wei,
                delivery_deadline=delivery_timestamp,
                oracle_signature=signature
            )
            
            # Update order record
            order.contract_address = result['contract_address']
            order.status = 'CONTRACT_CREATED'
            order.contract_created_at = datetime.utcnow()
            
            # Record transaction
            from app.models import BlockchainTransaction
            tx = BlockchainTransaction(
                tx_hash=result['transaction_hash'],
                block_number=result['block_number'],
                contract_address=result['contract_address'],
                function_name='createOrderFromGeM',
                gas_used=result['gas_used'],
                status='CONFIRMED'
            )
            db.add(tx)
            
            db.commit()
            
            logger.info(f"Contract created: {result['contract_address']}")
            
            # Notify MSME (queue notification task)
            notify_msme_new_order.delay(str(order.id))
            
            return {
                'status': 'success',
                'contract_address': result['contract_address'],
                'transaction_hash': result['transaction_hash']
            }
    
    except Exception as e:
        logger.error(f"Error creating contract: {e}")
        import traceback
        traceback.print_exc()
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes


@celery_app.task
def notify_msme_new_order(gem_order_db_id: str):
    """
    Notify MSME about new order (placeholder)
    
    In production, this would:
    - Send email
    - Send SMS
    - Push notification
    - Update dashboard
    """
    logger.info(f"[NOTIFICATION] New order contract created: {gem_order_db_id}")
    
    # TODO: Implement actual notification logic
    # - Email via SendGrid
    # - SMS via Twilio
    # - Push via Firebase
    
    return {'status': 'notification_sent'}