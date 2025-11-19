from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, init_db, User, MenuItem, Order, OrderItem, Reservation
from forms import LoginForm, ReservationForm
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'a-very-secret-key-that-should-be-changed'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dinedesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database and Login Manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Database on first request
with app.app_context():
    init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Authentication Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main Application Routes ---

@app.route('/dashboard')
@login_required
def dashboard():
    # Simple dashboard data
    total_orders = Order.query.count()
    pending_items = OrderItem.query.filter_by(status='pending').count()
    return render_template('dashboard.html', total_orders=total_orders, pending_items=pending_items)

@app.route('/clock')
@login_required
def clock():
    return render_template('clock.html')

# --- Waiter: Make a new order ---
@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    menu = MenuItem.query.all()  # Get all dishes from menu
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        if not table_number:
            flash("Error: Table number is required", 'error')
            return redirect(url_for('new_order'))

        order = Order(table_number=table_number)
        db.session.add(order)
        db.session.flush() # Get the order ID before commit

        has_items = False
        for item in menu:
            qty = request.form.get(f'qty_{item.id}')
            if qty and int(qty) > 0:
                order_item = OrderItem(order_id=order.id, menu_item_id=item.id, quantity=int(qty))
                db.session.add(order_item)
                has_items = True
        
        if has_items:
            db.session.commit()
            flash(f"Order for Table {table_number} placed successfully!", 'success')
            return redirect(url_for('kitchen'))
        else:
            db.session.rollback()
            flash("Error: Order must contain at least one item", 'error')
            return redirect(url_for('new_order'))

    return render_template('new_order.html', menu=menu)

# --- Kitchen: View and update tickets ---
@app.route('/kitchen')
@login_required
def kitchen():
    # Fetch all items that are not yet served, ordered by ID (oldest first)
    tickets = OrderItem.query.filter(OrderItem.status != 'served').order_by(OrderItem.id).all()
    return render_template('kitchen.html', tickets=tickets)

# --- Kitchen: Update item status ---
@app.route('/kitchen/update/<int:item_id>/<status>', methods=['POST'])
@login_required
def update_status(item_id, status):
    item = OrderItem.query.get_or_404(item_id)
    
    valid_statuses = ['pending', 'preparing', 'ready', 'served']
    if status not in valid_statuses:
        flash("Error: Invalid status", 'error')
        return redirect(url_for('kitchen'))

    item.status = status
    db.session.commit()
    flash(f"Item {item.menu_item.name} status updated to {status}", 'success')
    return redirect(url_for('kitchen'))

# --- Reservation Route ---
@app.route('/reservation', methods=['GET', 'POST'])
@login_required
def reservation():
    form = ReservationForm()
    if form.validate_on_submit():
        try:
            guests = int(form.guests.data)
            new_reservation = Reservation(
                name=form.name.data,
                phone=form.phone.data,
                date=form.date.data,
                time=form.time.data,
                guests=guests
            )
            db.session.add(new_reservation)
            db.session.commit()
            flash('Reservation successfully made!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Number of Guests must be a valid number.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')

    return render_template('reservation_form.html', form=form)

# --- Reporting Feature ---
@app.route('/report')
@login_required
def generate_report():
    # 1. Fetch all data
    all_orders = Order.query.all()
    all_reservations = Reservation.query.all()
    
    # 2. Render the report template with the data
    # The report.html template will be created in the next step
    report_html_content = render_template('report_template.html', 
                                          orders=all_orders, 
                                          reservations=all_reservations)
    
    # 3. Save the rendered content to report.html file
    report_path = 'report.html'
    with open(report_path, 'w') as f:
        f.write(report_html_content)
        
    flash(f"Report generated and saved to {report_path}", 'success')
    # 4. Serve the generated file or redirect to a view of it
    # For simplicity, we will redirect to the dashboard and inform the user
    # that the file is saved in the working directory.
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
