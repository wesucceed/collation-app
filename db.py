import datetime
import hashlib
import os
import pyotp



import bcrypt
from flask_sqlalchemy import SQLAlchemy

from pandas import read_excel
db = SQLAlchemy()



class Polling_Agent(db.Model):
    """
    Polling Agent Model
    """
    __tablename__ = "polling_agents"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Polling Agent information
    name = db.Column(db.String, nullable = False)
    phone_number = db.Column(db.String, nullable = False, unique = True)
    password_digest = db.Column(db.String, nullable= False, unique = True)
    totp_key_digest = db.Column(db.String, nullable= False, unique = True)

    is_verified = db.Column(db.Boolean, default = False, nullable =  False)  #TODO: HOW TO VERIFY


    # Session information
    session_token = db.Column(db.String, nullable=False, unique=True)
    session_expiration = db.Column(db.DateTime, nullable=False)
    update_token = db.Column(db.String, nullable=False, unique=True)


    # Polling station result
    polling_station_result = db.relationship("Polling_Station_Result")  #TODO: cascade to be restrict
    polling_station_id = db.Column(db.Integer, db.ForeignKey("polling_stations.id"), nullable = False, unique = True)


    def __init__(self, **kwargs):
        """
        Initializes a polling agent object
        """
        self.name = kwargs.get("name")
        self.phone_number = kwargs.get("phone_number")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.polling_station_id = kwargs.get("polling_station_id")
        self.totp_key_digest = bcrypt.hashpw(kwargs.get("totp_key").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_session()


    def verify_polling_agent(self, name, phone_number):
        return self.name == name and self.phone_number == phone_number


    def serialize(self):
        """
        Returns a serialized polling agent
        """
        res = {
            "id" : self.id,
            "name" : self.name,
            "polling_station_id" : self.polling_station_id,
            "polling_station_results" : [result.serialize() for result in self.polling_station_result] #TODO: serializing 1:1 well?
        }
        return res

    def _urlsafe_base_64(self):
        """
        Randomly generates hashed tokens (used for session/update tokens)
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()
    
    def renew_session(self):
        """
        Renews session
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(minutes=15)
        self.update_token = self._urlsafe_base_64()

    def verify_password(self, password):
        """
        Verifies the password of a polling agent
        """
        return bcrypt.checkpw(password.encode("utf8"), self.password_digest)

    
    def verify_totp_key(self, totp_key, totp_value):
        """
        Verifies the auto password of a polling agent
        """
        if not bcrypt.checkpw(totp_key.encode("utf8"), self.totp_key_digest):
            return False
        return pyotp.TOTP(totp_key, interval= 15).verify(totp_value)
    
    def verify_session_token(self, session_token):
        """
        Verifies the session token of a user
        """

        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration
        
def load_polling_stations():
    """
    Loads polling stations into polling stations model from stations.xlsx

    stations.xlsx must contain name, number, constituency and region columns
    """

    polling_stations_df = read_excel('stations.xlsx')

    # Specify the table name and the SQLAlchemy engine
    engine = db.get_engine()

    # Insert the data into the database table

    polling_stations_df.to_sql("polling_stations", con = engine, if_exists = 'replace', index = False, chunksize = 1000) 
    db.session.commit()
    return True

class Polling_Station(db.Model):
    """
    Polling Station Model
    """
    __tablename__ = "polling_stations"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Polling station results
    polling_station_results = db.relationship("Polling_Station_Result") #TODO: cascade to be restrict

    # Assigned polling agent
    polling_agent = db.relationship("Polling_Agent")  #TODO: unique is not allowed. was removed

    # Polling Station information
    name = db.Column(db.String, nullable = False)
    number = db.Column(db.String, nullable = False, unique = True)
    region = db.Column(db.String, nullable = False)
    constituency = db.Column(db.String, nullable = False)
    # composite id between region and constituency



    def __init__(self, **kwargs):
        """
        Initializes a polling station object
        """
        self.name = kwargs.get("name") 
        self.number = kwargs.get("number") 
        self.constituency = kwargs.get("constituency")
        self.region = kwargs.get("region")

         
    def serialize(self):
        """
        Returns a serialized polling station
        """
        res = {
            "polling_station_name" : self.name,
            "polling_station_number" : self.number,
            "constituency_name" : self.constituency,
            "region_name" : self.region,
            "polling_station_result" : [result.serialize() for result in self.polling_station_results],
            "polling_agent" : [polling_agent.serialize() for polling_agent in self.polling_agent]
        }
        return res
    

class Polling_Station_Result(db.Model):
    """
    Polling Station Result Model
    """
    __tablename__ = "polling_station_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)

    # Candidates with votes

    cand1 = db.Column(db.Integer, nullable = False)
    cand2 = db.Column(db.Integer, nullable = False)
    cand3 = db.Column(db.Integer, nullable = False) #TODO: candidate table with party of candidate

    # measure of central tendies
    total_valid_ballots = db.Column(db.Integer, nullable = False)
    total_rejected_ballots = db.Column(db.Integer, nullable = False)
    total_votes_cast = db.Column(db.Integer, nullable = False)

    # pink_sheet
    pink_sheet = db.Column(db.String, nullable = False, unique = True)

    # Polling agent posted
    polling_agent_id = db.Column(db.Integer, db.ForeignKey("polling_agents.id"), nullable = False, unique = True)

    # polling station
    polling_station_id = db.Column(db.Integer, db.ForeignKey("polling_stations.id"), nullable = False, unique = True)


    def __init__(self, **kwargs):
        """
        Initializes a polling station result
        """
        self.cand1 = kwargs.get("votes").get("cand1")
        self.cand2 = kwargs.get("votes").get("cand2") 
        self.cand3 = kwargs.get("votes").get("cand3")

        self.total_rejected_ballots = kwargs.get("total_rejected_ballots")
        self.total_valid_ballots = kwargs.get("total_valid_ballots")
        self.total_votes_cast = kwargs.get("total_votes_cast")

        self.pink_sheet = kwargs.get("pink_sheet")

        self.polling_agent_id = kwargs.get("polling_agent_id")
        self.polling_station_id = kwargs.get("polling_station_id")


    def serialize(self):
        """
        Returns a serialized polling station result
        """
        res = {
            "data" : {
                "cand1" : self.cand1,
                "cand2" : self.cand2,
                "cand3" : self.cand3}
                ,
            "total_rejected_ballots" : self.total_rejected_ballots,
            "total_valid_ballots" : self.total_valid_ballots,
            "total_votes_cast" : self.total_votes_cast,
            "pink_sheet" : self.pink_sheet,
            "polling_agent_id" : self.polling_agent_id,
            "polling_station_id" : self.polling_station_id
        }
        return res
    

