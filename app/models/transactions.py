from app.extensions import db

class Transactions(db.Model):
    id         =  db.Column(db.Integer, primary_key=True)
    member_id  =  db.Column(db.String, nullable=True)
    card_type  =  db.Column(db.String, nullable=True)
    category_code  =  db.Column(db.String, nullable=True)
    merchant_name  =  db.Column(db.String, nullable=True)
    city  =  db.Column(db.String, nullable=True)
    country  =  db.Column(db.String, nullable=True)
    customer_transaction_type  =  db.Column(db.String, nullable=True)
    transaction_amount  =  db.Column(db.String, nullable=True)
    gender  =  db.Column(db.String, nullable=True)
    transaction_date  =  db.Column(db.String, nullable=True)
    transaction_id  =  db.Column(db.String, nullable=True)
    status  =  db.Column(db.String, nullable=True)
    created_at  =  db.Column(db.String, nullable=True)
    updated_at  =  db.Column(db.String, nullable=True)