# --- YÊU CẦU 2: DAO CHO NHÀ HÀNG / THỰC ĐƠN / GIỎ HÀNG ---
from sqlalchemy import or_
from QuanLyNhaHang.app import db
from models import Restaurant, Item, Cart, CartItem

def get_restaurants(q=None, is_open=None):
    query = Restaurant.query
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Restaurant.name.ilike(like), Restaurant.address.ilike(like)))
    if is_open in ("0", "1"):
        query = query.filter(Restaurant.is_open == bool(int(is_open)))
    return query.order_by(Restaurant.created_at.desc()).all()

def get_restaurant_by_id(restaurant_id: int):
    return Restaurant.query.get(restaurant_id)

def get_items_for_restaurant(restaurant_id: int):
    return (
        Item.query
        .filter(Item.restaurant_id == restaurant_id, Item.is_available.is_(True))
        .order_by(Item.created_at.desc())
        .all()
    )

def get_or_create_active_cart(user_id: int, restaurant_id: int):
    cart = (
        Cart.query
        .filter(Cart.user_id == user_id, Cart.restaurant_id == restaurant_id, Cart.status == "ACTIVE")
        .order_by(Cart.created_at.desc())
        .first()
    )
    if not cart:
        cart = Cart(user_id=user_id, restaurant_id=restaurant_id, status="ACTIVE")
        db.session.add(cart)
        db.session.commit()
    return cart

def add_item_to_cart(user_id: int, restaurant_id: int, item_id: int, qty: int = 1):
    # Validate item
    item = Item.query.get(item_id)
    if not item or item.restaurant_id != restaurant_id or not item.is_available:
        return False, "Món không hợp lệ hoặc đã ngừng bán"

    cart = get_or_create_active_cart(user_id, restaurant_id)

    row = CartItem.query.filter_by(cart_id=cart.id, item_id=item.id).first()
    if row:
        row.quantity += max(1, qty)
    else:
        db.session.add(CartItem(cart_id=cart.id, item_id=item.id, quantity=max(1, qty)))

    db.session.commit()
    return True, "Đã thêm vào giỏ"
