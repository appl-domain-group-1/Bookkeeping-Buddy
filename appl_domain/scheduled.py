"""
This file contains the different scheduled tasks that need to be run independent of the Flask server
"""
import json
from datetime import date, datetime, timedelta
import requests




def send_expired_emails():
    """
    Sends emails to all users with expired passwords
    """
    # Empty list for users to email
    user_list = []
    # Query the API on the flask server
    users = requests.get("localhost:5000/get_expired_users").content
    users = json.loads(users)
    if users:
        # Email the users
        pass  # TODO: email users
    else:
        return


if __name__ == '__main__':
    send_expired_emails()
