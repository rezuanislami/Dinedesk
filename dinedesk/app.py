from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------- DATABASE CONFIG ----------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dinedesk.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------- MODELS ----------
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    guests = db.Column(db.Integer)
    notes = db.Column(db.Text)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    total = db.Column(db.Float)
    items = db.Column(db.Text)  # JSON string of items
    notes = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    order_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.now())

# Create tables + Seed default admin user
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', password='1234')
        db.session.add(user)
        db.session.commit()


# ---------- LOGIN REQUIRED DECORATOR ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("base.html")


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            flash("Login successful!")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!")
    return redirect(url_for("login"))


# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():
    reservations = Reservation.query.order_by(Reservation.id.desc()).all()
    return render_template("dashboard.html", reservations=reservations)


# ---------- CREATE RESERVATION ----------
@app.route("/reservation", methods=["GET", "POST"])
@login_required
def reservation_form():
    if request.method == "POST":
        new_res = Reservation(
            name=request.form["name"],
            email=request.form["email"],
            date=request.form["date"],
            time=request.form["time"],
            guests=request.form["guests"],
            notes=request.form.get("notes", "")
        )
        db.session.add(new_res)
        db.session.commit()
        flash("Reservation added successfully!")
        return redirect(url_for("dashboard"))

    return render_template("reservation_form.html")


# ---------- EDIT RESERVATION ----------
@app.route("/reservation/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_reservation(id):
    res = Reservation.query.get_or_404(id)

    if request.method == "POST":
        res.name = request.form["name"]
        res.email = request.form["email"]
        res.date = request.form["date"]
        res.time = request.form["time"]
        res.guests = request.form["guests"]
        res.notes = request.form.get("notes", "")

        db.session.commit()
        flash("Reservation updated!")
        return redirect(url_for("dashboard"))

    return render_template("edit_reservation.html", res=res)


# ---------- DELETE ----------
@app.route("/reservation/delete/<int:id>")
@login_required
def delete_reservation(id):
    res = Reservation.query.get_or_404(id)
    db.session.delete(res)
    db.session.commit()
    flash("Reservation deleted.")
    return redirect(url_for("dashboard"))
    
@app.route("/menu")
@login_required
def menu():
    menu_items = [
        {"name": "Grilled Salmon", "category": "Main Course", "price": 24.99},
        {"name": "Caesar Salad", "category": "Appetizer", "price": 12.99},
    ]
    return render_template("menu.html", menu_items=menu_items)

@app.route("/new_order")
@login_required
def new_order():
    menu_data = {
        "appetizer": [
            {"id": 1, "name": "Bruschetta", "price": 8.99, "emoji": "🍞"},
            {"id": 2, "name": "Garlic Bread", "price": 6.99, "emoji": "🧄"},
        ],
        "main": [
            {"id": 11, "name": "Grilled Salmon", "price": 24.99, "emoji": "🐟"},
        ],
        # Add more categories...
    }
    return render_template("new_order.html", menu_data=menu_data)


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(debug=True)
