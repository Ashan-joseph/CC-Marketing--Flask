from flask import Blueprint, jsonify,request,render_template
from app.extensions import db
from app.models.transactions import Transactions as TransactionModel
from app.models.categories import Categories as CategoryModel
from app.models.customers import Customers as CustomerModel
from app.models.recomendations import Recommendations as RecommendationsModel
from app.models.campaigns import Campaigns as CampaignModel
from app.models.analytics import Analytics as AnalyticsModel
from sqlalchemy import not_

bp = Blueprint("campaign",__name__)

@bp.route("/marketings/inactive-customers", methods=["GET"])
def view_inactive_customer_marketing():
    return render_template("marketing/inactive.html")

@bp.route("/marketings/campaigns-by-mcc", methods=["GET"])
def view_capmpaigns_by_mcc():
    return render_template("marketing/campaign.html")

@bp.route("/marketings/serach-customer", methods=["GET"])
def search_customer():
    return render_template("customer/index.html")

@bp.route("/marketings/customer", methods=["GET"])
def view_customer():
    return render_template("customer/show.html")

@bp.route("/api/filter",methods=["POST"])
def filer_customer():
    data = request.json

    query = db.session.query(CustomerModel, RecommendationsModel).join(RecommendationsModel, CustomerModel.id == RecommendationsModel.customer_id)

    if data['mcc']:
        query = query.filter(RecommendationsModel.mcc == data['mcc'])
    if data['segment']:
        query = query.filter(CustomerModel.segment_name == data['segment'])
    if data['city']:
        query = query.filter(CustomerModel.preferred_city == data['city'])

    result = query.all()

    if data["is_create_campaign"] == '1':
        response = create_campaign(data,result)
        return response

    customer_list = []
    for customer_data, recommendation in result:
        
        customer_data = {
            "member_id": customer_data.id,
            "is_marketing_suitable": customer_data.is_marketing_suitable,
            "segment": customer_data.segment_name,
            "mcc_name" : get_mcc_name(recommendation.mcc),
            "city" : data['city'] if data['city'] else "All Cities",
            "type" : 'Already Interacted' if recommendation.is_interacted == 1 else "Recommneded by System",
            'average_spend' : customer_data.average_amount,
            "score" : recommendation.score

        }
        customer_list.append(customer_data)

    return jsonify({"error":"false","message": "Customers fetched!", "customer_data":customer_list})
    
@bp.route("/api/get-inactive-customers",methods=["POST"])
def inactive_customer():

    data = request.json

    if data['start_date'] == "" or data['end_date'] == "":
        return jsonify({"error":"true","message": "Date range is required", "customer_data":"null"})

    #query = db.session.query(CustomerModel, RecommendationsModel).join(RecommendationsModel, CustomerModel.id == RecommendationsModel.customer_id)
    query = db.session.query(CustomerModel, RecommendationsModel).join(RecommendationsModel, CustomerModel.id == RecommendationsModel.customer_id).filter(not_(CustomerModel.last_transaction_date.between(data['start_date'], data['end_date'])))

    if data['segment']:
        query = query.filter(CustomerModel.segment_name == data['segment'])
    
    result = query.all()

    if data["is_create_campaign"] == '1':
        response = create_campaign(data,result)
        return response

    customer_list = []
    for customer_data, recommendation in result:
        
        customer_data = {
            "member_id": customer_data.id,
            "segment": customer_data.segment_name,
            "preferred_mcc" : get_mcc_name(customer_data.preferred_category),
            "average_spend" : customer_data.average_amount,
            "last_transaction_date" : customer_data.last_transaction_date,
            "score" : recommendation.score

        }
        customer_list.append(customer_data)

    return jsonify({"error":"false","message": "Inactive customers fetched!", "customer_data":customer_list})

def get_mcc_name(mcc_code):
    try:
        category_data = CategoryModel.query.filter(CategoryModel.category_code == mcc_code).first()
        return category_data.name
    except Exception as e:
        return 'N/A'
    
def create_campaign(campaign_data,customers):

    try:
        new_campaign = CampaignModel(
            campaign_name = campaign_data['campaign_name'], 
            description   = campaign_data['campaign_description'],
            status        = '1'
        )

        db.session.add(new_campaign)
        db.session.commit()

        total_customer_count  = 0
        total_potential_count = 0

        for customer_data, recommendation in customers:

            total_customer_count += 1

            if(recommendation.score >=50):
                total_potential_count += 1
        
        analytis_data = AnalyticsModel(
            campaign_id      = new_campaign.id,
            targeted_count   = total_customer_count,
            conversion_count = total_potential_count,
            status           = '1'
        )

        db.session.add(analytis_data)
        db.session.commit()

        return jsonify({"error":"false","message": "campaign created successfully"})

    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500

@bp.route("/api/get-campaign-details",methods=["GET"])
def get_campaign_information():
    
    try:
        details = db.session.query(CampaignModel, AnalyticsModel).join(AnalyticsModel, CampaignModel.id == AnalyticsModel.campaign_id).filter(
                    CampaignModel.status == '1'
                ).all()
        
        campaign_data = []
        
        for campaign, analytics in details:
            campaign_details = {
                "campaign_name"   : campaign.campaign_name,
                "description"     : campaign.description,
                "targeted_count"  : analytics.targeted_count,
                "potential_count" : analytics.conversion_count,
                "success_rate"    : round((int(analytics.conversion_count)/ int(analytics.targeted_count)) * 100,2)
            }

            campaign_data.append(campaign_details)

        return jsonify({"error":"false","message": "campaign data fetched!", "campaign_data":campaign_data})
    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500
        
        
