"""
This file contains the different scheduled tasks that need to be run independent of the Flask server
"""
import json
import requests
from appl_domain.email_tasks import send_email, SITE_URL


def send_expired_emails():
    """
    Sends emails to all users with expired passwords
    """
    try:
        # Query the API on the flask server
        users = requests.get("http://127.0.0.1:5000/api/get_expired_users").content
        users = json.loads(users)
    except Exception as err:
        print(err)
        return
    subject = "Account Expiration Notice"
    if len(users):
        for user in users:
            message = f"Hello {user['first_name']} {user['last_name']},<br><br>Your password on Bookkeeping Buddy is " \
                      f"set to expire in {user['days_before_expiration']} days. Please <a href='{SITE_URL}'>log into \
                      your account</a> and reset your password.<br><br>Regards,<br><br>Your Bookkeeping Buddy"
            send_email(user['email_address'], subject, message)
    else:
        return


if __name__ == '__main__':
    send_expired_emails()
