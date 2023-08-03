import os
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

def sendmessage(dest, token):
    """
    Send sms given dest and token
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    message = client.messages.create(
                                from_= os.environ.get("TWILIO_PHONE_NUMBER"),
                                body= token,
                                to= dest
                            )

    print(f"Message SID: {message.sid}")

