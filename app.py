import json
import os

from db import db
from db import load_excel
from flask import Flask, request
import dao
import datetime

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
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("Missing auth header!")
    
    bearer_token = auth_header.replace("Bearer", "").strip()
    if not bearer_token:
        return False, failure_response("Invalid auth header")
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
    constituency_name = body.get("constituency name")

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

@app.route("/pollingagent/<int:id>/")
def get_polling_agent_by_id(id):
    """
    Endpoint to get polling agent by id
    """
    polling_agent = dao.get_polling_agent_by_id(id)

    if not polling_agent:
        return failure_response("Polling agent does not exists")
    
    return success_response(polling_agent.serialize())

# @app.route("/sendallregionsresults/")
# def send_all_results_by_region():  #questionable
    """
    Endpoint to get results by region
    """

# @app.route("/sendcandidatesresults/")
# def send_results_by_candidate():
#     """
#     Endpoint to get results by candidate
#     """

# @app.route("/sendallcandidateresults/")
# def send_all_results_by_candidate():
#     """
#     Endpoint to get results by candidate
#     """

###################################################################
#######################POSTS REQUESTS##############################


@app.route("/submitresult/", methods = ["POST"])
def submit_result():
    """
    Endpoint to create a result
    """
    # verify session

    # get inputs
    body = json.loads(request.data)
    data, total_rejected_ballots, total_votes_cast, total_valid_ballots, pink_sheet, polling_agent_name, phone_number = body.get("data"),
    body.get("total rejected ballots"), body.get("total votes cast"), body.get("total valid ballots"). body.get("pinksheet"), body.get("polling agent name"),
    body.get("polling agent phone number")

    # do some verifications
    polling_station_id, polling_agent_id = None, None

    # make pinksheet in right format

    created, polling_station_result = dao.create_polling_station_result(data = data, 
                                                                              total_votes_casts = total_votes_cast, 
                                                                              total_rejected_ballots = total_rejected_ballots,
                                                                              total_valid_ballots = total_valid_ballots,
                                                                              pink_sheet  = pink_sheet,
                                                                              polling_agent_id = polling_agent_id,
                                                                              polling_station_id = polling_station_id)
    
    if not created:
        return failure_response("Results already exists", 400)
    
    res = polling_station_result.serialize()

    return success_response(res, 201)


# @app.route("/pollingagentlogin/", methods=["POST"])
# def login_by_polling_agent():
#     """
#     Endpoint for logging in a polling agent
#     """
#     # get login required inputs
#     body = json.loads(request.data)
#     constituency, polling_station_name, polling_station_number, polling_agent_name = body.get("region"),body.get("constituency"), 
#     body.get("polling_station_name"), body.get("polling_station_number"), body.get("polling_agent_name")
    

#     # invalid inputs
#     if not(region and constituency and polling_station_name and polling_station_number and polling_agent_name):
#         return failure_response("Invalid inputs", 400)
    
#     #check if polling station exists
#     existed, polling_station = users_dao.get_polling_station(polling_station_name, polling_station_number, constituency, region)
#     if not existed:
#         return failure_response("Polling station doesn't exists", 201)
    
#     # check if polling agent exists
#     existed, polling_agent = users_dao.get_polling_agent_by_name(polling_agent_name)
#     if not existed:
#         return failure_response("Polling agent doesn't exists", 201)
    
#     # # verify polling agent
#     # success, user = users_dao.verify_credentials(email, password)

#     # if not success:
#     #     return failure_response("Incorrect email or password!")
    
#     return success_response(
#         {
#             "session_token" : user.session_token,
#             "session_expiration" : str(user.session_expiration),
#             "update_token" : user.update_token
#         }
#     )


@app.route("/pollingagentlogout/", methods=["POST"])
def logout_by_polling_agent():
    """
    Endpoint for logging out a polling agent
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    
    user = dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return failure_response("Invalid session token!", 400)
    user.session_expiration = datetime.datetime.now()
    db.session.commit()
    return success_response({"message" : "User has successfully logged out!"})



@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)

    if not success:
        return update_token
    
    user = dao.renew_session(update_token)

    if user is None:
        return failure_response("Invalid update token!")
    
    return success_response(
        {
            "session_token" : user.session_token,
            "session_expiration" : str(user.session_expiration),
            "update_token" : user.update_token
        }
    )


@app.route("/secret/", methods=["POST"])
def secret_message():
    """
    Endpoint for verifying a session token and returning a secret message

    In your project, you will use the same logic for any endpoint that needs 
    authentication
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    
    user = dao.get_user_by_session_token(session_token)

    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
    
    return success_response({"message" : "Wow we implemented session token!!"}, 201)

@app.route("/sendtoken/", methods=["POST"])
def send_token():
    """
    Endpoint to send vefication token via sms
    """

# manipulate data

# filtering using keys

# if new data is added, notify, cache the result, get from previous id
# what if more data submission made

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

