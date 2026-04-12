# oracle/services/gem_scraper.py
"""
GeM Portal Scraper
Monitors GeM portal for new government orders
"""

import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json
import re
import logging

# Import config (with fallback)
try:
    from app.config import settings
except ImportError:
    # Create minimal settings for testing
    class Settings:
        GEM_PORTAL_URL = "https://gem.gov.in"
        GEM_PORTAL_USERNAME = None
        GEM_PORTAL_PASSWORD = None
        SCRAPE_TIMEOUT_SECONDS = 30
    
    settings = Settings()

logger = logging.getLogger(__name__)


class GeMOrder:
    """Represents a GeM order"""
    
    def __init__(self, data: Dict):
        self.gem_order_id = data.get("gem_order_id")
        self.order_amount = float(data.get("order_amount", 0))
        self.order_date = data.get("order_date")
        self.delivery_deadline = data.get("delivery_deadline")
        self.buyer_organization = data.get("buyer_organization")
        self.seller_gstn = data.get("seller_gstn")
        self.product_category = data.get("product_category")
        self.product_description = data.get("product_description")
        self.raw_data = data
    
    def to_dict(self) -> Dict:
        return {
            "gem_order_id": self.gem_order_id,
            "order_amount": self.order_amount,
            "order_date": self.order_date,
            "delivery_deadline": self.delivery_deadline,
            "buyer_organization": self.buyer_organization,
            "seller_gstn": self.seller_gstn,
            "product_category": self.product_category,
            "product_description": self.product_description,
            "raw_data": self.raw_data
        }
    
    def is_valid(self) -> bool:
        """Check if order data is complete and valid"""
        return all([
            self.gem_order_id,
            self.order_amount > 0,
            self.order_date,
            self.delivery_deadline,
            self.seller_gstn
        ])


class GeMScraper:
    """
    Scraper for GeM Portal
    
    NOTE: This is a simplified implementation.
    Real GeM portal scraping would require:
    1. Authentication handling
    2. CAPTCHA solving
    3. Session management
    4. Rate limiting compliance
    5. Legal authorization
    """
    
    def __init__(self):
        self.base_url = settings.GEM_PORTAL_URL
        self.username = settings.GEM_PORTAL_USERNAME
        self.password = settings.GEM_PORTAL_PASSWORD
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def __enter__(self):
        """Context manager entry"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()
    
    def start_browser(self):
        """Start headless browser"""
        logger.info("Starting browser for GeM scraping")
        
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        self.page = self.browser.new_page()
        self.page.set_default_timeout(settings.SCRAPE_TIMEOUT_SECONDS * 1000)
        
        logger.info("Browser started successfully")
    
    def close_browser(self):
        """Close browser"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        logger.info("Browser closed")
    
    def login(self) -> bool:
        """
        Login to GeM portal
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info("Logging into GeM portal")
            
            # Navigate to login page
            self.page.goto(f"{self.base_url}/login")
            
            # Fill credentials
            self.page.fill('input[name="username"]', self.username)
            self.page.fill('input[name="password"]', self.password)
            
            # Submit form
            self.page.click('button[type="submit"]')
            
            # Wait for navigation
            self.page.wait_for_load_state('networkidle')
            
            # Check if login successful (look for dashboard elements)
            if "dashboard" in self.page.url.lower():
                logger.info("Login successful")
                return True
            else:
                logger.error("Login failed - not redirected to dashboard")
                return False
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def scrape_recent_orders(
        self,
        days_back: int = 7,
        min_amount: float = 100000  # ₹1 Lakh minimum
    ) -> List[GeMOrder]:
        """
        Scrape recent orders from GeM portal
        
        Args:
            days_back: How many days back to search
            min_amount: Minimum order amount to consider
        
        Returns:
            List of GeMOrder objects
        """
        logger.info(f"Scraping orders from last {days_back} days")
        
        orders = []
        
        try:
            # Login first
            if not self.login():
                logger.error("Cannot scrape - login failed")
                return orders
            
            # Navigate to orders page
            self.page.goto(f"{self.base_url}/orders/recent")
            self.page.wait_for_load_state('networkidle')
            
            # Get page content
            html = self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Find order cards/rows
            # NOTE: These selectors are examples - actual GeM portal uses different structure
            order_elements = soup.find_all('div', class_='order-card')
            
            logger.info(f"Found {len(order_elements)} order elements")
            
            for element in order_elements:
                try:
                    order_data = self._parse_order_element(element)
                    
                    # Filter by date and amount
                    order_date = datetime.strptime(order_data.get("order_date"), "%Y-%m-%d")
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    
                    if order_date >= cutoff_date and order_data.get("order_amount", 0) >= min_amount:
                        order = GeMOrder(order_data)
                        
                        if order.is_valid():
                            orders.append(order)
                            logger.info(f"Scraped order: {order.gem_order_id} - ₹{order.order_amount}")
                
                except Exception as e:
                    logger.warning(f"Failed to parse order element: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping orders: {e}")
        
        logger.info(f"Successfully scraped {len(orders)} valid orders")
        return orders
    
    def _parse_order_element(self, element) -> Dict:
        """
        Parse individual order element from HTML
        
        NOTE: This is a mock implementation.
        Real parsing would depend on actual GeM portal structure.
        """
        # Example parsing logic
        data = {}
        
        try:
            # Extract order ID
            order_id_elem = element.find('span', class_='order-id')
            if order_id_elem:
                data['gem_order_id'] = order_id_elem.text.strip()
            
            # Extract amount
            amount_elem = element.find('span', class_='order-amount')
            if amount_elem:
                amount_text = amount_elem.text.strip()
                # Remove ₹ and commas, convert to float
                amount_text = re.sub(r'[₹,]', '', amount_text)
                data['order_amount'] = float(amount_text)
            
            # Extract dates
            date_elem = element.find('span', class_='order-date')
            if date_elem:
                date_text = date_elem.text.strip()
                # Parse date (format: DD-MM-YYYY)
                date_obj = datetime.strptime(date_text, "%d-%m-%Y")
                data['order_date'] = date_obj.strftime("%Y-%m-%d")
            
            deadline_elem = element.find('span', class_='delivery-deadline')
            if deadline_elem:
                deadline_text = deadline_elem.text.strip()
                deadline_obj = datetime.strptime(deadline_text, "%d-%m-%Y")
                data['delivery_deadline'] = deadline_obj.strftime("%Y-%m-%d")
            
            # Extract buyer organization
            buyer_elem = element.find('span', class_='buyer-org')
            if buyer_elem:
                data['buyer_organization'] = buyer_elem.text.strip()
            
            # Extract seller GSTN
            gstn_elem = element.find('span', class_='seller-gstn')
            if gstn_elem:
                data['seller_gstn'] = gstn_elem.text.strip()
            
            # Extract category
            category_elem = element.find('span', class_='product-category')
            if category_elem:
                data['product_category'] = category_elem.text.strip()
            
            # Extract description
            desc_elem = element.find('div', class_='product-description')
            if desc_elem:
                data['product_description'] = desc_elem.text.strip()
        
        except Exception as e:
            logger.warning(f"Error parsing order element: {e}")
        
        return data
    
    def get_order_details(self, gem_order_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific order
        
        Args:
            gem_order_id: GeM order ID
        
        Returns:
            Order details dictionary or None
        """
        try:
            logger.info(f"Fetching details for order: {gem_order_id}")
            
            # Navigate to order detail page
            self.page.goto(f"{self.base_url}/orders/{gem_order_id}")
            self.page.wait_for_load_state('networkidle')
            
            # Extract all details
            html = self.page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Parse detailed information
            details = {
                "gem_order_id": gem_order_id,
                "detailed_description": "",
                "milestones": [],
                "payment_terms": "",
                "quality_requirements": "",
                "documents": []
            }
            
            # ... (add parsing logic based on actual page structure)
            
            return details
        
        except Exception as e:
            logger.error(f"Error fetching order details: {e}")
            return None


# ============================================
# MOCK SCRAPER (for testing without GeM access)
# ============================================

class MockGeMScraper:
    """
    Mock scraper for testing without actual GeM portal access
    Generates realistic fake data
    """
    
    def __init__(self):
        self.order_counter = 10001
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def scrape_recent_orders(
        self,
        days_back: int = 7,
        min_amount: float = 100000
    ) -> List[GeMOrder]:
        """Generate mock orders"""
        
        logger.info("[MOCK] Generating fake GeM orders for testing")
        
        orders = []
        
        # Generate 3-5 random orders
        import random
        num_orders = random.randint(3, 5)
        
        buyer_orgs = [
            "Ministry of Defence",
            "Indian Railways",
            "Ministry of Health",
            "Ministry of Education",
            "State Police Department"
        ]
        
        categories = [
            "Office Furniture",
            "IT Equipment",
            "Medical Supplies",
            "Construction Materials",
            "Electrical Components"
        ]
        
        for i in range(num_orders):
            order_id = f"GEM{self.order_counter}"
            self.order_counter += 1
            
            order_date = datetime.now() - timedelta(days=random.randint(1, days_back))
            delivery_days = random.randint(30, 120)
            delivery_deadline = datetime.now() + timedelta(days=delivery_days)
            
            order_data = {
                "gem_order_id": order_id,
                "order_amount": random.randint(int(min_amount), int(min_amount * 10)),
                "order_date": order_date.strftime("%Y-%m-%d"),
                "delivery_deadline": delivery_deadline.strftime("%Y-%m-%d"),
                "buyer_organization": random.choice(buyer_orgs),
                "seller_gstn": f"27AABCU{random.randint(1000,9999)}R1ZM",
                "product_category": random.choice(categories),
                "product_description": f"Supply of {random.choice(categories).lower()} as per specifications"
            }
            
            order = GeMOrder(order_data)
            orders.append(order)
            
            logger.info(f"[MOCK] Generated order: {order.gem_order_id} - ₹{order.order_amount}")
        
        return orders
    
    def get_order_details(self, gem_order_id: str) -> Optional[Dict]:
        """Generate mock order details"""
        return {
            "gem_order_id": gem_order_id,
            "detailed_description": "Detailed specifications for the order",
            "milestones": ["Production", "Quality Check", "Delivery"],
            "payment_terms": "30 days post delivery",
            "quality_requirements": "As per BIS standards"
        }


# ============================================
# FACTORY FUNCTION
# ============================================

def get_scraper(use_mock: bool = True) -> GeMScraper:
    """
    Get appropriate scraper instance
    
    Args:
        use_mock: If True, return mock scraper for testing
    
    Returns:
        Scraper instance
    """
    if use_mock or not settings.GEM_PORTAL_USERNAME:
        logger.info("Using MOCK GeM scraper (no real credentials)")
        return MockGeMScraper()
    else:
        logger.info("Using REAL GeM scraper")
        return GeMScraper()


# ============================================
# CLI for testing
# ============================================

if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    
    print("Testing GeM Scraper...")
    print("=" * 50)
    
    with get_scraper(use_mock=True) as scraper:
        orders = scraper.scrape_recent_orders(days_back=7)
        
        print(f"\nFound {len(orders)} orders:")
        print("-" * 50)
        
        for order in orders:
            print(f"\nOrder ID: {order.gem_order_id}")
            print(f"Amount: ₹{order.order_amount:,.2f}")
            print(f"Date: {order.order_date}")
            print(f"Deadline: {order.delivery_deadline}")
            print(f"Buyer: {order.buyer_organization}")
            print(f"GSTN: {order.seller_gstn}")