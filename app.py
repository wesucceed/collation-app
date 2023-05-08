import json
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from db import db
from flask import Flask, request
import users_dao
import datetime

db_filename = "auth.db"
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
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
    Endpoint for printing Hello World!
    """
    return "Hello, " + os.environ.get("ACTIVE")


@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
    address = body.get("address")
    name = body.get("name")
    major = body.get("major")

    if email is None or password is None or  address is None or name is None or major is None:  
        return failure_response("invalid inputs", 400)
    
    created, user = users_dao.create_user(name, email, password, address, major)
    
    if not created:
        return failure_response("User already exists", 400)
    res = user.serialize()
    res.update({   
            "name" : user.name,
            "address" : user.address,
            "session_token" : user.session_token,
            "session_expiration" : str(user.session_expiration),
            "update_token" : user.update_token
        })
    return success_response(res)

@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    email = body.get("email")
    password = body.get("password")
    
    if email is None or password is None:
        return failure_response("Invalid inputs!")
    
    success, user = users_dao.verify_credentials(email, password)

    if not success:
        return failure_response("Incorrect email or password!")
    
    return success_response(
        {
            "session_token" : user.session_token,
            "session_expiration" : str(user.session_expiration),
            "update_token" : user.update_token
        }
    )


@app.route("/session/", methods=["POST"])
def update_session():
    """
    Endpoint for updating a user's session
    """
    success, update_token = extract_token(request)

    if not success:
        return update_token
    
    user = users_dao.renew_session(update_token)

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
    
    user = users_dao.get_user_by_session_token(session_token)

    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
    
    return success_response({"message" : "Wow we implemented session token!!"}, 201)


@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, session_token = extract_token(request)
    if not success:
        return session_token
    
    user = users_dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return failure_response("Invalid session token!", 400)
    user.session_expiration = datetime.datetime.now()
    db.session.commit()
    return success_response({"message" : "User has successfully logged out!"})

@app.route("/address/", methods=["GET"])
def get_partners_by_address():
    """
    Endpoint for getting partners by location
    """
    body = json.loads(request.data)
    address = body.get("address")

    if address is None:
        return failure_response("Invalid inputs!")
    
    users = users_dao.get_user_by_address(address)

    if users is None:
        pass
    else:
        res = []
        for user in users:
            res.append(user.serialize())
        return success_response({"users" : res})


@app.route("/major/", methods=["GET"])
def get_partners_by_major():
    """
    Endpoint for getting partners by major
    """
    body = json.loads(request.data)
    major = body.get("major")

    if major is None:
        return failure_response("Invalid inputs!")
    
    users = users_dao.get_user_by_major(major)

    if users is None:
        pass
    else:
        res = []
        for user in users:
            res.append(user.serialize())
        return success_response({"users" : res})
    
    
@app.route("/closest/", methods=["GET"])
def get_closest_user():
    """
    Endpoint for getting partners by major
    """
    body = json.loads(request.data)
    email = body.get("email")

    if email is None:
        return failure_response("Invalid inputs!")
    user = users_dao.get_user_by_email(email)

    if user is None:
        return failure_response("user doesn't exists!")
    user1 = users_dao.get_closest_user(user)

    return success_response({"user" : user1.serialize()})


@app.route("/request/", methods=["GET"])
def request_partner():
    """
    Endpoint for requesting for a partner
    """
    body = json.loads(request.data)
    sender_email = body.get("sender email")
    receiver_email = body.get("receiver email")
    if sender_email is None or receiver_email is None:
        return failure_response("Invalid inputs!")
    sender = users_dao.get_user_by_email(sender_email)
    receiver = users_dao.get_user_by_email(receiver_email)

    if sender is None or receiver is None:
        return failure_response("User doesn't exists!")
    
    link = f"http://34.86.214.91/accept/{sender.id}/"

    message = f""""
    Dear {receiver.name}, 
            {sender.name} has requested to be your study partner. Click the link below to accept partnership
            link: {link}

    Best regards,
    We Study Team.
    """

    sent = send_email(sender, receiver, message)

    if not sent:
        return failure_response("Invalid inputs!")

    return success_response({"message" : "Message sent!",
                             "sent message" : message})


@app.route("/accept/<int:partner_id>/", methods=["POST"])
def accept_partner(partner_id):
    """
    Endpoint for accepting a partner
    """
    body = json.loads(request.data)
    user1_email = body.get("email")

    if user1_email is None:
        return failure_response("Invalid inputs!", 400)
    user1 = users_dao.get_user_by_email(user1_email)
    user2 = users_dao.get_user_by_id(partner_id)

    if user1 is None or user2 is None:
        return failure_response("User doesn't exists!", 400)
    if user1.email == user2.email or user1.accepted or user2.accepted:
        return failure_response("Invalid inputs", 400)
    
    user1.partner = user2.email
    user1.accepted = True
    user2.partner = user1.email
    user2.accepted = True
    db.session.commit()

    partners = [user1.serialize(), user2.serialize()]

    return success_response({
        "partners" : partners
    }, 201)


def send_email(sender, receiver, message):
    """
    Sends email 
    """
    msg = MIMEMultipart()
    msg['From'] = sender.email
    msg['To'] = receiver.email
    msg['Subject'] = "LET'S STUDY TOGETHER😊"
    body = message
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender.email, os.environ.get("PASSWORD"))

        server.sendmail(msg['From'], msg['To'], msg.as_string())

        server.quit()

        return True
    except:
         return False


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

