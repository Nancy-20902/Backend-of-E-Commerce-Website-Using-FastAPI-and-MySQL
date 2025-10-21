# app/crud.py
from sqlalchemy.orm import Session
from app import models, schemas, auth
from typing import List, Optional
 
# USER
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()
 
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()
 
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=models.UserRole.user,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
 
def update_user(db: Session, db_user: models.User, updates: schemas.UserUpdate):
    if updates.username is not None:
        db_user.username = updates.username
    if updates.email is not None:
        db_user.email = updates.email
    db.commit()
    db.refresh(db_user)
    return db_user
 
# CATEGORY
def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()
 
def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.name == name).first()
 
def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
 
def list_categories(db: Session) -> List[models.Category]:
    return db.query(models.Category).all()
 
# PRODUCT
def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        quantity=product.quantity,
    )
    # assign categories
    if product.category_ids:
        categories = db.query(models.Category).filter(models.Category.id.in_(product.category_ids)).all()
        db_product.categories = categories
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product
 
def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()
 
def list_products(db: Session, skip: int = 0, limit: int = 10,
                  category_id: Optional[int] = None,
                  min_price: Optional[float] = None,
                  max_price: Optional[float] = None) -> List[models.Product]:
    query = db.query(models.Product)
    if category_id:
        query = query.join(models.Product.categories).filter(models.Category.id == category_id)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    return query.offset(skip).limit(limit).all()
 
def update_product(db: Session, db_product: models.Product, updates: schemas.ProductUpdate):
    if updates.name is not None:
        db_product.name = updates.name
    if updates.description is not None:
        db_product.description = updates.description
    if updates.price is not None:
        db_product.price = updates.price
    if updates.quantity is not None:
        db_product.quantity = updates.quantity
    if updates.category_ids is not None:
        categories = db.query(models.Category).filter(models.Category.id.in_(updates.category_ids)).all()
        db_product.categories = categories
    db.commit()
    db.refresh(db_product)
    return db_product
 
def delete_product(db: Session, db_product: models.Product):
    db.delete(db_product)
    db.commit()
 
# CART
def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int):
    cart_item = db.query(models.CartItem).filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = models.CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item
 
def get_cart_items(db: Session, user_id: int) -> List[models.CartItem]:
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()
 
def update_cart_item(db: Session, cart_item_id: int, quantity: int):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if cart_item:
        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart_item)
    return cart_item
 
def remove_cart_item(db: Session, cart_item_id: int):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == cart_item_id).first()
    if cart_item:
        db.delete(cart_item)
        db.commit()
    return cart_item
 
def clear_cart(db: Session, user_id: int):
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()
 
# ORDER
def create_order(db: Session, user_id: int, items: List[schemas.OrderItemBase]) -> models.Order:
    total_price = 0.0
    order_items = []
 
    for item in items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product is None:
            raise Exception(f"Product with id {item.product_id} not found")
        if product.quantity < item.quantity:
            raise Exception(f"Not enough quantity for product {product.name}")
 
        price_for_item = product.price * item.quantity
        total_price += price_for_item
 
        order_item = models.OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            price_per_item=product.price
        )
        order_items.append(order_item)
 
        product.quantity -= item.quantity  # Reduce stock
 
    order = models.Order(user_id=user_id, total_price=total_price)
    order.items = order_items
 
    db.add(order)
    db.commit()
    db.refresh(order)
 
    # Clear cart after order
    clear_cart(db, user_id)
    return order
 
def get_orders_by_user(db: Session, user_id: int) -> List[models.Order]:
    return db.query(models.Order).filter(models.Order.user_id == user_id).order_by(models.Order.created_at.desc()).all()
 
def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    return db.query(models.Order).filter(models.Order.id == order_id).first()
 
def get_all_orders(db: Session) -> List[models.Order]:
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()
 
# REVIEWS
def create_review(db: Session, user_id: int, review: schemas.ReviewCreate) -> models.Review:
    db_review = models.Review(
        user_id=user_id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        is_approved=False  # Admin must approve
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
 
def get_reviews_for_product(db: Session, product_id: int) -> List[models.Review]:
    return db.query(models.Review).filter(
        models.Review.product_id == product_id,
        models.Review.is_approved == True
    ).all()
 
def get_reviews(db: Session) -> List[models.Review]:
    return db.query(models.Review).all()
 
def approve_review(db: Session, review_id: int):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review:
        review.is_approved = True
        db.commit()
        db.refresh(review)
    return review