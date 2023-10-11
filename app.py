import json
import os

from db import db
from db import load_polling_stations
from flask import Flask, request
import dao
import datetime
from twilioapp import sendmessage

db_filename = "collation.db"
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.drop_all()
    db.create_all()
    
# generalized response formats
def success_response(data, code=200):
    """
    Generalized success response function
    """
    return json.dumps(data), code


def failure_response(message, code=404):
    """
    Generalized failure response function
    """
    return json.dumps({"error": message}), code

def extract_token(request):
    """
    Extract token from request
    """
    auth_header = request.headers.get("Authorization")

    if auth_header is None:
        return False, str("Missing auth header")
    
    bearer_token = auth_header.replace("Bearer", "").strip()

    if not bearer_token:
        return False, str("Invalid auth header")
    
    return True, bearer_token


@app.route("/")
def hello_world():
    """
    Endpoint for testing server
    """
    return "Hello, " + os.environ.get("ACTIVE")


################################################################
#####################GET REQUESTS################################  


@app.route("/sendconstituencyresults/")
def send_results_by_constituency():
    """
    Endpoint to get results by constituency
    """
    body = json.loads(request.data)
    constituency_name = body.get("constituency_name")

    if constituency_name is None:
        return failure_response("Invalid inputs")
    
    success, res = dao.get_result_by_constituency(name = constituency_name)

    if not success:
        return failure_response("Constituency does not exists")
    
    return success_response(res)



@app.route("/sendregionresults/")
def send_results_by_region():
    """
    Endpoint to get results by region
    """
    body = json.loads(request.data)
    region_name = body.get("region_name")

    if region_name is None:
        return failure_response("Invalid inputs")
    
    success, res = dao.get_result_by_region(name = region_name)

    if not success:
        return failure_response("Region does not exists")
    
    return success_response(res)


@app.route("/sendallresults/")
def send_all_results():
    """
    Endpoint to get all results
    """
    
    success, res = dao.get_all_results()

    if not success:
        return failure_response("Results is empty")
    
    return success_response(res)

# @app.route("/pollingagent/<int:id>/")
# def get_polling_agent_by_id(id):
#     """
#     Endpoint to get polling agent by id
#     """
#     polling_agent = dao.get_polling_agent_by_id(id)

#     if not polling_agent:
#         return failure_response("Polling agent does not exists")
    
#     return success_response(polling_agent.serialize())


###################################################################
#######################POSTS REQUESTS##############################

@app.route("/createpollingstations/", methods = ["POST"])
def create_polling_stations():
    """
    Endpoint to create polling_stations
    """
    success = load_polling_stations()

    if not success:
        return failure_response("Couldn't load polling stations", 400)
    
    return success_response("Created polling stations", 201) 


@app.route("/pollingagent/", methods = ["POST"])
def create_polling_agent():
    """
    Endpoint to create a polling agent account
    """
    body = json.loads(request.data)
    
    firstname = body.get("firstname")
    lastname = body.get("lastname")
    password = body.get("password")
    phone_number = body.get("phone_number")
    polling_station_name = body.get("polling_station_name")
    polling_station_number = body.get("polling_station_number")
    constituency_name = body.get("constituency_name")
    region_name = body.get("region_name")

    if not (phone_number and firstname and lastname and password and polling_station_name and polling_station_number and constituency_name and region_name):
        return failure_response("Invalid inputs!", 400)
    
    success, polling_station = dao.get_polling_station(polling_station_name, polling_station_number, constituency_name, region_name)

    if not success:
        return failure_response("Polling station does not exists!", 400)
    
    if len(polling_station.serialize().get("polling_agent")):
        return failure_response("Polling station occupied", 400)
    
    name = firstname + " " + lastname
    created, polling_agent = dao.create_polling_agent(name, phone_number, password, polling_station.id)

    if not created:
        return failure_response("Polling Agent already exists", 400)

    res = {
        "session_token" : polling_agent.session_token
    }

    return success_response(res, 201)



# TODO: WORK ON THIS
@app.route("/submitresult/<int:polling_agent_id>/", methods = ["POST"])
def submit_result(polling_agent_id):
    """
    Endpoint to create a result
    """
    body = json.loads(request.data)
    
    data = body.get("data")
    total_rejected_ballots = body.get("total_rejected_ballots")
    total_votes_cast = body.get("total_votes_casts")
    total_valid_ballots = body.get("total_valid_ballots")
    pink_sheet = body.get("pinksheet")
    auto_password = body.get("auto_password")
    polling_station_id = body.get("polling_station_id")
    data, success_code = secret_message()

    if success_code != 201 or json.loads(data) != "Session verified!":
        return failure_response("Session expired", 400)

    provided_all_data = data and total_rejected_ballots and total_votes_cast and total_valid_ballots and pink_sheet and auto_password and polling_station_id
    if not (provided_all_data):
        return failure_response("Invalid inputs!", 400)
    
    created, polling_station_result = dao.create_polling_station_result(data, 
                                                                        total_votes_cast, 
                                                                        total_rejected_ballots,
                                                                        total_valid_ballots,
                                                                        pink_sheet,
                                                                        polling_agent_id,
                                                                        polling_station_id,
                                                                        auto_password)
    
    if not created:
        return failure_response("Couldn't create result", 400)
    
    return success_response(polling_station_result.serialize(), 201)
    

@app.route("/pollingagentlogin/", methods=["POST"])
def login_by_polling_agent():
    """
    Endpoint for logging in a polling agent
    """
    # get login required inputs
    body = json.loads(request.data)
    firstname = body.get("firstname")
    lastname = body.get("lastname")
    password = body.get("password")
    
    totp_key = body.get("totp_key")
    totp_value = body.get("totp_value")

    if not (firstname and lastname and password and totp_key and totp_value):
        return failure_response("Invalid inputs", 400)
    
    name = firstname + " " + lastname
    success, polling_agent = dao.verify_login_credentials(name, password)

    if not success:
        return failure_response("Invalid credentials")
    success, polling_agent = dao.verify_totp_key(totp_key, totp_value, polling_agent.id)

    if not success:
        return failure_response("Invalid Totp")
    
    dao.renew_session(polling_agent)
    
    res = {
        "session_token" : polling_agent.session_token
    }

    return success_response(res)


@app.route("/pollingagentlogout/", methods=["POST"])
def logout_by_polling_agent():
    """
    Endpoint to logout polling agent
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response(session_token)
    
    polling_agent = dao.get_polling_agent_by_session_token(session_token)

    if not polling_agent or not polling_agent.verify_session_token(session_token):
        return failure_response("Invalid session token")
    
    polling_agent.session_expiration = datetime.datetime.now()

    db.session.commit()

    return success_response("Logout success", 201)


@app.route("/secret/", methods = ["POST"])
def secret_message():
    """
    Endpoint to verifying session token and returning a secret message
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response(session_token)
    
    polling_agent = dao.get_polling_agent_by_session_token(session_token)
    if not polling_agent or not polling_agent.verify_session_token(session_token):
        return failure_response("Invalid session token")
    
    return success_response("Session verified!", 201)


    

#endpoint to create an acc
#endpoint to load excel into database
#if the polling agent has to be replaced, we will do that
# endpoint for admin creation and login 
#TODO: endpoint to send results on regular intervals 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

