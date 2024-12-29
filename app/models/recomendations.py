from app.extensions import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Recommendations(db.Model):
    __tablename__ = "recommendations"

    id         =  db.Column(db.Integer, primary_key=True)
    customer_id  =  db.Column(db.Integer,ForeignKey('customers.id'), nullable=True)
    mcc  =  db.Column(db.String, nullable=True)
    score  =  db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    is_interacted  =  db.Column(db.String, nullable=True)

    customer = relationship("Customers", back_populates="recommendations")
