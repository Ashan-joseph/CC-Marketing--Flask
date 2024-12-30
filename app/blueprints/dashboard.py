from flask import Blueprint, jsonify
from app.extensions import db
from app.models.categories import Categories as CategoryModel
from app.models.customers import Customers as CustomerModel
from sqlalchemy import func
import json
import os

bp = Blueprint("dashboard",__name__)

@bp.route("/api/generate-dashboard-json/", methods=["GET"])
def get_dashboard_data():

    try:
        total_customer_count =  CustomerModel.query.filter(CustomerModel.status == 1).with_entities(func.count(CustomerModel.id)).scalar()
        potential_count      =  CustomerModel.query.filter(
                                    CustomerModel.status == 1,CustomerModel.is_marketing_suitable == 1
                                ).with_entities(func.count(CustomerModel.id)).scalar()
        
        transaction_total    =  CustomerModel.query.filter(CustomerModel.status == 1).with_entities(func.sum(CustomerModel.total_amount)).scalar()

        low_key_users        =  CustomerModel.query.filter(CustomerModel.segment_name == 'Low Engagement').with_entities(func.count(CustomerModel.total_amount)).scalar()

        result = db.session.query(CustomerModel.preferred_category, func.sum(CustomerModel.total_amount)).group_by(CustomerModel.preferred_category).limit(10).all()

        category_list = []

        for data in result:
            cat_date = {
                "name": get_mcc_name(data[0]),
                "total" : "{:,}".format(data[1])
            }
            category_list.append(cat_date)

        dashboard_data = {
            "total_customer_count" : total_customer_count,
            "potantial_count"      : potential_count,
            "transaction_total"    : transaction_total,
            "low_key_users"        : low_key_users,
            "best_mcc"             : category_list
        }

        file_path = os.path.join('app', 'dashboard.json')
        chart_path = os.path.join('app', 'pie.png')

        with open(file_path, "w") as json_file:
            json.dump(dashboard_data, json_file, indent=4)

        return jsonify({"message": "Login successful!", "error": "false"})
    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500
    
def get_mcc_name(mcc_code):
    try:
        category_data = CategoryModel.query.filter(CategoryModel.category_code == mcc_code).first()
        return category_data.name
    except Exception as e:
        return 'N/A'