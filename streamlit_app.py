"""
Quad-Mesh Delivery Platform - Streamlit App
Main entry point with user type selection
"""

import streamlit as st
from datetime import datetime
import sys

# Page configuration
st.set_page_config(
    page_title="Quad-Mesh Delivery Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .user-card {
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem;
    }
    
    .user-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .customer-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .restaurant-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .rider-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    .admin-card {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'platform' not in st.session_state:
    from delivery_platform import DeliveryPlatform, Location
    st.session_state.platform = DeliveryPlatform(
        gps_tolerance_meters=50,
        rider_acceptance_timeout_minutes=5
    )
    st.session_state.initialized = False

if 'user_type' not in st.session_state:
    st.session_state.user_type = None

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Initialize demo data if needed
def initialize_demo_data():
    if not st.session_state.initialized:
        from delivery_platform import Location
        
        # Create demo users
        customer = st.session_state.platform.register_customer(
            "Alice Johnson",
            "alice@example.com",
            "+256-123-4567",
            Location(0.3476, 32.5825, "123 Main St, Kampala")
        )
        
        restaurant = st.session_state.platform.register_restaurant(
            "Mama Mia's Pizza",
            Location(0.3426, 32.5775, "45 Restaurant Row, Kampala"),
            "info@mamamia.com",
            "+256-987-6543",
            "BANK-ACCT-REST-001"
        )
        
        rider1 = st.session_state.platform.register_rider(
            "Bob Rider",
            "bob@delivery.com",
            "+256-555-0001",
            Location(0.3450, 32.5800, "Central Kampala"),
            "BANK-ACCT-RIDER-001"
        )
        
        rider2 = st.session_state.platform.register_rider(
            "Charlie Courier",
            "charlie@delivery.com",
            "+256-555-0002",
            Location(0.3460, 32.5810, "Near Central"),
            "BANK-ACCT-RIDER-002"
        )
        
        # Store in session state
        st.session_state.demo_customer = customer
        st.session_state.demo_restaurant = restaurant
        st.session_state.demo_rider1 = rider1
        st.session_state.demo_rider2 = rider2
        st.session_state.initialized = True

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Quad-Mesh Delivery Platform</h1>
        <p>Four-sided marketplace with GPS-based escrow system</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize demo data
    initialize_demo_data()
    
    # If user type not selected, show selection
    if st.session_state.user_type is None:
        st.markdown("### Select Your User Type")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="user-card customer-card">
                <h2>👤</h2>
                <h3>Customer</h3>
                <p>Place orders and track deliveries</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Enter as Customer", key="customer_btn"):
                st.session_state.user_type = "customer"
                st.session_state.current_user = st.session_state.demo_customer
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="user-card restaurant-card">
                <h2>🏪</h2>
                <h3>Restaurant</h3>
                <p>Manage incoming orders</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Enter as Restaurant", key="restaurant_btn"):
                st.session_state.user_type = "restaurant"
                st.session_state.current_user = st.session_state.demo_restaurant
                st.rerun()
        
        with col3:
            st.markdown("""
            <div class="user-card rider-card">
                <h2>🏍️</h2>
                <h3>Rider</h3>
                <p>Accept and deliver orders</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Enter as Rider", key="rider_btn"):
                st.session_state.user_type = "rider"
                st.session_state.current_user = st.session_state.demo_rider1
                st.rerun()
        
        with col4:
            st.markdown("""
            <div class="user-card admin-card">
                <h2>⚙️</h2>
                <h3>Admin</h3>
                <p>Monitor platform operations</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Enter as Admin", key="admin_btn"):
                st.session_state.user_type = "admin"
                st.rerun()
        
        # Platform stats
        st.markdown("---")
        st.markdown("### 📊 Platform Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", len(st.session_state.platform.orders))
        with col2:
            st.metric("Restaurants", len(st.session_state.platform.restaurants))
        with col3:
            st.metric("Riders", len(st.session_state.platform.riders))
        with col4:
            st.metric("Customers", len(st.session_state.platform.customers))
    
    else:
        # Show selected user dashboard
        if st.session_state.user_type == "customer":
            from pages import customer_dashboard
            customer_dashboard.show()
        elif st.session_state.user_type == "restaurant":
            from pages import restaurant_dashboard
            restaurant_dashboard.show()
        elif st.session_state.user_type == "rider":
            from pages import rider_dashboard
            rider_dashboard.show()
        elif st.session_state.user_type == "admin":
            from pages import admin_dashboard
            admin_dashboard.show()

if __name__ == "__main__":
    main()
