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

# def get_user_by_id(id):
#     """
#     Returns user given an id
#     """
#     return User.query.filter(User.id == id).first()


def verify_login_credentials(email, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    optional_user = get_user_by_email(email)

    if optional_user is  None:
        return False, None
    
    return optional_user.verify_password(password), optional_user

def verify_submit_credentials(polling_agent_name, polling_agent_phone_number):
    """
    Returns true if the credentials match, otherwise returns false
    """
    polling_agent = get_polling_agent(polling_agent_name, polling_agent_phone_number)

    if not polling_agent:
        return False, None
    
    # verify password
    # send a one time verification token to phone number
    
    return polling_agent.verify_password(password), optional_user


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


def create_polling_station(name, number, constituency, region):
    """
    Creates a Polling Station

    Returns false, if polling station already exists, otherwise true
    """
    polling_station = get_polling_station(name, number, constituency, region)

    if polling_station is not None:
        return False, polling_station
    
    polling_station = Polling_Station(name = name, number = number, constituency = constituency, region = region)

    db.session.add(polling_station)
    db.session.commit()

    return True, polling_station




def create_polling_station_result(name, number, constituency, region, votes, rejected_ballots, valid_ballots, total_votes, pink_sheet):
    """
    Creates a Polling Station Result 

    Returns false, if polling station result already exists, otherwise true
    """
    polling_station = get_polling_station(name, number, constituency, region)

    if not polling_station:
        return True, polling_station
    
    polling_station_result = get_polling_station_result_by_polling_station(polling_station.id)

    if polling_station_result is not None:
        return False, polling_station_result
    
    polling_station_result = Polling_Station_Result(
        total_votes_cast = total_votes,
        total_valid_ballots = valid_ballots,
        total_rejected_ballots = rejected_ballots,
        pink_sheet = pink_sheet
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

# function to load csv or excel into data base
# modification function


##### CONSTITUENCY #####
def get_result_by_constituency(name):
    """
    Returns a constituency result by name
    """
    
    result = Constituency.query.filter(
        Constituency.name == name
        )

    if result is None:
        return False, result

    return True, result.serialize()


def get_all_results_by_constituency():
    """
    Returns all results by constituency
    """
    results = Constituency.query.all()

    acc = []
    
    for result in results:
        acc.append(result.serialize())

    return True, acc



##### REGION #####
def get_result_by_region(name):
    """
    Returns a region result by name
    """
    result = Constituency.query.filter(
        Constituency.region == name
    )

    if result is None:
        return False, result
    
    return True, result.serialize()
