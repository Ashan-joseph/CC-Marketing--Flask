from flask import Flask, render_template, request, jsonify
from app.extensions import db
from app.blueprints import customer
from app.blueprints import campaign

app = Flask(__name__)
app.register_blueprint(customer.bp)
app.register_blueprint(campaign.bp)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/apiit'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning

db.init_app(app)

@app.route("/", methods=['GET'])
def home():
    return render_template("home.html")

@app.route("/api/get-sample", methods=["POST"])
def test():
    data = request.json
    username = data["username"]
    return jsonify({"message": "Login successful!", "username": username})
