"""Rider App - Accept and deliver orders"""
import streamlit as st
from delivery_platform import DeliveryPlatform, OrderStatus, init_demo_data

st.set_page_config(page_title="Rider - Quad-Mesh", page_icon="🏍️", layout="wide")

st.markdown("""
<style>
.main-header {background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

platform = DeliveryPlatform.get_instance()
init_demo_data()

rider = list(platform.riders.values())[0]

st.markdown(f'<div class="main-header"><h1>🏍️ Rider Portal</h1>'
            f'<p>{rider.name} • {"🟢 Available" if rider.is_available else "🔴 On Delivery"}</p></div>', 
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🏍️ Rider Menu")
    page = st.radio("", ["Available Deliveries", "Current Delivery", "Delivery History", "Earnings"])
    st.markdown("---")
    st.metric("Rating", f"{rider.rating:.1f} ⭐")
    st.metric("Deliveries", rider.total_deliveries)

if page == "Available Deliveries":
    st.markdown("## 📬 Delivery Requests")
    
    if not rider.is_available:
        st.warning("⚠️ You're currently on a delivery. Complete it to receive new requests.")
    
    assigned = [o for o in platform.orders.values() 
                if o.assigned_rider and o.assigned_rider.id == rider.id 
                and o.status == OrderStatus.RIDER_ASSIGNED]
    
    if not assigned:
        st.success("✅ No pending requests. You'll be notified when orders come in!")
    
    for order in assigned:
        with st.container():
            st.markdown(f"### 📦 Delivery Request #{order.id[:8]}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📍 Pickup**")
                st.write(order.restaurant.name)
                st.write(order.restaurant.location.address)
            
            with col2:
                st.markdown("**📍 Delivery**")
                st.write(order.customer.delivery_location.address)
            
            with col3:
                st.markdown("**💰 Earnings**")
                st.write(f"**{order.delivery_fee:,} UGX**")
                st.caption("50% on pickup\n50% on delivery")
            
            if st.button(f"✅ Accept Delivery #{order.id[:8]}", key=order.id, type="primary"):
                if platform.rider_accept_order(order):
                    st.success("✅ Delivery accepted!")
                    st.rerun()
            
            st.markdown("---")

elif page == "Current Delivery":
    st.markdown("## 📦 Active Delivery")
    
    active = [o for o in platform.orders.values() 
              if o.assigned_rider and o.assigned_rider.id == rider.id 
              and o.status.value in ['rider_en_route_pickup', 'rider_at_restaurant', 
                                     'order_picked_up', 'rider_en_route_delivery', 'rider_at_delivery']]
    
    if not active:
        st.info("No active delivery. Check 'Available Deliveries' for new requests!")
    else:
        order = active[0]
        j = platform.get_order_journey(order)
        
        st.progress(j['progress_percentage'] / 100)
        st.markdown(f"## {j['current_label']}")
        st.write(f"**Step {j['current_step']} of {j['total_steps']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Restaurant**")
            st.write(order.restaurant.name)
            st.write(order.restaurant.location.address)
            st.markdown("**Items**")
            for item in order.items:
                st.write(f"• {item.quantity}x {item.name}")
        
        with col2:
            st.markdown("**Customer**")
            st.write(order.customer.delivery_location.address)
            st.markdown("**Earnings**")
            if order.payment_status.value == 'rider_half_paid':
                st.success(f"✅ {order.delivery_fee/2:,.0f} UGX received")
                st.info(f"⏳ {order.delivery_fee/2:,.0f} UGX on delivery")
            else:
                st.info(f"💰 {order.delivery_fee:,} UGX total")
        
        st.markdown("---")
        st.markdown("### 🛰️ GPS Actions")
        
        if order.status == OrderStatus.RIDER_EN_ROUTE_PICKUP:
            if st.button("🎯 I've Arrived at Restaurant", type="primary", use_container_width=True):
                platform.check_rider_at_restaurant(order, order.restaurant.location)
                st.rerun()
        
        elif order.status == OrderStatus.RIDER_AT_RESTAURANT:
            if st.button("📦 Confirm Pickup", type="primary", use_container_width=True):
                if platform.confirm_pickup(order):
                    st.success(f"✅ {order.delivery_fee/2:,.0f} UGX paid!")
                    st.balloons()
                    st.rerun()
        
        elif order.status == OrderStatus.RIDER_EN_ROUTE_DELIVERY:
            if st.button("🎯 I've Arrived at Customer", type="primary", use_container_width=True):
                platform.check_rider_at_delivery(order, order.customer.delivery_location)
                st.rerun()
        
        elif order.status == OrderStatus.RIDER_AT_DELIVERY:
            if st.button("✅ Complete Delivery", type="primary", use_container_width=True):
                if platform.confirm_delivery(order):
                    st.success(f"🎉 {order.delivery_fee/2:,.0f} UGX paid!")
                    st.balloons()
                    st.rerun()

elif page == "Delivery History":
    st.markdown("## 📚 Delivery History")
    
    deliveries = [o for o in platform.orders.values() 
                  if o.assigned_rider and o.assigned_rider.id == rider.id]
    
    if not deliveries:
        st.info("No deliveries yet.")
    
    for order in reversed(deliveries):
        status_emoji = "✅" if order.status.value == "delivered" else "🔄"
        with st.expander(f"{status_emoji} #{order.id[:8]} - {order.created_at.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Pickup:** {order.restaurant.name}")
            with col2:
                st.write(f"**Status:** {order.status.value.replace('_', ' ').title()}")
            with col3:
                st.write(f"**Earned:** {order.delivery_fee:,} UGX")

else:  # Earnings
    st.markdown("## 💰 Earnings Dashboard")
    
    deliveries = [o for o in platform.orders.values() 
                  if o.assigned_rider and o.assigned_rider.id == rider.id 
                  and o.status == OrderStatus.DELIVERED]
    
    earnings = sum(o.delivery_fee for o in deliveries)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Completed Deliveries", len(deliveries))
    col2.metric("Total Earnings", f"{earnings:,} UGX")
    if deliveries:
        col3.metric("Avg per Delivery", f"{earnings/len(deliveries):,.0f} UGX")
