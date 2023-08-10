"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import Polling_Agent
from db import Polling_Station
from db import Polling_Station_Result
from db import Constituency
import db
from twilioapp import sendmessage
import secrets
import string
import os
from dotenv import load_dotenv
load_dotenv()


def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

#generate password function and send to admin for verification
def get_polling_agent_by_id(id, password):
    """
    Returns polling agent given an id
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.id == id).first()

    if polling_agent is None:
        return polling_agent

    return polling_agent

def get_polling_agent_by_name(name):
    """
    Returns polling agent given a name
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.name == name).first()

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent

def get_polling_agent_by_session_token(session_token):
    return Polling_Agent.query.filter(Polling_Agent.session_token == session_token)

def get_polling_agent_by_update_token(update_token):
    return Polling_Agent.query.filter(Polling_Agent.update_token == update_token)

def get_polling_agent(name, phone_number):
    return Polling_Agent.query.filter(Polling_Agent.name == name , Polling_Agent.phone_number == phone_number)

def renew_session(update_token):
    """
    Renews session
    """
    polling_agent = get_polling_agent_by_update_token(update_token)

    if not polling_agent:
        return None
    polling_agent.renew_session()
    return polling_agent


##### CREATE  ####

def create_polling_agent(name, phone_number, password, polling_station_id):    

    exists, polling_agent = get_polling_agent(name, phone_number)
    if exists:
        return False, polling_agent
    
    auto_password = generate_password()

    polling_agent = Polling_Agent(name = name, 
                                  phone_number = phone_number, 
                                  password = password, 
                                  polling_station_id = polling_station_id, 
                                  auto_password = auto_password)
    
    if not polling_agent:
        return False, polling_agent
    

    db.session.add(polling_agent)
    db.session.commit()

    return True, polling_agent
    

    

def create_polling_station_result(name, number, constituency, region, votes, rejected_ballots, valid_ballots, total_votes, pink_sheet, polling_agent_id, auto_password):
    """
    Creates a Polling Station Result 
    """
    #TODO: if not verified, verify with auto_password before submission
    #TODO: check if polling agent sending to right station
    verified, polling_agent = verify_auto_password(auto_password, polling_agent_id)

    if not verified:
        return False, polling_agent
    

    if not polling_agent.is_verified:
        polling_agent.is_verified = True
    
    polling_station = get_polling_station(name, number, constituency, region)

    if not polling_station:
        return False, polling_station
    
    polling_agent = polling_station.polling_agent

    if polling_agent.id != polling_agent_id:
        return False, polling_agent
    
    if polling_station.polling_station_result is not None and polling_agent.polling_station_result is not None:
        return False, polling_station.polling_station_result
    
    polling_station_result = Polling_Station_Result(
        total_votes_cast = total_votes,
        total_valid_ballots = valid_ballots,
        total_rejected_ballots = rejected_ballots,
        pink_sheet = pink_sheet,
        votes = votes,
        polling_station_id = polling_station.id,
        polling_agent_id = polling_agent.id,
    )

    if not polling_station_result:
        return False, polling_station_result

    db.session.add(polling_station_result)
    db.session.commit()

    return True, polling_station_result


def get_polling_station(name, number, constituency, region):
    """
    Returns a polling station
    """
    polling_station = Polling_Station.query.filter(
        Polling_Station.name == name,
        Polling_Station.number == number,
        Polling_Station.constituency == constituency,
        Polling_Station.region == region
    )

    if polling_station is None:
        return False, polling_station

    return True, polling_station


def get_polling_agent(name, phone_number):
    """
    Returns a polling agent
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.name == name, 
                                               Polling_Agent.phone_number == phone_number
                                               )

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent


def get_polling_station_result_by_polling_station_id(polling_station_id):
    """
    Returns polling station results by a polling station id
    """
    polling_station_result = Polling_Station_Result.query.filter(
        Polling_Station_Result.polling_station_id == polling_station_id
        )

    if polling_station_result is None:
        return False, polling_station_result

    return True, polling_station_result

# 4
def get_all_results():
    """
    Returs all the polling station results
    """
    results = Polling_Station_Result.query.all()
    return True, results


##### GET CONSTITUENCY #####
# 1
def get_result_by_constituency(name):
    """
    Returns a constituency result by name
    """
    results = Constituency.query.filter(Constituency.name == name).first()

    if results is None:
        return False, results

    return True, results

# 2
def get_all_results_by_constituency():
    """
    Returns all results by constituency
    """
    results = Constituency.query.all()
    return True, results


##### GET REGION #####
# 3
def get_result_by_region(name):
    """
    Returns a region result by name
    """
    results = Constituency.query.filter(Constituency.region == name)
    return True, results


##### VERIFICATION #####
def verify_sms_code(verification_code, polling_agent_id):
    user = get_polling_agent_by_id(id = polling_agent_id)

    if not user:
        return False, None
    
    if not user.verify_totp(verification_code):
        return False, None
    
    return True, user


def verify_auto_password(auto_password, polling_agent_id):
    """
    Verifies auto password
    """
    polling_agent = get_polling_agent_by_id(polling_agent_id)

    if polling_agent is  None:
        return False, polling_agent

    return polling_agent.verify_auto_password(auto_password), polling_agent


def verify_login_credentials(name, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    polling_agent = get_polling_agent_by_name(name)

    if polling_agent is  None:
        return False, polling_agent
    
    return polling_agent.verify_password(password), polling_agent