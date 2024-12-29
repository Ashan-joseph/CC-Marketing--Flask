from app.extensions import db

class Campaigns(db.Model):
    id             =  db.Column(db.Integer, primary_key=True)
    campaign_name  =  db.Column(db.String, nullable=True)
    description    =  db.Column(db.String, nullable=True)
    status         =  db.Column(db.String, nullable=True)
