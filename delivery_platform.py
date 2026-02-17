"""Core delivery platform - shared by all apps"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from math import radians, sin, cos, sqrt, atan2
import uuid

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

class PaymentStatus(Enum):
    PENDING = "pending"
    ESCROWED = "escrowed"
    RESTAURANT_PAID = "restaurant_paid"
    RIDER_HALF_PAID = "rider_half_paid"
    RIDER_FULL_PAID = "rider_full_paid"

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str
    
    def distance_to(self, other: 'Location') -> float:
        R = 6371000
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        dlat, dlon = lat2 - lat1, lon2 - lon1
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
    def __init__(self):
        self.escrow_accounts: Dict[str, Dict] = {}
    
    def create_escrow(self, order_id: str, total: float, restaurant: float, rider: float):
        self.escrow_accounts[order_id] = {
            'total': total, 'restaurant_amount': restaurant, 'rider_amount': rider,
            'restaurant_paid': False, 'rider_half_paid': False, 'rider_full_paid': False
        }
        return True
    
    def pay_restaurant(self, order_id: str):
        if order_id in self.escrow_accounts and not self.escrow_accounts[order_id]['restaurant_paid']:
            self.escrow_accounts[order_id]['restaurant_paid'] = True
            return True
        return False
    
    def pay_rider_half(self, order_id: str):
        if order_id in self.escrow_accounts and not self.escrow_accounts[order_id]['rider_half_paid']:
            self.escrow_accounts[order_id]['rider_half_paid'] = True
            return True
        return False
    
    def pay_rider_full(self, order_id: str):
        escrow = self.escrow_accounts.get(order_id)
        if escrow and escrow['rider_half_paid'] and not escrow['rider_full_paid']:
            escrow['rider_full_paid'] = True
            return True
        return False

class DeliveryPlatform:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, gps_tolerance_meters: float = 50, rider_timeout_min: int = 5):
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.restaurants: Dict[str, Restaurant] = {}
        self.riders: Dict[str, Rider] = {}
        self.escrow = EscrowSystem()
        self.gps_tolerance = gps_tolerance_meters
        self.rider_acceptance_timeout = timedelta(minutes=rider_timeout_min)
        self.rider_queue: List[str] = []
    
    def register_customer(self, name, email, phone, location):
        customer = Customer(str(uuid.uuid4()), name, email, phone, location)
        self.customers[customer.id] = customer
        return customer
    
    def register_restaurant(self, name, location, email, phone, bank_account):
        restaurant = Restaurant(str(uuid.uuid4()), name, location, email, phone, bank_account)
        self.restaurants[restaurant.id] = restaurant
        return restaurant
    
    def register_rider(self, name, email, phone, location, bank_account):
        rider = Rider(str(uuid.uuid4()), name, email, phone, location, bank_account)
        self.riders[rider.id] = rider
        self.rider_queue.append(rider.id)
        return rider
    
    def place_order(self, customer, restaurant, items, delivery_fee):
        order_id = str(uuid.uuid4())
        total = sum(i.price * i.quantity for i in items) + delivery_fee
        order = Order(order_id, customer, restaurant, items, total, delivery_fee,
                     OrderStatus.PENDING_PAYMENT, PaymentStatus.PENDING)
        self.orders[order_id] = order
        order.add_status(OrderStatus.PENDING_PAYMENT, "Order created")
        return order
    
    def process_payment(self, order):
        restaurant_cut = sum(i.price * i.quantity for i in order.items)
        self.escrow.create_escrow(order.id, order.total_amount, restaurant_cut, order.delivery_fee)
        order.payment_status = PaymentStatus.ESCROWED
        order.add_status(OrderStatus.PAYMENT_ESCROWED, "Payment secured")
        order.add_status(OrderStatus.RESTAURANT_NOTIFIED, f"Restaurant {order.restaurant.name} notified")
        return True
    
    def restaurant_confirm_order(self, order):
        if order.status != OrderStatus.RESTAURANT_NOTIFIED:
            return False
        if self.escrow.pay_restaurant(order.id):
            order.payment_status = PaymentStatus.RESTAURANT_PAID
            order.add_status(OrderStatus.RESTAURANT_CONFIRMED, "Restaurant confirmed and paid")
            self._seek_rider(order)
            return True
        return False
    
    def _seek_rider(self, order):
        order.add_status(OrderStatus.SEEKING_RIDER, "Finding rider")
        self._assign_next_rider(order)
    
    def _assign_next_rider(self, order):
        if not self.rider_queue:
            return False
        rider_id = self.rider_queue.pop(0)
        rider = self.riders.get(rider_id)
        if not rider or not rider.is_available:
            return self._assign_next_rider(order)
        order.assigned_rider = rider
        order.rider_acceptance_deadline = datetime.now() + self.rider_acceptance_timeout
        order.add_status(OrderStatus.RIDER_ASSIGNED, f"Assigned to {rider.name}")
        return True
    
    def rider_accept_order(self, order):
        if order.status != OrderStatus.RIDER_ASSIGNED or not order.assigned_rider:
            return False
        order.assigned_rider.is_available = False
        order.add_status(OrderStatus.RIDER_EN_ROUTE_PICKUP, "Rider en route to restaurant")
        return True
    
    def check_rider_at_restaurant(self, order, rider_location):
        if order.status != OrderStatus.RIDER_EN_ROUTE_PICKUP:
            return False
        if rider_location.distance_to(order.restaurant.location) <= self.gps_tolerance:
            order.add_status(OrderStatus.RIDER_AT_RESTAURANT, "Rider at restaurant")
            return True
        return False
    
    def confirm_pickup(self, order):
        if order.status != OrderStatus.RIDER_AT_RESTAURANT:
            return False
        if self.escrow.pay_rider_half(order.id):
            order.payment_status = PaymentStatus.RIDER_HALF_PAID
            order.add_status(OrderStatus.ORDER_PICKED_UP, "Picked up, rider paid 50%")
            order.add_status(OrderStatus.RIDER_EN_ROUTE_DELIVERY, "En route to customer")
            return True
        return False
    
    def check_rider_at_delivery(self, order, rider_location):
        if order.status != OrderStatus.RIDER_EN_ROUTE_DELIVERY:
            return False
        if rider_location.distance_to(order.customer.delivery_location) <= self.gps_tolerance:
            order.add_status(OrderStatus.RIDER_AT_DELIVERY, "Rider at delivery location")
            return True
        return False
    
    def confirm_delivery(self, order):
        if order.status != OrderStatus.RIDER_AT_DELIVERY:
            return False
        if self.escrow.pay_rider_full(order.id):
            order.payment_status = PaymentStatus.RIDER_FULL_PAID
            order.add_status(OrderStatus.DELIVERED, "Delivered, rider paid 100%")
            order.assigned_rider.total_deliveries += 1
            order.assigned_rider.is_available = True
            self.rider_queue.append(order.assigned_rider.id)
            return True
        return False
    
    def get_order_journey(self, order):
        journey_map = {
            OrderStatus.PENDING_PAYMENT: {"step": 1, "label": "Payment Processing"},
            OrderStatus.PAYMENT_ESCROWED: {"step": 2, "label": "Payment Secured"},
            OrderStatus.RESTAURANT_NOTIFIED: {"step": 3, "label": "Restaurant Notified"},
            OrderStatus.RESTAURANT_CONFIRMED: {"step": 4, "label": "Restaurant Confirmed"},
            OrderStatus.SEEKING_RIDER: {"step": 5, "label": "Finding Rider"},
            OrderStatus.RIDER_ASSIGNED: {"step": 6, "label": "Rider Assigned"},
            OrderStatus.RIDER_EN_ROUTE_PICKUP: {"step": 7, "label": "Rider → Restaurant"},
            OrderStatus.RIDER_AT_RESTAURANT: {"step": 8, "label": "At Restaurant"},
            OrderStatus.ORDER_PICKED_UP: {"step": 9, "label": "Order Picked Up"},
            OrderStatus.RIDER_EN_ROUTE_DELIVERY: {"step": 10, "label": "Rider → You"},
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
            "history": order.status_history
        }

def init_demo_data():
    """Initialize demo data - called once"""
    platform = DeliveryPlatform.get_instance()
    
    if not platform.customers:
        platform.register_customer(
            "Alice Johnson", "alice@example.com", "+256-123-4567",
            Location(0.3476, 32.5825, "123 Main St, Kampala"))
    
    if not platform.restaurants:
        platform.register_restaurant(
            "Mama Mia's Pizza", Location(0.3426, 32.5775, "45 Restaurant Row, Kampala"),
            "info@mamamia.com", "+256-987-6543", "BANK-REST-001")
    
    if not platform.riders:
        platform.register_rider(
            "Bob Rider", "bob@delivery.com", "+256-555-0001",
            Location(0.3450, 32.5800, "Central Kampala"), "BANK-RIDER-001")
        platform.register_rider(
            "Charlie Courier", "charlie@delivery.com", "+256-555-0002",
            Location(0.3460, 32.5810, "Near Central"), "BANK-RIDER-002")
