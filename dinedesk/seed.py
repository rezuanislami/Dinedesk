from app import app
from models import db, Table, MenuItem, User

with app.app_context():
    # add some tables
    if Table.query.count() == 0:
        for i in range(1,9):
            t = Table(label=f"T{i}", seats=4)
            db.session.add(t)
    if MenuItem.query.count() == 0:
        db.session.add(MenuItem(name='Margherita', category='Pizza', price=8.5, cost=3.0))
        db.session.add(MenuItem(name='Pasta Carbonara', category='Mains', price=10.5, cost=4.0))
    db.session.commit()
    print("Seeded data")
