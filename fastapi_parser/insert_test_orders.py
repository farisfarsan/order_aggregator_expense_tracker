from db.database import get_db
from db.models import Order
from datetime import datetime

db = next(get_db())

sample_orders = [
    Order(user_id=1, item_name="Amazon Order", amount=150.0, date=datetime.now()),
    Order(user_id=1, item_name="Flipkart Purchase", amount=200.0, date=datetime.now()),
]

db.add_all(sample_orders)
db.commit()
print("✅ Inserted test orders.")
