"""
Quad-Mesh Delivery Platform
Four-sided marketplace: Customer -> Restaurant -> Rider -> Delivery Location
With GPS-based payment escrow system
"""

import uuid
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

class OrderStatus(Enum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_ESCROWED = "payment_escrowed"
    RESTAURANT_NOTIFIED = "restaurant_notified"
    RESTAURANT_CONFIRMED = "restaurant_confirmed"
    SEEKING_RIDER = "seeking_rider"
    RIDER_ASSIGNED = "rider_assigned"
    RIDER_EN_ROUTE_PICKUP = "rider_en_route_pickup"
    RIDER_AT_RESTAURANT = "rider_at_restaurant"
    ORDER_PICKED_UP = "order_picked_up"
    RIDER_EN_ROUTE_DELIVERY = "rider_en_route_delivery"
    RIDER_AT_DELIVERY = "rider_at_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    PENDING = "pending"
    ESCROWED = "escrowed"
    RESTAURANT_PAID = "restaurant_paid"
    RIDER_HALF_PAID = "rider_half_paid"
    RIDER_FULL_PAID = "rider_full_paid"
    COMPLETED = "completed"

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance in meters using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: str
    delivery_location: Location

@dataclass
class Restaurant:
    id: str
    name: str
    location: Location
    email: str
    phone: str
    bank_account: str
    is_active: bool = True

@dataclass
class Rider:
    id: str
    name: str
    email: str
    phone: str
    current_location: Location
    bank_account: str
    is_available: bool = True
    rating: float = 5.0
    total_deliveries: int = 0

@dataclass
class OrderItem:
    name: str
    quantity: int
    price: float

@dataclass
class Order:
    id: str
    customer: Customer
    restaurant: Restaurant
    items: List[OrderItem]
    total_amount: float
    delivery_fee: float
    status: OrderStatus
    payment_status: PaymentStatus
    assigned_rider: Optional[Rider] = None
    created_at: datetime = field(default_factory=datetime.now)
    restaurant_confirmation_deadline: Optional[datetime] = None
    rider_assignment_deadline: Optional[datetime] = None
    rider_acceptance_deadline: Optional[datetime] = None
    status_history: List[Dict] = field(default_factory=list)
    
    def add_status(self, status: OrderStatus, note: str = ""):
        self.status = status
        self.status_history.append({
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "note": note
        })

class EscrowSystem:
    """Manages payments in escrow until milestones are reached"""
    
    def __init__(self):
        self.escrow_accounts: Dict[str, Dict] = {}
    
    def create_escrow(self, order_id: str, total_amount: float, 
                     restaurant_amount: float, rider_amount: float) -> bool:
        """Create escrow account for an order"""
        self.escrow_accounts[order_id] = {
            'total': total_amount,
            'restaurant_amount': restaurant_amount,
            'rider_amount': rider_amount,
            'restaurant_paid': False,
            'rider_half_paid': False,
            'rider_full_paid': False,
            'created_at': datetime.now().isoformat()
        }
        print(f"💰 Escrow created for order {order_id}: ${total_amount}")
        return True
    
    def pay_restaurant(self, order_id: str, restaurant: Restaurant) -> bool:
        """Pay restaurant upon order confirmation"""
        if order_id not in self.escrow_accounts:
            return False
        
        escrow = self.escrow_accounts[order_id]
        if not escrow['restaurant_paid']:
            amount = escrow['restaurant_amount']
            escrow['restaurant_paid'] = True
            print(f"✅ Restaurant {restaurant.name} paid ${amount} to {restaurant.bank_account}")
            return True
        return False
    
    def pay_rider_half(self, order_id: str, rider: Rider) -> bool:
        """Pay rider 50% upon pickup confirmation"""
        if order_id not in self.escrow_accounts:
            return False
        
        escrow = self.escrow_accounts[order_id]
        if not escrow['rider_half_paid']:
            amount = escrow['rider_amount'] / 2
            escrow['rider_half_paid'] = True
            print(f"✅ Rider {rider.name} paid 50% (${amount}) to {rider.bank_account}")
            return True
        return False
    
    def pay_rider_remaining(self, order_id: str, rider: Rider) -> bool:
        """Pay rider remaining 50% upon delivery confirmation"""
        if order_id not in self.escrow_accounts:
            return False
        
        escrow = self.escrow_accounts[order_id]
        if escrow['rider_half_paid'] and not escrow['rider_full_paid']:
            amount = escrow['rider_amount'] / 2
            escrow['rider_full_paid'] = True
            print(f"✅ Rider {rider.name} paid remaining 50% (${amount}) to {rider.bank_account}")
            return True
        return False

class DeliveryPlatform:
    """Main platform orchestrating the four-sided marketplace"""
    
    def __init__(self, gps_tolerance_meters: float = 50, 
                 rider_acceptance_timeout_minutes: int = 5):
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.restaurants: Dict[str, Restaurant] = {}
        self.riders: Dict[str, Rider] = {}
        self.escrow = EscrowSystem()
        self.gps_tolerance = gps_tolerance_meters
        self.rider_acceptance_timeout = timedelta(minutes=rider_acceptance_timeout_minutes)
        self.rider_queue: List[str] = []  # Queue of available riders
        
    def register_customer(self, name: str, email: str, phone: str, 
                         location: Location) -> Customer:
        customer_id = str(uuid.uuid4())
        customer = Customer(customer_id, name, email, phone, location)
        self.customers[customer_id] = customer
        print(f"👤 Customer registered: {name}")
        return customer
    
    def register_restaurant(self, name: str, location: Location, email: str, 
                           phone: str, bank_account: str) -> Restaurant:
        restaurant_id = str(uuid.uuid4())
        restaurant = Restaurant(restaurant_id, name, location, email, 
                               phone, bank_account)
        self.restaurants[restaurant_id] = restaurant
        print(f"🏪 Restaurant registered: {name}")
        return restaurant
    
    def register_rider(self, name: str, email: str, phone: str, 
                      current_location: Location, bank_account: str) -> Rider:
        rider_id = str(uuid.uuid4())
        rider = Rider(rider_id, name, email, phone, current_location, bank_account)
        self.riders[rider_id] = rider
        self.rider_queue.append(rider_id)
        print(f"🏍️ Rider registered: {name}")
        return rider
    
    def place_order(self, customer: Customer, restaurant: Restaurant, 
                   items: List[OrderItem], delivery_fee: float) -> Order:
        """Customer places an order"""
        order_id = str(uuid.uuid4())
        total_item_cost = sum(item.price * item.quantity for item in items)
        total_amount = total_item_cost + delivery_fee
        
        order = Order(
            id=order_id,
            customer=customer,
            restaurant=restaurant,
            items=items,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            status=OrderStatus.PENDING_PAYMENT,
            payment_status=PaymentStatus.PENDING
        )
        
        self.orders[order_id] = order
        order.add_status(OrderStatus.PENDING_PAYMENT, "Order created by customer")
        
        print(f"\n📱 NEW ORDER #{order_id[:8]}")
        print(f"   Customer: {customer.name}")
        print(f"   Restaurant: {restaurant.name}")
        print(f"   Items: {len(items)} items, Total: ${total_amount:.2f}")
        
        return order
    
    def process_payment(self, order: Order) -> bool:
        """Process payment and move to escrow"""
        # Simulate payment processing
        restaurant_cut = sum(item.price * item.quantity for item in order.items)
        rider_cut = order.delivery_fee
        
        # Create escrow
        success = self.escrow.create_escrow(
            order.id, 
            order.total_amount,
            restaurant_cut,
            rider_cut
        )
        
        if success:
            order.payment_status = PaymentStatus.ESCROWED
            order.add_status(OrderStatus.PAYMENT_ESCROWED, "Payment secured in escrow")
            
            # Notify restaurant
            self._notify_restaurant(order)
            return True
        
        return False
    
    def _notify_restaurant(self, order: Order):
        """Notify restaurant of new order"""
        order.add_status(OrderStatus.RESTAURANT_NOTIFIED, 
                        f"Restaurant {order.restaurant.name} notified")
        print(f"\n🔔 Restaurant {order.restaurant.name} notified of order #{order.id[:8]}")
        print(f"   → Order appears on restaurant dashboard")
    
    def restaurant_confirm_order(self, order: Order) -> bool:
        """Restaurant confirms they can fulfill the order"""
        if order.status != OrderStatus.RESTAURANT_NOTIFIED:
            print(f"❌ Order not in correct state for restaurant confirmation")
            return False
        
        # Pay restaurant immediately upon confirmation
        payment_success = self.escrow.pay_restaurant(order.id, order.restaurant)
        
        if payment_success:
            order.payment_status = PaymentStatus.RESTAURANT_PAID
            order.add_status(OrderStatus.RESTAURANT_CONFIRMED, 
                           "Restaurant confirmed and paid")
            
            # Start seeking rider
            self._seek_rider(order)
            return True
        
        return False
    
    def _seek_rider(self, order: Order):
        """Start seeking available rider from queue"""
        order.add_status(OrderStatus.SEEKING_RIDER, "Looking for available rider")
        print(f"\n🔍 Seeking rider for order #{order.id[:8]}")
        
        # Set deadline for rider acceptance
        order.rider_acceptance_deadline = datetime.now() + self.rider_acceptance_timeout
        
        # Try to assign to next available rider
        self._assign_next_rider(order)
    
    def _assign_next_rider(self, order: Order) -> bool:
        """Assign order to next rider in queue"""
        if not self.rider_queue:
            print(f"⚠️ No available riders in queue")
            return False
        
        # Get next rider from queue
        rider_id = self.rider_queue.pop(0)
        rider = self.riders.get(rider_id)
        
        if not rider or not rider.is_available:
            # Rider not available, try next
            return self._assign_next_rider(order)
        
        order.assigned_rider = rider
        order.rider_acceptance_deadline = datetime.now() + self.rider_acceptance_timeout
        order.add_status(OrderStatus.RIDER_ASSIGNED, 
                        f"Assigned to rider {rider.name}")
        
        print(f"📲 Order assigned to rider {rider.name}")
        print(f"   ⏰ Rider has {self.rider_acceptance_timeout.seconds // 60} minutes to accept")
        
        return True
    
    def rider_accept_order(self, order: Order) -> bool:
        """Rider accepts the delivery"""
        if order.status != OrderStatus.RIDER_ASSIGNED:
            return False
        
        if not order.assigned_rider:
            return False
        
        # Check if deadline passed
        if datetime.now() > order.rider_acceptance_deadline:
            print(f"⏰ Rider acceptance timeout - moving to next rider")
            return self._reassign_to_next_rider(order)
        
        rider = order.assigned_rider
        rider.is_available = False
        
        order.add_status(OrderStatus.RIDER_EN_ROUTE_PICKUP, 
                        f"Rider {rider.name} accepted, en route to restaurant")
        
        print(f"✅ Rider {rider.name} accepted order #{order.id[:8]}")
        print(f"   → Rider heading to {order.restaurant.name}")
        
        return True
    
    def rider_reject_or_timeout(self, order: Order) -> bool:
        """Handle rider rejection or timeout - pass to next rider"""
        return self._reassign_to_next_rider(order)
    
    def _reassign_to_next_rider(self, order: Order) -> bool:
        """Reassign order to next available rider"""
        if order.assigned_rider:
            # Return rider to queue
            self.rider_queue.append(order.assigned_rider.id)
            order.assigned_rider.is_available = True
            order.assigned_rider = None
        
        print(f"🔄 Reassigning order #{order.id[:8]} to next rider...")
        return self._assign_next_rider(order)
    
    def check_rider_at_restaurant(self, order: Order, rider_location: Location) -> bool:
        """Check if rider GPS coordinates match restaurant location"""
        if order.status != OrderStatus.RIDER_EN_ROUTE_PICKUP:
            return False
        
        distance = rider_location.distance_to(order.restaurant.location)
        
        print(f"📍 Checking rider location: {distance:.1f}m from restaurant")
        
        if distance <= self.gps_tolerance:
            order.add_status(OrderStatus.RIDER_AT_RESTAURANT, 
                           "Rider arrived at restaurant")
            print(f"✅ Rider at restaurant (within {self.gps_tolerance}m)")
            return True
        
        return False
    
    def confirm_pickup(self, order: Order) -> bool:
        """Rider confirms pickup - triggers 50% payment"""
        if order.status != OrderStatus.RIDER_AT_RESTAURANT:
            return False
        
        rider = order.assigned_rider
        if not rider:
            return False
        
        # Pay rider 50%
        payment_success = self.escrow.pay_rider_half(order.id, rider)
        
        if payment_success:
            order.payment_status = PaymentStatus.RIDER_HALF_PAID
            order.add_status(OrderStatus.ORDER_PICKED_UP, 
                           "Order picked up, rider paid 50%")
            order.add_status(OrderStatus.RIDER_EN_ROUTE_DELIVERY,
                           f"Rider heading to delivery location")
            
            print(f"📦 Order picked up by {rider.name}")
            print(f"   → Heading to {order.customer.delivery_location.address}")
            return True
        
        return False
    
    def check_rider_at_delivery(self, order: Order, rider_location: Location) -> bool:
        """Check if rider GPS coordinates match delivery location"""
        if order.status != OrderStatus.RIDER_EN_ROUTE_DELIVERY:
            return False
        
        distance = rider_location.distance_to(order.customer.delivery_location)
        
        print(f"📍 Checking rider location: {distance:.1f}m from delivery address")
        
        if distance <= self.gps_tolerance:
            order.add_status(OrderStatus.RIDER_AT_DELIVERY, 
                           "Rider arrived at delivery location")
            print(f"✅ Rider at delivery location (within {self.gps_tolerance}m)")
            return True
        
        return False
    
    def confirm_delivery(self, order: Order) -> bool:
        """Confirm delivery - triggers remaining 50% payment to rider"""
        if order.status != OrderStatus.RIDER_AT_DELIVERY:
            return False
        
        rider = order.assigned_rider
        if not rider:
            return False
        
        # Pay rider remaining 50%
        payment_success = self.escrow.pay_rider_remaining(order.id, rider)
        
        if payment_success:
            order.payment_status = PaymentStatus.RIDER_FULL_PAID
            order.add_status(OrderStatus.DELIVERED, 
                           "Order delivered, rider paid in full")
            
            # Update rider stats
            rider.total_deliveries += 1
            rider.is_available = True
            self.rider_queue.append(rider.id)
            
            print(f"🎉 ORDER DELIVERED SUCCESSFULLY!")
            print(f"   Order #{order.id[:8]} completed")
            print(f"   Rider {rider.name} back in queue")
            
            return True
        
        return False
    
    def get_order_journey(self, order: Order) -> Dict:
        """Get current status and journey for customer tracking"""
        journey_map = {
            OrderStatus.PENDING_PAYMENT: {"step": 1, "label": "Payment Processing"},
            OrderStatus.PAYMENT_ESCROWED: {"step": 2, "label": "Payment Secured"},
            OrderStatus.RESTAURANT_NOTIFIED: {"step": 3, "label": "Restaurant Notified"},
            OrderStatus.RESTAURANT_CONFIRMED: {"step": 4, "label": "Restaurant Confirmed"},
            OrderStatus.SEEKING_RIDER: {"step": 5, "label": "Finding Rider"},
            OrderStatus.RIDER_ASSIGNED: {"step": 6, "label": "Rider Assigned"},
            OrderStatus.RIDER_EN_ROUTE_PICKUP: {"step": 7, "label": "Rider Going to Restaurant"},
            OrderStatus.RIDER_AT_RESTAURANT: {"step": 8, "label": "Rider at Restaurant"},
            OrderStatus.ORDER_PICKED_UP: {"step": 9, "label": "Order Picked Up"},
            OrderStatus.RIDER_EN_ROUTE_DELIVERY: {"step": 10, "label": "Rider Coming to You"},
            OrderStatus.RIDER_AT_DELIVERY: {"step": 11, "label": "Rider Nearby"},
            OrderStatus.DELIVERED: {"step": 12, "label": "Delivered!"},
        }
        
        current = journey_map.get(order.status, {"step": 0, "label": "Unknown"})
        
        return {
            "order_id": order.id,
            "current_status": order.status.value,
            "current_step": current["step"],
            "current_label": current["label"],
            "total_steps": 12,
            "progress_percentage": (current["step"] / 12) * 100,
            "assigned_rider": order.assigned_rider.name if order.assigned_rider else None,
            "rider_location": {
                "lat": order.assigned_rider.current_location.latitude,
                "lng": order.assigned_rider.current_location.longitude
            } if order.assigned_rider else None,
            "history": order.status_history
        }


def run_demo():
    """Demonstrate the complete order flow"""
    print("=" * 70)
    print("🚀 QUAD-MESH DELIVERY PLATFORM DEMO")
    print("=" * 70)
    
    # Initialize platform
    platform = DeliveryPlatform(
        gps_tolerance_meters=50,
        rider_acceptance_timeout_minutes=5
    )
    
    # Register entities
    print("\n📋 SETTING UP PLATFORM...")
    
    customer = platform.register_customer(
        "Alice Johnson",
        "alice@email.com",
        "+256-123-4567",
        Location(0.3476, 32.5825, "123 Main St, Kampala")
    )
    
    restaurant = platform.register_restaurant(
        "Mama Mia's Pizza",
        Location(0.3426, 32.5775, "45 Restaurant Row, Kampala"),
        "info@mamamia.com",
        "+256-987-6543",
        "BANK-ACCT-REST-001"
    )
    
    rider1 = platform.register_rider(
        "Bob Rider",
        "bob@delivery.com",
        "+256-555-0001",
        Location(0.3450, 32.5800, "Central Kampala"),
        "BANK-ACCT-RIDER-001"
    )
    
    rider2 = platform.register_rider(
        "Charlie Courier",
        "charlie@delivery.com",
        "+256-555-0002",
        Location(0.3460, 32.5810, "Near Central"),
        "BANK-ACCT-RIDER-002"
    )
    
    # Customer places order
    print("\n" + "=" * 70)
    print("STEP 1: CUSTOMER PLACES ORDER")
    print("=" * 70)
    
    items = [
        OrderItem("Margherita Pizza", 2, 25000),
        OrderItem("Caesar Salad", 1, 15000),
        OrderItem("Coca Cola", 2, 3000)
    ]
    
    order = platform.place_order(customer, restaurant, items, delivery_fee=5000)
    
    # Process payment
    print("\n" + "=" * 70)
    print("STEP 2: PAYMENT PROCESSING")
    print("=" * 70)
    platform.process_payment(order)
    
    # Restaurant confirms
    print("\n" + "=" * 70)
    print("STEP 3: RESTAURANT CONFIRMATION")
    print("=" * 70)
    time.sleep(1)
    platform.restaurant_confirm_order(order)
    
    # First rider doesn't accept - times out
    print("\n" + "=" * 70)
    print("STEP 4: RIDER ASSIGNMENT (FIRST ATTEMPT)")
    print("=" * 70)
    time.sleep(1)
    print("⏰ Simulating rider timeout...")
    platform.rider_reject_or_timeout(order)
    
    # Second rider accepts
    print("\n" + "=" * 70)
    print("STEP 5: RIDER ASSIGNMENT (SECOND ATTEMPT)")
    print("=" * 70)
    time.sleep(1)
    platform.rider_accept_order(order)
    
    # Rider arrives at restaurant
    print("\n" + "=" * 70)
    print("STEP 6: RIDER TRAVELING TO RESTAURANT")
    print("=" * 70)
    time.sleep(1)
    
    # Simulate rider movement toward restaurant
    rider_location = Location(0.3425, 32.5776, "Near restaurant")
    platform.check_rider_at_restaurant(order, rider_location)
    
    # Confirm pickup
    print("\n" + "=" * 70)
    print("STEP 7: ORDER PICKUP")
    print("=" * 70)
    time.sleep(1)
    platform.confirm_pickup(order)
    
    # Rider travels to delivery location
    print("\n" + "=" * 70)
    print("STEP 8: RIDER TRAVELING TO CUSTOMER")
    print("=" * 70)
    time.sleep(1)
    
    # Simulate rider movement toward customer
    rider_location = Location(0.3477, 32.5826, "Near customer")
    platform.check_rider_at_delivery(order, rider_location)
    
    # Confirm delivery
    print("\n" + "=" * 70)
    print("STEP 9: DELIVERY CONFIRMATION")
    print("=" * 70)
    time.sleep(1)
    platform.confirm_delivery(order)
    
    # Show order journey
    print("\n" + "=" * 70)
    print("CUSTOMER ORDER TRACKING VIEW")
    print("=" * 70)
    journey = platform.get_order_journey(order)
    print(json.dumps(journey, indent=2, default=str))
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
