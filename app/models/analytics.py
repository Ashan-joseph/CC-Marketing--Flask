from app.extensions import db

class Analytics(db.Model):
    id                =  db.Column(db.Integer, primary_key=True)
    campaign_id       =  db.Column(db.String, nullable=True)
    targeted_count    =  db.Column(db.String, nullable=True)
    conversion_count  =  db.Column(db.String, nullable=True)
    status            =  db.Column(db.String, nullable=True)