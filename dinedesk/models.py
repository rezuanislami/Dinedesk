from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# --- User Model (for Flask-Login) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# --- DineDesk Models ---
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_complete = db.Column(db.Boolean, default=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} - Table {self.table_number}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, preparing, ready, served
    menu_item = db.relationship('MenuItem')

    def __repr__(self):
        return f'<OrderItem {self.id} - Qty {self.quantity} of {self.menu_item.name}>'

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(10), nullable=False) # Storing as string for simplicity with form
    time = db.Column(db.String(5), nullable=False)  # Storing as string for simplicity with form
    guests = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reservation {self.name} - {self.date} {self.time}>'

# --- Database Initialization and Seeding ---
def init_db(app):
    with app.app_context():
        db.create_all()
        # Seed initial menu items if the table is empty
        if MenuItem.query.count() == 0:
            db.session.add_all([
                MenuItem(name='Burger', price=12.50, category='Main'),
                MenuItem(name='Fries', price=4.00, category='Side'),
                MenuItem(name='Coke', price=2.50, category='Drink'),
                MenuItem(name='Salad', price=8.00, category='Main'),
            ])
            db.session.commit()
        
        # Seed a default user for login functionality
        if User.query.count() == 0:
            admin = User(username='admin')
            admin.set_password('password') # Use a secure password in production
            db.session.add(admin)
            db.session.commit()
