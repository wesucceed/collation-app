import os
from twilio.rest import Client
def sendmessage(dest, token):
    """
    Send sms
    """
    # Download the helper library from https://www.twilio.com/docs/python/install



    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    message = client.messages.create(
                                from_='+15557122661',
                                body='Hi there',
                                to='+15558675310'
                            )

    print(message.sid)
