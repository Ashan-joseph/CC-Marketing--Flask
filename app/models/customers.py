from app.extensions import db
from sqlalchemy.orm import relationship

class Customers(db.Model):
    __tablename__ = "customers"

    id         =  db.Column(db.Integer, primary_key=True)
    member_id  =  db.Column(db.String, nullable=True)
    preferred_category  =  db.Column(db.String, nullable=True)
    preferred_city	  =  db.Column(db.String, nullable=True)
    preferred_merchant	  =  db.Column(db.String, nullable=True)
    total_amount  =  db.Column(db.String, nullable=True)
    average_amount  =  db.Column(db.String, nullable=True)
    transaction_count  =  db.Column(db.String, nullable=True)
    last_transaction_date  =  db.Column(db.String, nullable=True)
    gender  =  db.Column(db.String, nullable=True)
    is_marketing_suitable	  =  db.Column(db.String, nullable=True)
    segment_name  =  db.Column(db.String, nullable=True)
    is_recomended =  db.Column(db.String, nullable=True)
    status  =  db.Column(db.String, nullable=True)
    created_at  =  db.Column(db.String, nullable=True)
    updated_at  =  db.Column(db.String, nullable=True)

    recommendations = relationship("Recommendations", back_populates="customer")