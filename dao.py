"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import Polling_Agent
from db import Polling_Station
from db import Polling_Station_Result
from db import db
from twilioapp import sendmessage

import os
from dotenv import load_dotenv
load_dotenv()
import pyotp
import qrcode
from PIL import Image, ImageDraw, ImageFont



def gen_totp_key():
    return pyotp.random_base32()

def gen_totp_uri(key, polling_agent_name):
    return pyotp.totp.TOTP(key, interval= 15).provisioning_uri(name=polling_agent_name, issuer_name="Collation App")

def gen_qrcode(data, content, name, id):
    qr = qrcode.QRCode(
        version=1,  
        error_correction=qrcode.constants.ERROR_CORRECT_L,  
        box_size=10,  
        border=4,    
    )


    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    title = f"{content}-{name}-{id}"
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(img)
    text_width = text_height = font.getlength(title)
    x = (img.size[0] - text_width) // 2
    y = img.size[1]//25  
    draw.text((x, y), title, font=font, fill="black")

    img.save(f"{title}.png")



def get_polling_agent_by_id(id):
    """
    Returns polling agent given an id
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.id == id).first()

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent

def get_polling_agent_by_name(name):
    """
    Returns polling agent given a name
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.name == name).first()

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent

def get_polling_agent_by_session_token(session_token):
    return Polling_Agent.query.filter(Polling_Agent.session_token == session_token).first()

def get_polling_agent(name, phone_number):
    return Polling_Agent.query.filter(Polling_Agent.name == name , Polling_Agent.phone_number == phone_number)

def renew_session(polling_agent):
    """
    Renews session
    """

    polling_agent.renew_session()
    db.session.commit()

    return polling_agent


##### CREATE  ####

def create_polling_agent(name, phone_number, password, polling_station_id):    

    exists, polling_agent = get_polling_agent(name, phone_number)
    if exists:
        return False, polling_agent
    
    totp_key = gen_totp_key()

    polling_agent = Polling_Agent(name = name, 
                                  phone_number = phone_number, 
                                  password = password, 
                                  polling_station_id = polling_station_id, 
                                  totp_key = totp_key)
    
    if not polling_agent:
        return False, polling_agent
    
    gen_qrcode(gen_totp_uri(totp_key, polling_agent.name), "uri", polling_agent.name, polling_station_id)
    gen_qrcode(totp_key, "key", polling_agent.name, polling_station_id)

    db.session.add(polling_agent)
    db.session.commit()




    return True, polling_agent
    

    
# TODO: work on this
def create_polling_station_result(data,
                                  total_votes_cast, 
                                  total_rejected_ballots,
                                  total_valid_ballots, 
                                  pink_sheet, 
                                  polling_agent_id, 
                                  polling_station_id,
                                  auto_password):
    """
    Creates a Polling Station Result 
    """
    #TODO: if not verified, verify with totp_key before submission
    #TODO: check if polling agent sending to right station
    verified, polling_agent = verify_totp_key(totp_key, polling_agent_id)

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
    ).first()

    if polling_station is None:
        return False, polling_station

    return True, polling_station


def get_polling_agent(name, phone_number):
    """
    Returns a polling agent
    """
    polling_agent = Polling_Agent.query.filter(Polling_Agent.name == name, 
                                               Polling_Agent.phone_number == phone_number
                                               ).first()

    if polling_agent is None:
        return False, polling_agent

    return True, polling_agent


def get_polling_station_result_by_polling_station_id(polling_station_id):
    """
    Returns polling station results by a polling station id
    """
    polling_station_result = Polling_Station_Result.query.filter(
        Polling_Station_Result.polling_station_id == polling_station_id
        ).first()

    if polling_station_result is None:
        return False, polling_station_result

    return True, polling_station_result





##### GET CONSTITUENCY #####
# 1
def get_result_by_constituency(name):
    """
    Returns constituency results by name
    """
    
    polling_stations = Polling_Station.query.filter(Polling_Station.constituency == name).all()

    if polling_stations is None:
        return False, polling_stations
    
    acc = []

    for polling_station in polling_stations:
        acc.append(polling_station.serialize())

    return True, acc

# 2
def get_all_results():
    """
    Returns all results 
    """
    polling_stations = Polling_Station.query.all()

    if polling_stations is None:
        return False, polling_stations
    
    acc = []

    for polling_station in polling_stations:
        acc.append(polling_station.serialize())

    return True, acc


##### GET REGION #####
# 3
def get_result_by_region(name):
    """
    Returns results by region
    """
    polling_stations = Polling_Station.query.filter(Polling_Station.region == name).all()

    if polling_stations is None:
        return False, polling_stations
    
    acc = []

    for polling_station in polling_stations:
        acc.append(polling_station.serialize())

    return True, acc


##### VERIFICATION #####
def verify_sms_code(verification_code, polling_agent_id):
    user = get_polling_agent_by_id(id = polling_agent_id)

    if not user:
        return False, None
    
    if not user.verify_totp(verification_code):
        return False, None
    
    return True, user


def verify_totp_key(totp_key, totp_value, polling_agent_id):
    """
    Verifies totp
    """
    success, polling_agent = get_polling_agent_by_id(polling_agent_id)

    if not success:
        return False, polling_agent
    return polling_agent.verify_totp_key(totp_key, totp_value), polling_agent


def verify_login_credentials(name, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    success, polling_agent = get_polling_agent_by_name(name)
    if not success:
        return False, polling_agent
    
    return polling_agent.verify_password(password), polling_agent