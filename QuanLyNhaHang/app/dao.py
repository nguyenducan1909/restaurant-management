# --- DAO: Nhà hàng / Thực đơn / Giỏ hàng / Đơn hàng / Thanh toán ---
from decimal import Decimal
from sqlalchemy import or_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from QuanLyNhaHang.app import db
from models import User, Restaurant, Item, Cart, CartItem, Order, OrderItem, Payment


# ----------------
# RESTAURANT & MENU
# ----------------
def get_restaurants(q: str | None = None, is_open: str | None = None):
    """
    Trả về danh sách nhà hàng, có thể lọc theo từ khóa q (tên/địa chỉ) và trạng thái mở cửa.
    - is_open: "1" chỉ mở cửa, "0" chỉ đóng cửa, None = tất cả.
    """
    query = Restaurant.query
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Restaurant.name.ilike(like), Restaurant.address.ilike(like)))
    if is_open in ("0", "1"):
        query = query.filter(Restaurant.is_open == bool(int(is_open)))
    return query.order_by(Restaurant.created_at.desc()).all()


def get_restaurant_by_id(restaurant_id: int):
    # Với Flask-SQLAlchemy 3.x có thể dùng db.session.get(Restaurant, id)
    return Restaurant.query.get(restaurant_id)


def get_items_for_restaurant(restaurant_id: int):
    return (
        Item.query
        .filter(
            Item.restaurant_id == restaurant_id,
            Item.is_available.is_(True)
        )
        .order_by(Item.created_at.desc())
        .all()
    )


# ----------------
# USERS (đăng ký/đăng nhập)
# ----------------
def get_user_by_username(username: str):
    return User.query.filter_by(username=username).first()


def get_user_by_email(email: str):
    return User.query.filter_by(email=email).first()


def create_user(username: str, email: str, password: str, full_name: str | None = None, phone: str | None = None):
    # Kiểm tra trùng
    if get_user_by_username(username):
        return False, "Tên đăng nhập đã tồn tại"
    if get_user_by_email(email):
        return False, "Email đã được sử dụng"

    try:
        user = User(
            username=username,
            email=email,
            full_name=(full_name or None),
            phone=(phone or None)
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return True, user
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi tạo tài khoản: {str(e)}"


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if user and user.check_password(password):
        return True, user
    return False, "Tên đăng nhập hoặc mật khẩu không đúng"


# ----------------
# CART
# ----------------
def get_or_create_active_cart(user_id: int, restaurant_id: int):
    """
    Lấy giỏ hàng ACTIVE gần nhất (nếu chưa có thì tạo).
    Match với enum: status in ("ACTIVE", "CHECKED_OUT").
    """
    cart = (
        Cart.query
        .filter(
            Cart.user_id == user_id,
            Cart.restaurant_id == restaurant_id,
            Cart.status == "ACTIVE"
        )
        .order_by(Cart.created_at.desc())
        .first()
    )
    if not cart:
        cart = Cart(user_id=user_id, restaurant_id=restaurant_id, status="ACTIVE")
        db.session.add(cart)
        db.session.commit()
    return cart


def add_item_to_cart(user_id: int, restaurant_id: int, item_id: int, qty: int = 1):
    """
    Thêm/ tăng số lượng 1 món vào giỏ.
    - Tôn trọng ràng buộc UNIQUE (cart_id, item_id) trên DB.
    - Chỉ cho phép thêm món cùng nhà hàng, còn bán (is_available=True).
    """
    try:
        item = Item.query.get(item_id)
        if not item or item.restaurant_id != restaurant_id or not item.is_available:
            return False, "Món không hợp lệ hoặc đã ngừng bán"

        cart = get_or_create_active_cart(user_id, restaurant_id)

        row = CartItem.query.filter_by(cart_id=cart.id, item_id=item.id).first()
        add_qty = max(1, int(qty or 1))
        if row:
            row.quantity = int(row.quantity) + add_qty
        else:
            db.session.add(CartItem(cart_id=cart.id, item_id=item.id, quantity=add_qty))

        db.session.commit()
        return True, "Đã thêm vào giỏ"
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm vào giỏ: {str(e)}"


def get_active_cart_detail(user_id: int, restaurant_id: int):
    """
    Trả về (cart, items[], total_amount)
    items: [{ item_id, item_name, unit_price, quantity, line_total }]
    """
    cart = get_or_create_active_cart(user_id, restaurant_id)

    rows = (
        db.session.query(
            CartItem.item_id,
            CartItem.quantity,
            Item.name.label('item_name'),
            Item.price.label('unit_price'),
            (Item.price * CartItem.quantity).label('line_total')
        )
        .join(Item, Item.id == CartItem.item_id)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    items = [
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "unit_price": Decimal(r.unit_price),
            "quantity": int(r.quantity),
            "line_total": Decimal(r.line_total),
        }
        for r in rows
    ]
    total_amount = sum((i["line_total"] for i in items), Decimal('0'))
    return cart, items, total_amount


def update_cart_item_quantity(cart_id: int, item_id: int, quantity: int):
    """
    Nếu quantity <= 0: xóa khỏi giỏ.
    """
    try:
        row = CartItem.query.filter_by(cart_id=cart_id, item_id=item_id).first()
        if not row:
            return False, "Không tìm thấy món trong giỏ"

        if quantity is None or int(quantity) <= 0:
            db.session.delete(row)
        else:
            row.quantity = int(quantity)

        db.session.commit()
        return True, "Cập nhật giỏ hàng thành công"
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi cập nhật giỏ hàng: {str(e)}"


def remove_item_from_cart(cart_id: int, item_id: int):
    try:
        row = CartItem.query.filter_by(cart_id=cart_id, item_id=item_id).first()
        if not row:
            return False, "Không tìm thấy món trong giỏ"
        db.session.delete(row)
        db.session.commit()
        return True, "Đã xóa món khỏi giỏ"
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi xóa món: {str(e)}"


# ----------------
# ORDER & PAYMENT
# ----------------
def create_order_from_cart(
    user_id: int,
    restaurant_id: int,
    ship_name: str,
    ship_phone: str,
    ship_address: str,
    payment_method: str
):
    """
    Tạo order từ giỏ ACTIVE và tạo Payment tương ứng.
    - Nếu COD: đánh dấu thanh toán thành công ngay (status=SUCCEEDED, order.payment_status=PAID).
    - Các method khác: tạo payment PENDING.
    - Cart chuyển sang CHECKED_OUT.
    """
    try:
        cart, items, total = get_active_cart_detail(user_id, restaurant_id)
        if not items:
            return False, "Giỏ hàng trống", None

        # Snapshot về Order + OrderItems
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
        db.session.flush()  # sinh order.id

        for it in items:
            db.session.add(OrderItem(
                order_id=order.id,
                item_id=it["item_id"],                 # SET NULL nếu item bị xóa sau này (model đã set)
                item_name=it["item_name"],             # snapshot
                unit_price=it["unit_price"],           # snapshot
                quantity=it["quantity"],
                line_total=it["line_total"]
            ))

        if payment_method == "COD":
            # thanh toán thành công ngay
            order.payment_status = "PAID"
            pay = Payment(
                order_id=order.id,
                amount=total,
                method="COD",
                status="SUCCEEDED",
                paid_at=func.now()
            )
            db.session.add(pay)
            cart.status = "CHECKED_OUT"
            db.session.commit()
            return True, "Đặt hàng thành công (COD)", order

        # method khác -> tạo giao dịch chờ
        pay = Payment(
            order_id=order.id,
            amount=total,
            method=payment_method,
            status="PENDING",
            paid_at=None
        )
        db.session.add(pay)
        cart.status = "CHECKED_OUT"
        db.session.commit()
        return True, "Tạo đơn hàng thành công, chuyển đến cổng thanh toán", order

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi tạo đơn hàng: {str(e)}", None


def _get_latest_or_pending_payment(order_id: int) -> Payment | None:
    """
    Lấy payment gần nhất (ưu tiên PENDING), dùng cho cập nhật kết quả.
    Vì schema là 1-n payments (giữ lịch sử), tránh nhầm payment cũ.
    """
    # ưu tiên payment đang PENDING
    pay = (
        Payment.query
        .filter_by(order_id=order_id, status="PENDING")
        .order_by(desc(Payment.id))
        .first()
    )
    if pay:
        return pay
    # nếu không có PENDING, lấy payment mới nhất
    return (
        Payment.query
        .filter_by(order_id=order_id)
        .order_by(desc(Payment.id))
        .first()
    )


def update_payment_result(order_id: int, result: str):
    """
    Cập nhật kết quả thanh toán:
    - result == "success": payment -> SUCCEEDED, order.payment_status -> PAID
    - else: payment -> FAILED (không đổi order.payment_status nếu đã PAID)
    """
    try:
        order = Order.query.get(order_id)
        if not order:
            return False, "Không tìm thấy đơn hàng"

        pay = _get_latest_or_pending_payment(order.id)
        if not pay:
            return False, "Thiếu giao dịch thanh toán"

        if result == "success":
            pay.status = "SUCCEEDED"
            pay.paid_at = func.now()
            order.payment_status = "PAID"
        else:
            # lưu thất bại cho payment hiện tại (order có thể vẫn UNPAID)
            # không đổi paid_at
            pay.status = "FAILED"

        db.session.commit()
        return True, "Cập nhật thanh toán thành công"
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Lỗi cập nhật thanh toán: {str(e)}"


# ----------------
# Helper: lấy order & payment để hiển thị trang chuyển khoản
# ----------------
def get_payment_info(order_id: int):
    """
    Trả về (order, payment_mới_nhất) theo order_id, hoặc (None, None).
    Với 1-n payments, nên hiển thị payment mới nhất cho user.
    """
    order = Order.query.get(order_id)
    if not order:
        return None, None
    payment = (
        Payment.query
        .filter_by(order_id=order.id)
        .order_by(desc(Payment.id))
        .first()
    )
    return order, payment
