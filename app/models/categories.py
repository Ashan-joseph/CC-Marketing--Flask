from app.extensions import db

class Categories(db.Model):
    category_id         =  db.Column(db.Integer, primary_key=True)
    category_code	  =  db.Column(db.String, nullable=True)
    name  =  db.Column(db.String, nullable=True)
    status  =  db.Column(db.String, nullable=True)
