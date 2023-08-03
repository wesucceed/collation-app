import json
import os

from db import db
from db import load_excel
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
    load_excel()
    
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


@app.route("/sendallconstituenciesresults/")
def send_all_results_by_constituency():
    """
    Endpoint to get all results by constituency
    """
    body = json.loads(request.data)

    success, res = dao.get_all_results_by_constituency()

    if not success:
        return failure_response("Failed to get results")
    
    return success_response(res)


@app.route("/sendregionresults/")
def send_results_by_region():
    """
    Endpoint to get results by region
    """
    body = json.loads(request.data)
    region_name = body.get("region name")

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

@app.route("/pollingagent/<int:id>/")
def get_polling_agent_by_id(id):
    """
    Endpoint to get polling agent by id
    """
    polling_agent = dao.get_polling_agent_by_id(id)

    if not polling_agent:
        return failure_response("Polling agent does not exists")
    
    return success_response(polling_agent.serialize())


###################################################################
#######################POSTS REQUESTS##############################


@app.route("/submitresult/<int:polling_agent_id>/", methods = ["POST"])
def submit_result(polling_agent_id, polling_station_id):
    """
    Endpoint to create a result
    """
    # verify session
    # get inputs
    body = json.loads(request.data)
    data = body.get("data")
    total_rejected_ballots = body.get("total rejected ballots")
    total_votes_cast = body.get("total votes cast")
    total_valid_ballots = body.get("total valid ballots")
    pink_sheet = body.get("pinksheet")
    code = body.get("verification_code")
    polling_station_id = body.get("polling_station_id")

    success, polling_agent = dao.verify_sms_code(code, polling_agent_id)

    if not success:
        return failure_response("Invalid verification code!")

    if not (data and total_rejected_ballots and total_votes_cast and total_valid_ballots and pink_sheet):
        return failure_response("Invalid inputs!")
    
    created, polling_station_result = dao.create_polling_station_result(data, 
                                                                        total_votes_cast, 
                                                                        total_rejected_ballots,
                                                                        total_valid_ballots,
                                                                        pink_sheet,
                                                                        polling_agent_id,
                                                                        polling_station_id)
    
    if not created:
        return failure_response("Results already exists", 400)
    
    return success_response(polling_station_result, 201)

@app.route("/verifypollingagent/", methods = ["POST"])
def verify_polling_agent_existence():
    """
    Endpoint to verify polling agent existence
    """
    body = json.loads(request.data)
    firstname = body.get("firstname")
    lastname = body.get("lastname")
    phone_number = body.get("phone_number")

    if not (firstname and lastname and phone_number):
        return failure_response("Invalid inputs!")
    
    name = firstname + " " + lastname
    success, polling_agent = dao.get_polling_agent_by_name(name)

    if not success:
        return failure_response("Incorrect credentials", 400)
    
    success = polling_agent.verify_polling_agent(name, phone_number)

    if not success:
        return failure_response("Incorrect credentials", 400)
    
    polling_agent.renew_totp()

    sent = sendmessage(polling_agent.phone_number, polling_agent.get_totp())

    if not sent:
        return failure_response("Incorrect credentials", 400)
    
    return success_response({"success" : "Verification code sent!"}, 201)

@app.route("/setpassword/", methods = ["POST"])
def set_password():
    """
    Endpoint to verify polling agent existence
    """
    body = json.loads(request.data)
    password = body.get("password")
    verification_code = body.get("verification_code")
    firstname = body.get("firstname")
    lastname = body.get("lastname")
    phone_number = body.get("phone_number")
    
    if not (firstname and lastname and password and verification_code and phone_number):
        return failure_response("Invalid inputs!")
    
    name = firstname + " " + lastname

    polling_agent = dao.get_polling_agent(name, phone_number)

    if not polling_agent:
        return failure_response("Incorrect credentials!")

    verified = polling_agent.verify_totp(verification_code)   

    if not verified:
        return failure_response("Invalid credentials") 
    
    polling_agent.renew_password_digest(password)
    
    res = {
        "session_token" : polling_agent.session_token,
        "session_expiration" : polling_agent.session_expiration,
        "update_token" : polling_agent.update_token
    }

    return success_response(res, 201)

    


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

    if not (firstname and lastname and password):
        return failure_response("Invalid inputs", 400)
    
    name = firstname + " " + lastname
    success, polling_agent = dao.verify_login_credentials(name, password)

    if not success:
        return failure_response("Invalid credentials")
    
    res = {
        "session_token" : polling_agent.session_token,
        "session_expiration" : polling_agent.session_expiration,
        "update_token" : polling_agent.update_token
    }

    return success(res)

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

@app.route("/session/", methods=["POST"])
def update_session():
    success, update_token = extract_token(request)

    if not success:
        return failure_response(update_token)
    
    polling_agent = dao.renew_session(update_token)

    if not polling_agent:
        return failure_response("Invalid update token")
    
    res = {
        "session_token" : polling_agent.session_token,
        "session_expiration" : polling_agent.session_expiration,
        "update_token" : polling_agent.update_token
    }

    return success(res, 201)


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


@app.route("/sendtoken/", methods=["POST"])
def send_token():
    """
    Endpoint to send vefication token via sms
    """
    success, session_token = extract_token(request)
    if not success:
        return failure_response(session_token)
    
    polling_agent = dao.get_polling_agent_by_session_token(session_token)

    if not polling_agent or not polling_agent.verify_session_token(session_token):
        return failure_response("Invalid session token")
    

#endpoint to create an acc
#endpoint to load excel into database

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

