# --- YÊU CẦU 2: MODELS CHO ĐẶT MÓN ---
from sqlalchemy import func, Numeric, Enum, Boolean, BigInteger, Integer, String, TIMESTAMP
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
