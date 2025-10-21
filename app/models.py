# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

# Many-to-many association table for products & categories
product_category = Table(
    "product_category",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id")),
    Column("category_id", Integer, ForeignKey("categories.id"))
)

class UserRole(enum.Enum):
    admin = "admin"
    user = "user"

class OrderStatus(enum.Enum):
    pending = "Pending"
    shipped = "Shipped"
    delivered = "Delivered"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.user)

    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)

    products = relationship("Product", secondary=product_category, back_populates="categories")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)

    categories = relationship("Category", secondary=product_category, back_populates="products")
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

    user = relationship("User")
    product = relationship("Product")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_per_item = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
