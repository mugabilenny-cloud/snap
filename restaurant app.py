"""Restaurant App - Manage orders"""
import streamlit as st
from delivery_platform import DeliveryPlatform, OrderStatus, init_demo_data

st.set_page_config(page_title="Restaurant - Quad-Mesh", page_icon="🏪", layout="wide")

st.markdown("""
<style>
.main-header {background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

platform = DeliveryPlatform.get_instance()
init_demo_data()

restaurant = list(platform.restaurants.values())[0]

st.markdown(f'<div class="main-header"><h1>🏪 Restaurant Portal</h1>'
            f'<h3>{restaurant.name}</h3></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🏪 Restaurant Menu")
    page = st.radio("", ["Pending Orders", "Active Orders", "Order History", "Analytics"])
    st.markdown("---")
    orders = [o for o in platform.orders.values() if o.restaurant.id == restaurant.id]
    completed = len([o for o in orders if o.status == OrderStatus.DELIVERED])
    st.metric("Total Orders", len(orders))
    st.metric("Completed", completed)

if page == "Pending Orders":
    st.markdown("## 📋 Orders Awaiting Confirmation")
    
    pending = [o for o in platform.orders.values() 
               if o.restaurant.id == restaurant.id 
               and o.status == OrderStatus.RESTAURANT_NOTIFIED]
    
    if not pending:
        st.success("✅ No pending orders! All caught up.")
    else:
        st.warning(f"⚠️ You have {len(pending)} orders waiting!")
    
    for order in pending:
        with st.container():
            st.markdown(f"### 📦 Order #{order.id[:8]}")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Customer:** {order.customer.name}")
                st.write(f"**Phone:** {order.customer.phone}")
                st.markdown("**Items:**")
                for item in order.items:
                    st.write(f"• {item.quantity}x {item.name} - {item.price:,} UGX")
            
            with col2:
                item_total = sum(i.price * i.quantity for i in order.items)
                st.write(f"**Order Value:** {item_total:,} UGX")
                st.write(f"**Delivery Fee:** {order.delivery_fee:,} UGX")
                st.write(f"**Total:** {order.total_amount:,} UGX")
                st.info("💰 You'll be paid immediately upon confirmation")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Confirm", key=f"confirm_{order.id}", type="primary"):
                    if platform.restaurant_confirm_order(order):
                        st.success(f"✅ Confirmed! {item_total:,} UGX sent to {restaurant.bank_account}")
                        st.balloons()
                        st.rerun()
            
            st.markdown("---")

elif page == "Active Orders":
    st.markdown("## 🔄 Active Orders")
    
    active = [o for o in platform.orders.values() 
              if o.restaurant.id == restaurant.id 
              and o.status.value in ['restaurant_confirmed', 'seeking_rider', 'rider_assigned',
                                     'rider_en_route_pickup', 'rider_at_restaurant', 'order_picked_up',
                                     'rider_en_route_delivery', 'rider_at_delivery']]
    
    if not active:
        st.info("No active orders.")
    
    for order in active:
        j = platform.get_order_journey(order)
        with st.expander(f"Order #{order.id[:8]} - {j['current_label']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Items**")
                for item in order.items:
                    st.write(f"{item.quantity}x {item.name}")
            with col2:
                st.markdown("**Status**")
                st.progress(j['progress_percentage'] / 100)
                st.write(j['current_label'])
            with col3:
                st.markdown("**Rider**")
                if order.assigned_rider:
                    st.write(f"🏍️ {order.assigned_rider.name}")
                else:
                    st.write("Finding rider...")

elif page == "Order History":
    st.markdown("## 📚 Order History")
    
    orders = [o for o in platform.orders.values() if o.restaurant.id == restaurant.id]
    
    if not orders:
        st.info("No orders yet.")
    
    for order in reversed(orders):
        status_emoji = "✅" if order.status.value == "delivered" else "🔄"
        with st.expander(f"{status_emoji} #{order.id[:8]} - {order.created_at.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                for item in order.items:
                    st.write(f"{item.quantity}x {item.name}")
            with col2:
                st.write(f"**Status:** {order.status.value.replace('_', ' ').title()}")
            with col3:
                revenue = sum(i.price * i.quantity for i in order.items)
                st.write(f"**Revenue:** {revenue:,} UGX")

else:  # Analytics
    st.markdown("## 📊 Analytics")
    
    orders = [o for o in platform.orders.values() if o.restaurant.id == restaurant.id]
    completed = [o for o in orders if o.status == OrderStatus.DELIVERED]
    revenue = sum(sum(i.price * i.quantity for i in o.items) for o in completed)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", len(orders))
    col2.metric("Completed", len(completed))
    col3.metric("Total Revenue", f"{revenue:,} UGX")
    if completed:
        col4.metric("Avg Order", f"{revenue/len(completed):,.0f} UGX")
