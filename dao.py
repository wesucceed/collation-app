"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import Polling_Agent
from db import Polling_Station
from db import Polling_Station_Result
from db import Constituency
import os
import db




# def get_user_by_session_token(session_token):
#     """
#     Returns a user object from the database given a session token
#     """
#     return User.query.filter(User.session_token == session_token).first()


# def get_user_by_update_token(update_token):
#     """
#     Returns a user object from the database given an update token
#     """
#     return User.query.filter(User.update_token == update_token).first()

def get_polling_agent_by_id(id):
    """
    Returns polling agent given an id
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.id == id).first()
    print("Uri: ", polling_agent.totp_uri)

    if polling_agent.totp_uri is None:
        polling_agent.renew_session()
        print("renewed: ", polling_agent.totp_uri)

    return polling_agent


# def verify_login_credentials(email, password):
#     """
#     Returns true if the credentials match, otherwise returns false
#     """
#     optional_user = get_user_by_email(email)

#     if optional_user is  None:
#         return False, None
    
#     return optional_user.verify_password(password), optional_user

# def verify_submit_credentials(polling_agent_name, polling_agent_phone_number):
#     """
#     Returns true if the credentials match, otherwise returns false
#     """
#     polling_agent = get_polling_agent(polling_agent_name, polling_agent_phone_number)

#     if not polling_agent:
#         return False, None
    
    # verify password
    # send a one time verification token to phone number
    
    # return polling_agent.verify_password(password), optional_user


# def renew_session(update_token):
#     """
#     Renews a user's session token
    
#     Returns the User object
#     """
#     user = get_user_by_update_token(update_token)

#     if user is None:
#         return None
    
#     user.renew_session()
#     db.session.commit()
#     return user





##### CREATE POLLING STATION RESULTS ####
def create_polling_station_result(name, number, constituency, region, votes, rejected_ballots, valid_ballots, total_votes, pink_sheet, polling_agent_name, polling_agent_number):
    """
    Creates a Polling Station Result 
    """
    polling_agent = get_polling_agent(name = polling_agent_name, phone_number = polling_agent_number)

    if not polling_agent:
        return False, polling_agent
    
    polling_station = get_polling_station(name, number, constituency, region)

    if not polling_station:
        return False, polling_station
    
    polling_station_result = get_polling_station_result_by_polling_station(polling_station.id)

    if polling_station_result is not None:
        return False, polling_station_result
    
    
    polling_station_result = Polling_Station_Result(
        total_votes_cast = total_votes,
        total_valid_ballots = valid_ballots,
        total_rejected_ballots = rejected_ballots,
        pink_sheet = pink_sheet,
        votes = votes,
        polling_station_id = polling_station.id,
        polling_agent_id = polling_agent.id,
    )

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

def get_polling_agent_by_name(name):
    """
    Returns a polling agent by name
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.name == name
                                               )

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent


def get_polling_stations_result_by_id(id):
    """
    Returns polling station results by id
    """
    polling_station_result = Polling_Station_Result.query.filter(
        Polling_Station_Result.id == id
        )

    if polling_station_result is None:
        return False, polling_station_result

    return True, polling_station_result


def get_polling_station_result_by_polling_station(polling_station_id):
    """
    Returns polling station results by a polling station id
    """
    polling_station_result = Polling_Station_Result.query.filter(
        Polling_Station_Result.polling_station_id == polling_station_id
        )

    if polling_station_result is None:
        return False, polling_station_result

    return True, polling_station_result


def get_all_results():
    """
    Returs all the polling station results
    """
    results = Polling_Station_Result.query.all()
    acc = []
    for result in results:
        acc.append(result.serizalize())
    return True, acc


##### GET CONSTITUENCY #####
def get_result_by_constituency(name):
    """
    Returns a constituency result by name
    """
    
    results = Constituency.query.filter(Constituency.name == name).first()

    if results is None:
        return False, results

    return True, results.serialize()


def get_all_results_by_constituency():
    """
    Returns all results by constituency
    """
    results = Constituency.query.all()
    acc = []
    for result in results:
        acc.append(result.serialize())

    return True, acc

    



##### GET REGION #####
def get_result_by_region(name):
    """
    Returns a region result by name
    """
    results = Constituency.query.filter(Constituency.region == name)
    acc = []
    for result in results:
        acc.append(result.serialize())

    return True, acc
