# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas, crud, database, auth
from fastapi.middleware.cors import CORSMiddleware
 
models.Base.metadata.create_all(bind=database.engine)
 
app = FastAPI(title="E-commerce API")
 
@app.get("/")
def root():
    return {"message": "E-commerce backend is running and connected to MySQL!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Dependency
get_db = database.get_db
 
# User Registration
@app.post("/register", response_model=schemas.UserResponse, tags=["Users"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
 
# Login (JWT token)
@app.post("/login", response_model=schemas.Token, tags=["Users"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
 
# Get current user
@app.get("/users/me", response_model=schemas.UserResponse, tags=["Users"])
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user
 
# Update current user info
@app.put("/users/me", response_model=schemas.UserResponse, tags=["Users"])
def update_user_info(updates: schemas.UserUpdate,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.update_user(db, current_user, updates)
 
# ADMIN ONLY - List all users
@app.get("/users", response_model=List[schemas.UserResponse], tags=["Admin"])
def list_users(db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_active_admin)):
    return db.query(models.User).all()
 
# CATEGORY routes
@app.post("/categories", response_model=schemas.CategoryResponse, tags=["Category"])
def create_category(category: schemas.CategoryCreate,
                    db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_active_admin)):
    db_cat = crud.get_category_by_name(db, category.name)
    if db_cat:
        raise HTTPException(status_code=400, detail="Category already exists")
    return crud.create_category(db, category)
 
@app.get("/categories", response_model=List[schemas.CategoryResponse], tags=["Category"])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_categories(db)
 
# PRODUCT routes
@app.post("/products", response_model=schemas.ProductResponse, tags=["Products"])
def create_product(product: schemas.ProductCreate,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_active_admin)):
    return crud.create_product(db, product)
 
@app.get("/products", response_model=List[schemas.ProductResponse], tags=["Products"])
def list_products(
    skip: int = 0,
    limit: int = 10,
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    return crud.list_products(db, skip=skip, limit=limit, category_id=category_id, min_price=min_price, max_price=max_price)
 
@app.get("/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
 
@app.put("/products/{product_id}", response_model=schemas.ProductResponse, tags=["Products"])
def update_product(product_id: int, updates: schemas.ProductUpdate,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_active_admin)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.update_product(db, product, updates)
 
@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
def delete_product(product_id: int,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_active_admin)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud.delete_product(db, product)
    return None
 
# CART routes
@app.post("/cart", response_model=schemas.CartItemResponse, tags=["Cart"])
def add_item_to_cart(item: schemas.CartItemBase,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_active_user)):
    product = crud.get_product(db, item.product_id)
    if not product or product.quantity < item.quantity:
        raise HTTPException(status_code=400, detail="Product not available in requested quantity")
    return crud.add_to_cart(db, current_user.id, item.product_id, item.quantity)
 
@app.get("/cart", response_model=List[schemas.CartItemResponse], tags=["Cart"])
def get_cart(db: Session = Depends(get_db),
             current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.get_cart_items(db, current_user.id)
 
@app.put("/cart/{cart_item_id}", response_model=schemas.CartItemResponse, tags=["Cart"])
def update_cart_item(cart_item_id: int, quantity: int,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_active_user)):
    cart_item = crud.update_cart_item(db, cart_item_id, quantity)
    if not cart_item or cart_item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return cart_item
 
@app.delete("/cart/{cart_item_id}", status_code=204, tags=["Cart"])
def delete_cart_item(cart_item_id: int,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_active_user)):
    cart_item = crud.get_cart_items(db, current_user.id)
    item_to_delete = next((item for item in cart_item if item.id == cart_item_id), None)
    if not item_to_delete:
        raise HTTPException(status_code=404, detail="Cart item not found")
    crud.remove_cart_item(db, cart_item_id)
    return None
 
# ORDER routes
@app.post("/orders", response_model=schemas.OrderResponse, tags=["Orders"])
def create_order(order: schemas.OrderCreate,
                 db: Session = Depends(get_db),
                 current_user: models.User = Depends(auth.get_current_active_user)):
    try:
        new_order = crud.create_order(db, current_user.id, order.items)
        return new_order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
 
@app.get("/orders", response_model=List[schemas.OrderResponse], tags=["Orders"])
def get_my_orders(db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_active_user)):
    return crud.get_orders_by_user(db, current_user.id)
 
@app.get("/orders/{order_id}", response_model=schemas.OrderResponse, tags=["Orders"])
def get_order(order_id: int, db: Session = Depends(get_db),
              current_user: models.User = Depends(auth.get_current_active_user)):
    order = crud.get_order(db, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
 
# ADMIN ONLY - list all orders
@app.get("/admin/orders", response_model=List[schemas.OrderResponse], tags=["Admin"])
def list_all_orders(db: Session = Depends(get_db),
                    current_user: models.User = Depends(auth.get_current_active_admin)):
    return crud.get_all_orders(db)
 
# REVIEWS routes
@app.post("/reviews", response_model=schemas.ReviewResponse, tags=["Review"])
def submit_review(review: schemas.ReviewCreate,
                  db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_active_user)):
    product = crud.get_product(db, review.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.create_review(db, current_user.id, review)
 
@app.get("/products/{product_id}/reviews", response_model=List[schemas.ReviewResponse], tags=["Review"])
def get_approved_reviews(product_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_for_product(db, product_id)
 
# ADMIN ONLY - approve review
@app.put("/admin/reviews/{review_id}/approve", response_model=schemas.ReviewResponse, tags=["Admin"])
def approve_review(review_id: int,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_active_admin)):
    review = crud.approve_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review