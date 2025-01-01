from flask import Blueprint, jsonify,request, render_template
from app.extensions import db
from app.models.transactions import Transactions as TransactionModel
from app.models.categories import Categories as CategoryModel
from app.models.customers import Customers as CustomerModel
from app.models.recomendations import Recommendations as RecommendationsModel
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder,StandardScaler
import joblib
from sqlalchemy import not_
import pickle
import json

bp = Blueprint("customer",__name__)

@bp.route("/search-customer", methods=["GET"])
def search_customer_view():
    return render_template("customer/index.html")

@bp.route("/view-customer", methods=["GET"])
def view_customer():
    return render_template("customer/show.html")  

@bp.route("/api/process-customer/", methods=["GET"])
def index():
    
    try:
        trans = TransactionModel.query.all()
        data = [row.__dict__ for row in trans]

        for item in data:
            item.pop('_sa_instance_state', None)

        #transactions in a df
        trans_df  = pd.DataFrame(data)

        le = LabelEncoder()
        trans_df['member_id'] = le.fit_transform(trans_df['member_id']) #label encode member id

        df  = remove_unnecessary_transactions(trans_df)       

        cleaned_data = clean_data(df)
        copy_data = cleaned_data

        profile_data = get_customer_profile_info(cleaned_data)

        full_profile = get_preferred_merchant(profile_data,copy_data)
        save_dataframe_to_mysql(full_profile, 'customers', db.engine)

        return jsonify({"error": "false", "message": 'Updated'})
    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500

def remove_unnecessary_transactions(df):

    category_list = []
    categories = CategoryModel.query.filter_by(status='1').all()

    for row in categories:
        category_list.append(row.category_code)

    categories_array = np.array(category_list)
    df = df[df['category_code'].isin(categories_array)]
    return df    

def clean_data(df):

    df.dropna(inplace=True)
    df = df[df['customer_transaction_type'] != 'IN']
    df.drop(['customer_transaction_type'], axis=1, inplace=True)

    dfg = pd.get_dummies(df["gender"]).astype(int)
    new_data =pd.concat([df,dfg],axis=1)
    new_data.drop(["gender"],axis=1,inplace=True)
    new_data.drop(["F"],axis=1,inplace=True)
    new_data.rename(columns={'M': 'gender'}, inplace=True)
    return new_data

def get_customer_profile_info(cleaned_data):

    customer_profile = cleaned_data.groupby('member_id').agg({
    'transaction_date': [('last_Transaction_Date', 'max')], 
    'transaction_amount': [
        ('total_Amount', 'sum'),  
        ('average_Amount', 'mean'),  
        ('transaction_Count', 'count')  
    ],
    'category_code': [('preferred_Category', lambda x: x.mode().iloc[0] if not x.mode().empty else None)],
    'city': [('preferred_City', lambda x: x.mode().iloc[0] if not x.mode().empty else None)], 
    'gender': [('gender', 'first')] 
    }).reset_index()

    customer_profile.columns = ['member_id', 'last_transaction_date', 'total_amount', 'average_amount', 'transaction_count',
                            'preferred_category','preferred_city',  'gender']
                        
    return customer_profile

def get_preferred_merchant(customer_profile,copy_data):

    precomputed = (
        copy_data.groupby(['member_id', 'category_code'])['merchant_name']
        .agg(lambda x: x.mode()[0]) 
        .reset_index()
        .rename(columns={'merchant_name': 'preferred_merchant'})
    )

    customer_profile = customer_profile.merge(
        precomputed,
        how='left',  
        left_on=['member_id', 'preferred_category'],
        right_on=['member_id', 'category_code']
    )

    customer_profile = customer_profile.drop(columns=['category_code'])

    return customer_profile

def save_dataframe_to_mysql(df, table_name, engine):

    df.to_sql(table_name, con=engine, if_exists='append', index=False)

@bp.route("/api/predict-suitability", methods=["GET"])
def predict():

    try:

        model_path = r"C:\Apiit\CC Marketing\marketing_predict.joblib"
        model = joblib.load(model_path)

        customers = CustomerModel.query.all()

        for customer in customers:

            features = pd.DataFrame([[customer.total_amount,customer.average_amount,customer.transaction_count]], 
            columns=["total_amount", "average_amount", "transaction_count"])       
            
            prediction = model.predict(features)
            customer.is_marketing_suitable =  prediction[0]
            db.session.commit()

        return jsonify({"error": "false", "message": 'prediction ran successfully'})
    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500

        
@bp.route("/api/customer-segment", methods=["GET"])
def predict_segment():
    try:
        model  = joblib.load('kmeans_model.pkl')
        model_path = r"C:\Apiit\CC Marketing\scaler.pkl"
        scaler = joblib.load(model_path)

        CustomerModel.query.filter_by(is_marketing_suitable=0).update({"segment_name": 'Low Engagement'})

        customers = CustomerModel.query.filter(
                        CustomerModel.is_marketing_suitable == 1,
                        CustomerModel.segment_name.is_(None)  # IS NULL condition
                    ).limit(1000).all()

        for customer in customers:

            feature_names = ['total_amount','transaction_count']
            features = pd.DataFrame([[customer.total_amount,customer.transaction_count]], columns=feature_names) 

            x_scaled = scaler.transform(features)

            cluster = model.predict(x_scaled)

            if(cluster[0] == 1):
                CustomerModel.query.filter_by(id=customer.id).update({"segment_name": 'Budget Spenders'})
            elif(cluster[0] == 2):
                CustomerModel.query.filter_by(id=customer.id).update({"segment_name": 'High Spenders'})
            else:
                CustomerModel.query.filter_by(id=customer.id).update({"segment_name": 'Moderate Spenders'})

        db.session.commit()

        return jsonify({"error": "false", "message": 'segment predicted'})

    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500

@bp.route("/api/get-customer-recomendations", methods=["GET"])
def get_recomendations():

    try:

        user_item          = joblib.load('user_item_matrix.pkl')
        similarity_matrix  = joblib.load('item_similarity_matrix.pkl')

        customers = CustomerModel.query.filter(
                CustomerModel.status == 1,
                CustomerModel.is_recomended == 0,
        ).limit(1000).all()


        for customer in customers:
            status,interacted,recomendations = get_customer_recomendation(customer.member_id,user_item,similarity_matrix)

            if status=='false':

                for category_code, score in recomendations.items():
                    recommend_mcc = RecommendationsModel(
                        customer_id   = customer.id,
                        mcc           = category_code,
                        score         = score,
                        is_interacted = 0
                    )
                    db.session.add(recommend_mcc)
                    db.session.commit()
                for category_code, score in interacted.items():
                    interacted_mcc = RecommendationsModel(
                        customer_id    = customer.id,
                        mcc            = category_code,
                        score          = score,
                        is_interacted  = 1
                    )
                    db.session.add(interacted_mcc)
                    db.session.commit()
            else:
                customer.is_recomended =  '2'
                db.session.commit()

            customer.is_recomended =  '1'
            db.session.commit()

        return jsonify({"error": "false", "message": 'Customer Recomendtion done'})


    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500
    
def get_customer_recomendation(member_id, user_data, similarity_matrix, top_n=2):

    if member_id not in user_data.index:
        return 'true',[],[]
    user_vector = user_data.loc[member_id].values
    # Predict scores for all items based on similarity
    scores = np.dot(user_vector, similarity_matrix)
    # Convert scores to a Pandas Series
    scores_series = pd.Series(scores.flatten(), index=similarity_matrix.columns)
    
    already_interacted = user_data.loc[member_id][user_data.loc[member_id] > 0].index
    interacted_with_score = scores_series[already_interacted]
    scores_series = scores_series.drop(already_interacted)
    
    recommendations = scores_series.sort_values(ascending=False).head(top_n)
    return 'false',interacted_with_score,recommendations

@bp.route("/api/search-customer",methods=["POST"])
def search_customer():

    try:
        data = request.json
        customer_id = data["customer_id"]

        customer_data = CustomerModel.query.filter(CustomerModel.member_id==customer_id).first()

        customer_data = {
            "member_id": customer_data.id,
            "preferred_merchant" : customer_data.preferred_merchant,
            "preferred_city": customer_data.preferred_city,
            "preferred_category": get_mcc_name(customer_data.preferred_category),
            "is_marketing_suitable": customer_data.is_marketing_suitable,
            "segment": customer_data.segment_name,
            "total_transactions" : customer_data.total_amount,
            "transaction_count" : customer_data.transaction_count,
            "average_amount" : customer_data.average_amount,
            "interacted_mcc" : get_interacted_mcc(customer_data.id),
            "recomended_mcc" : get_recomended_mcc(customer_data.id)
        }

        return jsonify({"error":"false","message": "Customer fetched!", "customer_data": customer_data})
    
    except Exception as e:
        return jsonify({"error": "true",'message': f'An unexpected error occurred: {str(e)}'}), 500

def get_interacted_mcc(customer_id):

    try:
        recomdendations = RecommendationsModel.query.filter(
                            RecommendationsModel.customer_id == customer_id,
                            RecommendationsModel.is_interacted ==1).order_by(RecommendationsModel.score.desc()).all()

        interacted_list = []

        for recomendation in recomdendations:
            category_data = CategoryModel.query.filter(CategoryModel.category_code == recomendation.mcc).first()
            interacted_list.append(category_data.name)

        return interacted_list
    except Exception as e:
            return []

def get_recomended_mcc(customer_id):

    try:
        recomdendations = RecommendationsModel.query.filter(
                            RecommendationsModel.customer_id == customer_id,
                            RecommendationsModel.is_interacted ==0).order_by(RecommendationsModel.score.desc()).all()

        recomended_list = []

        for recomendation in recomdendations:
            category_data = CategoryModel.query.filter(CategoryModel.category_code == recomendation.mcc).first()
            recomended_list.append(category_data.name)

        return recomended_list
    except Exception as e:
        return []
    
def get_mcc_name(mcc_code):
    try:
        category_data = CategoryModel.query.filter(CategoryModel.category_code == mcc_code).first()
        return category_data.name
    except Exception as e:
        return 'N/A'
