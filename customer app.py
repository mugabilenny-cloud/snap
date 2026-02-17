"""Customer App - Place and track orders"""
import streamlit as st
from delivery_platform import DeliveryPlatform, OrderItem, init_demo_data

st.set_page_config(page_title="Customer - Quad-Mesh", page_icon="👤", layout="wide")

st.markdown("""
<style>
.main-header {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# Initialize
platform = DeliveryPlatform.get_instance()
init_demo_data()

customer = list(platform.customers.values())[0]

# Header
st.markdown(f'<div class="main-header"><h1>👤 Customer Portal</h1>'
            f'<p>Welcome, {customer.name}!</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📱 Customer Menu")
    page = st.radio("", ["Place Order", "Track Orders", "Order History"])
    st.markdown("---")
    st.info(f"📧 {customer.email}\n📱 {customer.phone}")

if page == "Place Order":
    st.markdown("## 📝 Place New Order")
    
    restaurant = list(platform.restaurants.values())[0]
    st.info(f"🏪 **{restaurant.name}**\n📍 {restaurant.location.address}")
    
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        item_name = st.text_input("Item Name", "Margherita Pizza")
    with col2:
        item_qty = st.number_input("Quantity", 1, 10, 1)
    with col3:
        item_price = st.number_input("Price (UGX)", 1000, 100000, 25000, 1000)
    with col4:
        st.write("")
        st.write("")
        if st.button("➕"):
            st.session_state.cart.append({"name": item_name, "qty": item_qty, "price": item_price})
            st.rerun()
    
    if st.session_state.cart:
        st.markdown("### 🛒 Your Cart")
        total = 0
        for i, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            col1.write(item['name'])
            col2.write(f"x{item['qty']}")
            item_total = item['price'] * item['qty']
            col3.write(f"{item_total:,} UGX")
            total += item_total
            if col4.button("🗑️", key=f"del_{i}"):
                st.session_state.cart.pop(i)
                st.rerun()
        
        delivery_fee = 5000
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Subtotal:** {total:,} UGX")
            st.write(f"**Delivery:** {delivery_fee:,} UGX")
            st.markdown(f"### **Total: {total + delivery_fee:,} UGX**")
        
        if st.button("🚀 Place Order", type="primary", use_container_width=True):
            items = [OrderItem(i['name'], i['qty'], i['price']) for i in st.session_state.cart]
            order = platform.place_order(customer, restaurant, items, delivery_fee)
            platform.process_payment(order)
            st.session_state.cart = []
            st.success(f"✅ Order placed! Order #{order.id[:8]}")
            st.balloons()
            st.rerun()

elif page == "Track Orders":
    st.markdown("## 📦 Track Your Orders")
    
    orders = [o for o in platform.orders.values() 
              if o.customer.id == customer.id 
              and o.status.value not in ['delivered']]
    
    if not orders:
        st.info("No active orders to track.")
    
    for order in orders:
        j = platform.get_order_journey(order)
        with st.expander(f"📦 Order #{order.id[:8]} - {j['current_label']}", expanded=True):
            st.progress(j['progress_percentage'] / 100)
            st.markdown(f"### {j['current_label']}")
            st.write(f"**Step {j['current_step']} of {j['total_steps']}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Order Details**")
                for item in order.items:
                    st.write(f"• {item.quantity}x {item.name}")
                st.write(f"**Total:** {order.total_amount:,} UGX")
            
            with col2:
                st.markdown("**Delivery Info**")
                if j['assigned_rider']:
                    st.write(f"🏍️ **Rider:** {j['assigned_rider']}")
                else:
                    st.write("🔍 Finding rider...")
            
            with st.expander("📜 Status History"):
                for h in reversed(j['history']):
                    st.caption(f"• {h['note']} - {h['timestamp'][:19]}")

else:  # Order History
    st.markdown("## 📚 Order History")
    
    orders = [o for o in platform.orders.values() if o.customer.id == customer.id]
    
    if not orders:
        st.info("No orders yet. Place your first order!")
    
    for order in reversed(orders):
        status_emoji = "✅" if order.status.value == "delivered" else "🔄"
        with st.expander(f"{status_emoji} Order #{order.id[:8]} - {order.created_at.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Restaurant:** {order.restaurant.name}")
                for item in order.items:
                    st.write(f"• {item.quantity}x {item.name}")
            with col2:
                st.write(f"**Total:** {order.total_amount:,} UGX")
                st.write(f"**Status:** {order.status.value.replace('_', ' ').title()}")
