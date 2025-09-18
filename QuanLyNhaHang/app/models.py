# --- YÊU CẦU 2: MODELS CHO ĐẶT MÓN ---
from sqlalchemy import func, Numeric, Enum, Boolean, BigInteger, Integer, String, TIMESTAMP, DateTime
from QuanLyNhaHang.app import db

class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id = db.Column(BigInteger, primary_key=True)
    owner_id = db.Column(BigInteger, nullable=False)
    name = db.Column(String(191), nullable=False)
    address = db.Column(String(255))
    phone = db.Column(String(30))
    is_open = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(TIMESTAMP, server_default=func.current_timestamp())

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(BigInteger, primary_key=True)
    restaurant_id = db.Column(BigInteger, nullable=False, index=True)
    name = db.Column(String(191), nullable=False)
    price = db.Column(Numeric(12, 2), nullable=False)
    is_available = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(TIMESTAMP, server_default=func.current_timestamp())

class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(BigInteger, primary_key=True)
    user_id = db.Column(BigInteger, nullable=False, index=True)
    restaurant_id = db.Column(BigInteger, nullable=False, index=True)
    status = db.Column(Enum("ACTIVE", "CHECKED_OUT", name="cart_status"), default="ACTIVE", nullable=False)
    created_at = db.Column(TIMESTAMP, server_default=func.current_timestamp())

class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(BigInteger, primary_key=True)
    cart_id = db.Column(BigInteger, nullable=False, index=True)
    item_id = db.Column(BigInteger, nullable=False, index=True)
    quantity = db.Column(Integer, nullable=False, default=1)
    created_at = db.Column(TIMESTAMP, server_default=func.current_timestamp())


# ----------------
# ORDERS & ORDER ITEMS
# ----------------
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(BigInteger, primary_key=True)
    user_id = db.Column(BigInteger, nullable=True, index=True)
    restaurant_id = db.Column(BigInteger, nullable=False, index=True)
    status = db.Column(Enum("PENDING","ACCEPTED","REJECTED","COMPLETED","CANCELLED", name="order_status"),
                       nullable=False, default="PENDING")
    payment_status = db.Column(Enum("UNPAID","PAID", name="payment_status"), nullable=False, default="UNPAID")
    payment_method = db.Column(Enum("COD","CARD","EWALLET","BANK", name="payment_method"), nullable=False, default="CARD")
    ship_name = db.Column(String(120))
    ship_phone = db.Column(String(30))
    ship_address = db.Column(String(255))
    total_amount = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    created_at = db.Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(BigInteger, primary_key=True)
    order_id = db.Column(BigInteger, nullable=False, index=True)
    item_id = db.Column(BigInteger, nullable=True, index=True)  # cho phép NULL nếu món bị xóa sau này
    item_name = db.Column(String(191), nullable=False)          # snapshot
    unit_price = db.Column(Numeric(12, 2), nullable=False)      # snapshot
    quantity = db.Column(Integer, nullable=False, default=1)
    line_total = db.Column(Numeric(12, 2), nullable=False)

# ----------------
# PAYMENTS
# ----------------
class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(BigInteger, primary_key=True)
    order_id = db.Column(BigInteger, nullable=False, unique=True, index=True)
    amount = db.Column(Numeric(12, 2), nullable=False)
    method = db.Column(Enum("COD","CARD","EWALLET","BANK", name="pay_method"), nullable=False)
    status = db.Column(Enum("PENDING","SUCCEEDED","FAILED","REFUNDED", name="pay_status"), nullable=False, default="PENDING")
    paid_at = db.Column(DateTime, nullable=True)