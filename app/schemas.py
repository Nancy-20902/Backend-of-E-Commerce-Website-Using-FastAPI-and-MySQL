# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class OrderStatus(str, Enum):
    pending = "Pending"
    shipped = "Shipped"
    delivered = "Delivered"

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]

class UserResponse(UserBase):
    id: int
    is_active: bool
    role: UserRole

    class Config:
        from_attributes = True

# Category schemas
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = Field(ge=0)

class ProductCreate(ProductBase):
    category_ids: List[int] = []

class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    quantity: Optional[int]
    category_ids: Optional[List[int]] = None

class ProductResponse(ProductBase):
    id: int
    categories: List[CategoryResponse] = []

    class Config:
        from_attributes = True

# Review schemas
class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    product_id: int

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    product_id: int
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

# CartItem schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class CartItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int

    class Config:
        from_attributes = True

# OrderItem schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    price_per_item: float

    class Config:
        from_attributes = True

# Order schemas
class OrderBase(BaseModel):
    total_price: float
    status: OrderStatus

class OrderCreate(BaseModel):
    items: List[OrderItemBase]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# Token schemas for auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
