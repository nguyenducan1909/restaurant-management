# --- MODELS ĐẶT MÓN (chuẩn MySQL/InnoDB, khớp foodhub.sql) ---
from sqlalchemy import (
    func, Numeric, Enum, Boolean, BigInteger, Integer, String,
    TIMESTAMP, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from QuanLyNhaHang.app import db


# ======================
# USERS
# ======================
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id          = db.Column(BigInteger, primary_key=True, autoincrement=True)
    username    = db.Column(String(50), unique=True, nullable=False)
    email       = db.Column(String(100), unique=True, nullable=False)
    password_hash = db.Column(String(255), nullable=False)
    full_name   = db.Column(String(100))
    phone       = db.Column(String(20))
    role        = db.Column(
        Enum("CUSTOMER", "OWNER", "ADMIN", name="role_enum"),
        nullable=False,
        server_default="CUSTOMER"
    )
    is_active   = db.Column(Boolean, nullable=False, server_default="1")
    created_at  = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationships
    restaurants = relationship("Restaurant", back_populates="owner", passive_deletes=True)
    carts       = relationship("Cart", back_populates="user", passive_deletes=True)
    orders      = relationship("Order", back_populates="user", passive_deletes=True)

    # Password helpers
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}#{self.id}>"


# ======================
# RESTAURANTS
# ======================
class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id         = db.Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id   = db.Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name       = db.Column(String(191), nullable=False)
    address    = db.Column(String(255))
    phone      = db.Column(String(30))
    is_open    = db.Column(Boolean, nullable=False, server_default="1")
    image_url  = db.Column(String(255))
    created_at = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationships
    owner      = relationship("User", back_populates="restaurants")
    items      = relationship("Item", back_populates="restaurant",
                              cascade="all, delete-orphan", passive_deletes=True)
    carts      = relationship("Cart", back_populates="restaurant", passive_deletes=True)
    orders     = relationship("Order", back_populates="restaurant", passive_deletes=True)

    def __repr__(self):
        return f"<Restaurant {self.name}#{self.id}>"


# ======================
# MENU ITEMS
# ======================
class Item(db.Model):
    __tablename__ = "items"

    id             = db.Column(BigInteger, primary_key=True, autoincrement=True)
    restaurant_id  = db.Column(
        BigInteger,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name           = db.Column(String(191), nullable=False)
    price          = db.Column(Numeric(12, 2), nullable=False)
    is_available   = db.Column(Boolean, nullable=False, server_default="1")
    image_url      = db.Column(String(255))
    created_at     = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    restaurant = relationship("Restaurant", back_populates="items")

    def __repr__(self):
        return f"<Item {self.name}#{self.id} R{self.restaurant_id}>"


# ======================
# CARTS
# ======================
class Cart(db.Model):
    __tablename__ = "carts"

    id            = db.Column(BigInteger, primary_key=True, autoincrement=True)
    user_id       = db.Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    restaurant_id = db.Column(
        BigInteger,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status        = db.Column(
        Enum("ACTIVE", "CHECKED_OUT", name="cart_status_enum"),
        nullable=False,
        server_default="ACTIVE"
    )
    created_at    = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationships
    user       = relationship("User", back_populates="carts")
    restaurant = relationship("Restaurant", back_populates="carts")
    items      = relationship("CartItem", back_populates="cart",
                              cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<Cart #{self.id} U{self.user_id} R{self.restaurant_id} {self.status}>"


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id         = db.Column(BigInteger, primary_key=True, autoincrement=True)
    cart_id    = db.Column(
        BigInteger,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_id    = db.Column(
        BigInteger,
        ForeignKey("items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quantity   = db.Column(Integer, nullable=False, server_default="1")
    created_at = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cart_item_quantity_pos"),
        UniqueConstraint("cart_id", "item_id", name="uq_cart_item_once_per_cart"),
    )

    cart = relationship("Cart", back_populates="items")
    item = relationship("Item")

    def __repr__(self):
        return f"<CartItem C{self.cart_id} I{self.item_id} x{self.quantity}>"


# ======================
# ORDERS & ORDER ITEMS
# ======================
class Order(db.Model):
    __tablename__ = "orders"

    id             = db.Column(BigInteger, primary_key=True, autoincrement=True)
    user_id        = db.Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    restaurant_id  = db.Column(
        BigInteger,
        ForeignKey("restaurants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    status         = db.Column(
        Enum("PENDING","ACCEPTED","REJECTED","COMPLETED","CANCELLED", name="order_status_enum"),
        nullable=False,
        server_default="PENDING"
    )
    payment_status = db.Column(
        Enum("UNPAID","PAID", name="payment_status_enum"),
        nullable=False,
        server_default="UNPAID"
    )
    payment_method = db.Column(
        Enum("COD","CARD","EWALLET","BANK", name="payment_method_enum"),
        nullable=False,
        server_default="CARD"
    )
    ship_name      = db.Column(String(120))
    ship_phone     = db.Column(String(30))
    ship_address   = db.Column(String(255))
    total_amount   = db.Column(Numeric(12, 2), nullable=False, server_default="0.00")
    created_at     = db.Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationships
    user       = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items      = relationship("OrderItem", back_populates="order",
                              cascade="all, delete-orphan", passive_deletes=True)
    payments   = relationship("Payment", back_populates="order", passive_deletes=True)

    def __repr__(self):
        return f"<Order #{self.id} R{self.restaurant_id} {self.status} {self.payment_status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id          = db.Column(BigInteger, primary_key=True, autoincrement=True)
    order_id    = db.Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    item_id     = db.Column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    item_name   = db.Column(String(191), nullable=False)
    unit_price  = db.Column(Numeric(12, 2), nullable=False)
    quantity    = db.Column(Integer, nullable=False, server_default="1")
    line_total  = db.Column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_pos"),
    )

    order = relationship("Order", back_populates="items")
    item  = relationship("Item")

    def __repr__(self):
        return f"<OrderItem O{self.order_id} '{self.item_name}' x{self.quantity}>"


# ======================
# PAYMENTS
# ======================
class Payment(db.Model):
    __tablename__ = "payments"

    id       = db.Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount   = db.Column(Numeric(12, 2), nullable=False)
    method   = db.Column(
        Enum("COD","CARD","EWALLET","BANK", name="pay_method_enum"),
        nullable=False
    )
    status   = db.Column(
        Enum("PENDING","SUCCEEDED","FAILED","REFUNDED", name="pay_status_enum"),
        nullable=False,
        server_default="PENDING"
    )
    paid_at  = db.Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment #{self.id} O{self.order_id} {self.status}>"
