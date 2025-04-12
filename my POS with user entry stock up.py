from sqlmodel import Field, SQLModel, create_engine, Session, Relationship, select
from typing import Optional, List

# Base class for furniture
class Furniture(SQLModel):
    category: str
    warehouse_location: str  # Location: Fanling or Mongkok

# Chair model
class Chair(Furniture, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_no: str = Field(index=True, unique=True)
    stock_level: int
    price: float
    material: str
    width: float
    height: float
    depth: float
    has_armrests: bool
    max_weight: float
    has_sitting_pad: bool
    cart_items: List["CartItem"] = Relationship(back_populates="chair")

# Bed model
class Bed(Furniture, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_no: str = Field(index=True, unique=True)
    stock_level: int
    price: float
    material: str
    width: float
    height: float
    depth: float
    bed_size: str
    has_headboard: bool
    cart_items: List["CartItem"] = Relationship(back_populates="bed")

# Bookshelf model
class Bookshelf(Furniture, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_no: str = Field(index=True, unique=True)
    stock_level: int
    price: float
    material: str
    width: float
    height: float
    depth: float
    shelf_layers: int
    maximum_weight: float
    cart_items: List["CartItem"] = Relationship(back_populates="bookshelf")

# Shopping Cart Item model
class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: str  # e.g., user name like "Simon" or "Peter"
    product_type: str  # Chair, Bed or Bookshelf
    model_no: str  
    quantity: int = Field(ge=1)  # Quantity of the product in the cart
    chair_id: Optional[int] = Field(default=None, foreign_key="chair.id")
    bed_id: Optional[int] = Field(default=None, foreign_key="bed.id")
    bookshelf_id: Optional[int] = Field(default=None, foreign_key="bookshelf.id")
    chair: Optional[Chair] = Relationship(back_populates="cart_items")
    bed: Optional[Bed] = Relationship(back_populates="cart_items")
    bookshelf: Optional[Bookshelf] = Relationship(back_populates="cart_items")

# Create initial products list
products = [
    # Chair samples
    Chair(category="Wooden Chair", warehouse_location="FanLing", model_no="CH-001", stock_level=50, 
          price=299.0, material="Wood", width=45.0, height=85.0, depth=50.0, has_armrests=False, 
          max_weight=120.0, has_sitting_pad=True),
    Chair(category="Metal Chair", warehouse_location="Mongkok", model_no="CH-002", stock_level=30, 
          price=349.0, material="Metal", width=50.0, height=90.0, depth=55.0, has_armrests=True, 
          max_weight=150.0, has_sitting_pad=True),
    # Bed samples
    Bed(category="Wooden Bed - Double", warehouse_location="FanLing", model_no="BD-001", stock_level=10, 
        price=1999.0, material="Wood", width=200.0, height=40.0, depth=160.0, bed_size="Double", 
        has_headboard=True),
    Bed(category="Metal Bed - Double", warehouse_location="Mongkok", model_no="BD-002", stock_level=15, 
        price=1499.0, material="Metal", width=180.0, height=35.0, depth=150.0, bed_size="Double", 
        has_headboard=False),
    # Bookshelf samples
    Bookshelf(category="Wooden Book Shelf - Small Size", warehouse_location="FanLing", model_no="BS-001", 
              stock_level=25, price=599.0, material="Wood", width=80.0, height=180.0, depth=30.0, 
              shelf_layers=5, maximum_weight=25.0),
    Bookshelf(category="Metal Book Shelf", warehouse_location="Mongkok", model_no="BS-002", stock_level=30, 
              price=499.0, material="Metal", width=70.0, height=160.0, depth=25.0, shelf_layers=4, 
              maximum_weight=20.0),
]

# Create SQLite engine
engine = create_engine("sqlite:///furniture.db")

# Create all tables
SQLModel.metadata.create_all(engine)

# Insert furniture products
def insert_furniture(products):
    valid_locations = {"FanLing", "Mongkok"}
    with Session(engine) as session:
        for product in products:
            if product.warehouse_location not in valid_locations:
                raise ValueError(f"Invalid warehouse_location: {product.warehouse_location}")
            existing = None
            if isinstance(product, Chair):
                existing = session.exec(select(Chair).where(Chair.model_no == product.model_no)).first()
            elif isinstance(product, Bed):
                existing = session.exec(select(Bed).where(Bed.model_no == product.model_no)).first()
            elif isinstance(product, Bookshelf):
                existing = session.exec(select(Bookshelf).where(Bookshelf.model_no == product.model_no)).first()
            if not existing:
                session.add(product)
        session.commit()

# Insert shopping cart items
def insert_cart_items(cart_items):
    with Session(engine) as session:
        for item in cart_items:
            valid_product_types = {"Chair", "Bed", "Bookshelf"}
            if item.product_type not in valid_product_types:
                raise ValueError(f"Invalid product_type: {item.product_type}")
            product = None
            if item.product_type == "Chair":
                product = session.exec(select(Chair).where(Chair.model_no == item.model_no)).first()
                if product:
                    item.chair_id = product.id
            elif item.product_type == "Bed":
                product = session.exec(select(Bed).where(Bed.model_no == item.model_no)).first()
                if product:
                    item.bed_id = product.id
            elif item.product_type == "Bookshelf":
                product = session.exec(select(Bookshelf).where(Bookshelf.model_no == item.model_no)).first()
                if product:
                    item.bookshelf_id = product.id
            if not product:
                raise ValueError(f"Product {item.model_no} ({item.product_type}) does not exist")
            if product.stock_level < item.quantity:
                raise ValueError(f"Insufficient stock for {item.product_type} {item.model_no}. Available: {product.stock_level}")
            existing_item = session.exec(
                select(CartItem).where(
                    CartItem.cart_id == item.cart_id,
                    CartItem.product_type == item.product_type,
                    CartItem.model_no == item.model_no
                )
            ).first()
            if existing_item:
                existing_item.quantity += item.quantity
            else:
                session.add(item)
        session.commit()

# List shopping cart contents
def list_cart_contents(cart_id: str):
    with Session(engine) as session:
        cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart_id)).all()
        if not cart_items:
            print(f"No items found in cart for {cart_id}")
            return
        print(f"\nShopping Cart Contents for {cart_id}:")
        print("-" * 40)
        print(f"{'Item':<20} {'Quantity':<10} {'Unit Price':<12} {'Total Price':<12}")
        print("-" * 40)
        total_cart_price = 0.0
        for item in cart_items:
            product = None
            unit_price = 0.0
            item_name = f"{item.product_type} {item.model_no}"
            if item.product_type == "Chair":
                product = session.exec(select(Chair).where(Chair.model_no == item.model_no)).first()
            elif item.product_type == "Bed":
                product = session.exec(select(Bed).where(Bed.model_no == item.model_no)).first()
            elif item.product_type == "Bookshelf":
                product = session.exec(select(Bookshelf).where(Bookshelf.model_no == item.model_no)).first()
            if product:
                unit_price = product.price
            else:
                print(f"Warning: Product {item.product_type} {item.model_no} not found")
                continue
            total_item_price = item.quantity * unit_price
            total_cart_price += total_item_price
            print(f"{item_name:<20} {item.quantity:<10} ${unit_price:<11.2f} ${total_item_price:<11.2f}")
        print("-" * 40)
        print(f"{'Total':<20} {'':<10} {'':<12} ${total_cart_price:.2f}")

# Checkout function to reduce stock levels
def checkout_cart(cart_id: str):
    with Session(engine) as session:
        cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart_id)).all()
        if not cart_items:
            print("Your cart is empty.")
            return
        unavailable_items = []
        for item in cart_items:
            product = None
            if item.chair:
                product = item.chair
            elif item.bed:
                product = item.bed
            elif item.bookshelf:
                product = item.bookshelf
            if product:
                if product.stock_level < item.quantity:
                    unavailable_items.append(
                        f"{item.product_type} {item.model_no} (Available: {product.stock_level}, Requested: {item.quantity})"
                    )
            else:
                print(f"Warning: CartItem {item.id} has no linked product.")
        if unavailable_items:
            print("The following items are unavailable or have insufficient stock:")
            for unavail in unavailable_items:
                print(f"- {unavail}")
            print("Please adjust your cart and try again.")
            return
        for item in cart_items:
            product = None
            if item.chair:
                product = item.chair
            elif item.bed:
                product = item.bed
            elif item.bookshelf:
                product = item.bookshelf
            if product:
                product.stock_level -= item.quantity
                session.add(product)
        for item in cart_items:
            session.delete(item)
        session.commit()
        print("Purchase successful! Your cart has been cleared.")

# Function to adjust stock levels (In-House Use)
def adjust_stock():
    while True:
        print("\nSelect product type to adjust stock:")
        print("1. Chair")
        print("2. Bed")
        print("3. Bookshelf")
        choice = input("Enter choice (1-3): ").strip()
        if choice == "1":
            product_type = "Chair"
        elif choice == "2":
            product_type = "Bed"
        elif choice == "3":
            product_type = "Bookshelf"
        else:
            print("Invalid choice. Please try again.")
            continue
        with Session(engine) as session:
            display_items_by_category(session, product_type)
            while True:
                model_no = input(f"Enter model number for {product_type}: ").strip()
                item = session.exec(
                    select(product_classes[product_type]).where(product_classes[product_type].model_no == model_no)
                ).first()
                if item:
                    break
                else:
                    print("Invalid model number. Please try again.")
            while True:
                try:
                    quantity = int(input("Enter quantity to add: ").strip())
                    if quantity < 0:
                        print("Quantity must be a non-negative integer.")
                    else:
                        break
                except ValueError:
                    print("Invalid quantity. Please enter a number.")
            item.stock_level += quantity
            session.add(item)
            session.commit()
            print(f"Added {quantity} to stock of {product_type} {model_no}. New stock level: {item.stock_level}")
        cont = input("Adjust another item? (yes/no): ").strip().lower()
        if cont != "yes":
            break

# Dictionary to map product types to their classes
product_classes = {
    "Chair": Chair,
    "Bed": Bed,
    "Bookshelf": Bookshelf
}

# Function to display items by category
def display_items_by_category(session, product_type):
    items = session.exec(select(product_classes[product_type])).all()
    print(f"\nAvailable {product_type}s:")
    for item in items:
        print(f"Model: {item.model_no}, Category: {item.category}, Price: ${item.price:.2f}, Stock: {item.stock_level}")

# Insert initial furniture products
insert_furniture(products)

# Main loop with In-House Use and POS options
while True:
    choice = input("Enter 'In-House Use' to adjust stock levels, 'POS' to start shopping, or 'EXIT' to quit: ").strip().upper()
    if choice == "EXIT":
        break
    elif choice == "IN-HOUSE USE":
        adjust_stock()
    elif choice == "POS":
        while True:
            user_name = input("Enter buyer name (or 'END' to return to main menu): ").strip()
            if user_name.upper() == "END":
                break
            cart_id = user_name
            while True:
                print(f"\nOptions for {cart_id}:")
                print("1. Add items to cart")
                print("2. View cart")
                print("3. Checkout")
                print("4. Exit to buyer selection")
                option = input("Enter choice (1-4): ").strip()
                if option == "1":
                    while True:
                        print("\nSelect category to add to cart:")
                        print("1. Chair")
                        print("2. Bed")
                        print("3. Bookshelf")
                        print("4. DONE adding items")
                        category_choice = input("Enter choice (1-4): ").strip()
                        if category_choice == "4":
                            break
                        elif category_choice == "1":
                            product_type = "Chair"
                        elif category_choice == "2":
                            product_type = "Bed"
                        elif category_choice == "3":
                            product_type = "Bookshelf"
                        else:
                            print("Invalid choice. Please try again.")
                            continue
                        with Session(engine) as session:
                            display_items_by_category(session, product_type)
                            while True:
                                model_no = input(f"Enter model number for {product_type}: ").strip()
                                item = session.exec(
                                    select(product_classes[product_type]).where(product_classes[product_type].model_no == model_no)
                                ).first()
                                if item:
                                    break
                                else:
                                    print("Invalid model number. Please try again.")
                            while True:
                                try:
                                    quantity = int(input("Enter quantity: ").strip())
                                    if quantity <= 0:
                                        print("Quantity must be a positive integer.")
                                    elif quantity > item.stock_level:
                                        print(f"Insufficient stock. Available: {item.stock_level}")
                                    else:
                                        break
                                except ValueError:
                                    print("Invalid quantity. Please enter a number.")
                            cart_item = CartItem(cart_id=cart_id, product_type=product_type, model_no=model_no, quantity=quantity)
                            try:
                                insert_cart_items([cart_item])
                                print(f"Added {quantity} x {product_type} {model_no} to cart.")
                            except ValueError as e:
                                print(f"Error: {e}")
                elif option == "2":
                    list_cart_contents(cart_id)
                elif option == "3":
                    checkout_cart(cart_id)
                elif option == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")
    else:
        print("Invalid choice. Please try again.")