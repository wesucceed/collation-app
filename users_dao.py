"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import User
from db import db
import os
from geopy.distance import distance
import googlemaps
gmaps = googlemaps.Client(key = os.environ.get("GOOGLEMAPKEY"))


def get_user_by_email(email):
    """
    Returns a user object from the database given an email
    """
    return User.query.filter(User.email == email).first()


def get_user_by_session_token(session_token):
    """
    Returns a user object from the database given a session token
    """
    return User.query.filter(User.session_token == session_token).first()


def get_user_by_update_token(update_token):
    """
    Returns a user object from the database given an update token
    """
    return User.query.filter(User.update_token == update_token).first()

def get_user_by_id(id):
    """
    Returns user given an id
    """
    return User.query.filter(User.id == id).first()


def verify_credentials(email, password):
    """
    Returns true if the credentials match, otherwise returns false
    """
    optional_user = get_user_by_email(email)

    if optional_user is  None:
        return False, None
    
    return optional_user.verify_password(password), optional_user


def create_user(name, email, password, address, major):
    """
    Creates a User object in the database

    Returns if creation was successful, and the User object
    """
    optional_user = get_user_by_email(email)

    if optional_user is not None:
        return False, optional_user
    
    user = User(email = email, password = password, name = name, address = address, major = major)

    db.session.add(user)
    db.session.commit()

    return True, user


def renew_session(update_token):
    """
    Renews a user's session token
    
    Returns the User object
    """
    user = get_user_by_update_token(update_token)

    if user is None:
        return None
    
    user.renew_session()
    db.session.commit()
    return user

def path(user1, user2):
    """
    Returns the distance between two users in miles
    """
    location1 = (gmaps.geocode(user1.address)[0]['geometry']['location']['lat'],
                 gmaps.geocode(user1.address)[0]['geometry']['location']['lng'])
    
    location2 = (gmaps.geocode(user2.address)[0]['geometry']['location']['lat'],
                 gmaps.geocode(user2.address)[0]['geometry']['location']['lng'])
    
    dist = distance(location1, location2).miles

    return dist

def get_user_by_major(major):
    """
    Returns users from the database whose major is "major"
    """
    return User.query.filter(User.major == major, User.accepted == False).all()

def get_user_by_address(address):
    """
    Returns users from the database who address is "address"
    """
    return User.query.filter(User.address == address, User.accepted == False).all()

def get_closest_user(user):
    """
    Returns the closest user
    """
    users = User.query.filter(User.accepted == False).all()
    closest_user = None
    closest_dist = float('inf')
    for u in users:
        dist = path(u, user)
        if dist < closest_dist and u != user:
            closest_dist = dist
            closest_user = u
    
    return closest_user
