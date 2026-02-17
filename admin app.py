"""Admin App - Monitor platform"""
import streamlit as st
from delivery_platform import DeliveryPlatform, OrderStatus, init_demo_data

st.set_page_config(page_title="Admin - Quad-Mesh", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
.main-header {background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

platform = DeliveryPlatform.get_instance()
init_demo_data()

st.markdown('<div class="main-header"><h1>⚙️ Admin Portal</h1>'
            '<p>Platform Overview & Management</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Admin Menu")
    page = st.radio("", ["Overview", "Orders", "Users", "Payments", "Settings"])

if page == "Overview":
    st.markdown("## 📊 Platform Overview")
    
    completed = len([o for o in platform.orders.values() if o.status == OrderStatus.DELIVERED])
    active = len([o for o in platform.orders.values() if o.status.value not in ['delivered']])
    available_riders = len([r for r in platform.riders.values() if r.is_available])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", len(platform.orders))
    col2.metric("Completed", completed)
    col3.metric("Active", active)
    col4.metric("Available Riders", f"{available_riders}/{len(platform.riders)}")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", len(platform.customers))
    col2.metric("Restaurants", len(platform.restaurants))
    col3.metric("Riders", len(platform.riders))
    
    st.markdown("---")
    st.markdown("### 📋 Recent Orders")
    
    for order in list(platform.orders.values())[-10:]:
        col1, col2, col3, col4 = st.columns(4)
        col1.write(f"#{order.id[:8]}")
        col2.write(order.restaurant.name)
        col3.write(order.status.value.replace('_', ' ').title())
        col4.write(f"{order.total_amount:,} UGX")

elif page == "Orders":
    st.markdown("## 📦 All Orders")
    
    for order in reversed(list(platform.orders.values())):
        j = platform.get_order_journey(order)
        with st.expander(f"Order #{order.id[:8]} - {j['current_label']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Customer:** {order.customer.name}")
                st.write(f"**Restaurant:** {order.restaurant.name}")
            with col2:
                st.progress(j['progress_percentage'] / 100)
                st.write(f"{j['current_step']}/12 steps")
            with col3:
                st.write(f"**Total:** {order.total_amount:,} UGX")
                if order.assigned_rider:
                    st.write(f"**Rider:** {order.assigned_rider.name}")

elif page == "Users":
    tab1, tab2, tab3 = st.tabs(["Customers", "Restaurants", "Riders"])
    
    with tab1:
        st.markdown("### 👤 Customers")
        for customer in platform.customers.values():
            with st.expander(f"{customer.name}"):
                st.write(f"**Email:** {customer.email}")
                st.write(f"**Phone:** {customer.phone}")
                orders = [o for o in platform.orders.values() if o.customer.id == customer.id]
                st.metric("Total Orders", len(orders))
    
    with tab2:
        st.markdown("### 🏪 Restaurants")
        for restaurant in platform.restaurants.values():
            with st.expander(f"{restaurant.name}"):
                st.write(f"**Email:** {restaurant.email}")
                st.write(f"**Phone:** {restaurant.phone}")
                orders = [o for o in platform.orders.values() if o.restaurant.id == restaurant.id]
                st.metric("Total Orders", len(orders))
    
    with tab3:
        st.markdown("### 🏍️ Riders")
        for rider in platform.riders.values():
            status = "🟢" if rider.is_available else "🔴"
            with st.expander(f"{status} {rider.name}"):
                st.write(f"**Email:** {rider.email}")
                st.write(f"**Phone:** {rider.phone}")
                st.metric("Deliveries", rider.total_deliveries)
                st.metric("Rating", f"{rider.rating:.1f} ⭐")

elif page == "Payments":
    st.markdown("## 💰 Payments & Escrow")
    
    total_escrowed = sum(a['total'] for a in platform.escrow.escrow_accounts.values())
    restaurant_paid = sum(a['restaurant_amount'] for a in platform.escrow.escrow_accounts.values() if a['restaurant_paid'])
    rider_paid = sum(a['rider_amount'] for a in platform.escrow.escrow_accounts.values() if a['rider_full_paid'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("In Escrow", f"{total_escrowed:,} UGX")
    col2.metric("Paid to Restaurants", f"{restaurant_paid:,} UGX")
    col3.metric("Paid to Riders", f"{rider_paid:,} UGX")

else:  # Settings
    st.markdown("## ⚙️ Platform Settings")
    
    st.number_input("GPS Tolerance (meters)", 10, 200, int(platform.gps_tolerance), 10)
    st.number_input("Rider Timeout (minutes)", 1, 15, 5, 1)
    
    st.info(f"**Current Settings:**\n- GPS Tolerance: {platform.gps_tolerance}m\n- Rider Timeout: 5 minutes")
