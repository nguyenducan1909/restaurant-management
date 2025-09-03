# --- YÊU CẦU 2: DAO CHO NHÀ HÀNG / THỰC ĐƠN / GIỎ HÀNG ---
from sqlalchemy import or_
from QuanLyNhaHang.app import db
from models import Restaurant, Item, Cart, CartItem, Order, OrderItem, Payment
from decimal import Decimal
from sqlalchemy import or_, func

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


#DDD
def get_active_cart_detail(user_id: int, restaurant_id: int):
    cart = get_or_create_active_cart(user_id, restaurant_id)
    rows = db.session.query(
        CartItem.item_id,
        CartItem.quantity,
        Item.name.label('item_name'),
        Item.price.label('unit_price'),
        (Item.price * CartItem.quantity).label('line_total')
    ).join(Item, Item.id == CartItem.item_id).filter(CartItem.cart_id == cart.id).all()

    items = [
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "unit_price": Decimal(r.unit_price),
            "quantity": int(r.quantity),
            "line_total": Decimal(r.line_total),
        } for r in rows
    ]
    total_amount = sum(i["line_total"] for i in items) if items else Decimal('0')
    return cart, items, total_amount

def update_cart_item_quantity(cart_id: int, item_id: int, quantity: int):
    row = CartItem.query.filter_by(cart_id=cart_id, item_id=item_id).first()
    if not row:
        return False, "Không tìm thấy món trong giỏ"
    if quantity <= 0:
        db.session.delete(row)
    else:
        row.quantity = quantity
    db.session.commit()
    return True, "Cập nhật giỏ hàng thành công"

def remove_item_from_cart(cart_id: int, item_id: int):
    row = CartItem.query.filter_by(cart_id=cart_id, item_id=item_id).first()
    if not row:
        return False, "Không tìm thấy món trong giỏ"
    db.session.delete(row)
    db.session.commit()
    return True, "Đã xóa món khỏi giỏ"


# ----------------
# ORDER & PAYMENT
# ----------------
def create_order_from_cart(user_id: int, restaurant_id: int, ship_name: str, ship_phone: str, ship_address: str, payment_method: str):
    cart, items, total = get_active_cart_detail(user_id, restaurant_id)
    if not items:
        return False, "Giỏ hàng trống", None

    order = Order(
        user_id=user_id,
        restaurant_id=restaurant_id,
        status="PENDING",
        payment_status="UNPAID",
        payment_method=payment_method,
        ship_name=(ship_name or '').strip()[:120],
        ship_phone=(ship_phone or '').strip()[:30],
        ship_address=(ship_address or '').strip()[:255],
        total_amount=total
    )
    db.session.add(order)
    db.session.flush()  # có order.id

    for it in items:
        db.session.add(OrderItem(
            order_id=order.id,
            item_id=it["item_id"],
            item_name=it["item_name"],
            unit_price=it["unit_price"],
            quantity=it["quantity"],
            line_total=it["line_total"]
        ))

    # COD => thanh toán thành công ngay
    if payment_method == "COD":
        order.payment_status = "PAID"
        pay = Payment(order_id=order.id, amount=total, method="COD", status="SUCCEEDED", paid_at=func.now())
        db.session.add(pay)
        cart.status = "CHECKED_OUT"
        db.session.commit()
        return True, "Đặt hàng thành công (COD)", order

    # method khác: tạo giao dịch chờ
    pay = Payment(order_id=order.id, amount=total, method=payment_method, status="PENDING", paid_at=None)
    db.session.add(pay)
    cart.status = "CHECKED_OUT"
    db.session.commit()
    return True, "Tạo đơn hàng thành công, chuyển đến cổng thanh toán", order

def update_payment_result(order_id: int, result: str):
    order = Order.query.get(order_id)
    if not order:
        return False, "Không tìm thấy đơn hàng"
    pay = Payment.query.filter_by(order_id=order.id).first()
    if not pay:
        return False, "Thiếu giao dịch thanh toán"

    if result == "success":
        pay.status = "SUCCEEDED"
        order.payment_status = "PAID"
        pay.paid_at = func.now()
    else:
        pay.status = "FAILED"
    db.session.commit()
    return True, "Cập nhật thanh toán thành công"

# ----------------
# Helper: lấy order & payment để hiển thị trang chuyển khoản
# ----------------
def get_payment_info(order_id: int):
    """Trả về (order, payment) theo order_id, hoặc (None, None) nếu không có."""
    order = Order.query.get(order_id)
    if not order:
        return None, None
    payment = Payment.query.filter_by(order_id=order.id).first()
    return order, payment