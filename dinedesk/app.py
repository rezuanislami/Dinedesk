from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import json
from datetime import datetime
import queue

from flask_migrate import Migrate


# ================================
# APP SETUP
# ================================
app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------- DATABASE CONFIG ----------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dinedesk.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)      # ✅ FIXED: Now app and db exist


# ================================
# MODELS
# ================================
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
    items = db.Column(db.Text)
    notes = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    order_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default="incoming")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ---------- Auto-create DB + admin account ----------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        user = User(username="admin", password="1234")
        db.session.add(user)
        db.session.commit()


# ================================
# HELPERS
# ================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ================================
# SSE DATA
# ================================
orders = []        # real-time kitchen order list
sse_queues = []    # connected SSE clients


# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return render_template("base.html")


# ---------- AUTH ----------
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


# ---------- RESERVATIONS ----------
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


@app.route("/reservation/delete/<int:id>")
@login_required
def delete_reservation(id):
    res = Reservation.query.get_or_404(id)
    db.session.delete(res)
    db.session.commit()
    flash("Reservation deleted.")
    return redirect(url_for("dashboard"))


# ---------- MENU ----------
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
    return render_template("new_order.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/save_restaurant", methods=["POST"])
def save_restaurant():
    data = {
        "name": request.form.get("restaurant-name"),
        "phone": request.form.get("restaurant-phone"),
        "email": request.form.get("restaurant-email"),
        "address": request.form.get("restaurant-address"),
        "opening": request.form.get("opening-time"),
        "closing": request.form.get("closing-time")
    }
    with open("restaurant_settings.json", "w") as f:
        json.dump(data, f, indent=4)

    return redirect(url_for("settings"))


# ---------- FLOOR ----------
@app.route("/floor")
def floor_plan():
    reservations = [
        {"id": 1, "name": "Phillipe Carrera-Jones", "guests": 4, "time": "11:00", "table": "C224", "status": "seated"},
        {"id": 2, "name": "Jane Doe", "guests": 2, "time": "12:30", "table": "22", "status": "confirmed"},
    ]
    tables = [
        {"id": "C224", "room": "indoor", "shape": "round", "size": "60px", "top": "100px", "left": "150px", "capacity": 4},
        {"id": "22", "room": "indoor", "shape": "square", "size": "60px", "top": "100px", "left": "250px", "capacity": 2},
    ]
    return render_template("floor.html", reservations=reservations, tables=tables)


@app.route("/staff")
def staff():
    return render_template("staff.html")


@app.route("/kitchen")
@login_required
def kitchen():
    return render_template("kitchen.html")


# ================================
# REAL-TIME ORDER SYSTEM (SSE)
# ================================
@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.get_json()

    if not data or "customer" not in data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        # Save in DB
        order_model = Order(
            customer_name=data["customer"],
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            total=float(data["total"]),
            items=json.dumps(data["items"]),
            notes=data.get("notes", ""),
            payment_method=data["paymentMethod"],
            order_type=data["orderType"],
            status="incoming"
        )
        db.session.add(order_model)
        db.session.commit()

        # Order dictionary to broadcast
        order = {
            "id": order_model.id,
            "customer": data["customer"],
            "phone": data.get("phone", ""),
            "notes": data.get("notes", ""),
            "items": data["items"],
            "paymentMethod": data["paymentMethod"],
            "orderType": data["orderType"],
            "total": data["total"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "incoming"
        }

        orders.append(order)

        # Broadcast to kitchen
        msg = f"data: {json.dumps(order)}\n\n"
        for q in sse_queues[:]:
            try:
                q.put(msg)
            except:
                sse_queues.remove(q)

        return jsonify({"success": True, "order_id": order_model.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/update_order_status", methods=["POST"])
def update_order_status():
    data = request.get_json()
    order_id = data.get("orderId")
    new_status = data.get("status")

    if not order_id or not new_status:
        return jsonify({"error": "Missing orderId or status"}), 400

    # DB update
    order_model = Order.query.get(order_id)
    if order_model:
        order_model.status = new_status
        db.session.commit()

    # Update in-memory
    for order in orders:
        if order["id"] == order_id:
            order["status"] = new_status
            break

    return jsonify({"success": True})


@app.route("/events")
def events():
    def event_stream():
        q = queue.Queue()
        sse_queues.append(q)

        # Send existing incoming orders
        for o in Order.query.filter_by(status="incoming").all():
            payload = {
                "id": o.id,
                "customer": o.customer_name,
                "phone": o.phone,
                "notes": o.notes,
                "items": json.loads(o.items),
                "paymentMethod": o.payment_method,
                "orderType": o.order_type,
                "total": o.total,
                "timestamp": o.timestamp.isoformat(),
                "status": o.status
            }
            yield f"data: {json.dumps(payload)}\n\n"

        # Live updates
        try:
            while True:
                yield q.get()
        except GeneratorExit:
            if q in sse_queues:
                sse_queues.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


# ================================
# RUN SERVER
# ================================
if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
