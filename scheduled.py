"""
This file contains the different scheduled tasks that need to be run independent of the Flask server

For PythonAnywhere, this file will need to be added to the nightly cron jobs
"""
import json
import pickle

import requests
from appl_domain.email_tasks import send_email, SITE_URL

# Uncomment based on where this is running
# HOST = "http://eexley1.pythonanywhere.com"
HOST = "http://localhost:5000"


def get_credentials():
    """
    Logs into the system to make sure the cookie is fresh and writes the credentials to a file
    """
    username = "DDELETE0922"
    password = "Test123456!!!!"
    login = requests.post(f"{HOST}/auth/login", data={'username': username, 'password': password}, allow_redirects=False)
    with open('api_cookie', 'wb') as file:
        pickle.dump(login.cookies, file)


def load_credentials():
    with open('api_cookie', 'rb') as file:
        return pickle.load(file)


def setup():
    get_credentials()
    return load_credentials()


def send_expiration_emails(cookie):
    """
    Sends emails to all users with expired passwords
    """
    try:
        # Query the API on the flask server
        users = requests.get(f"{HOST}/api/expiring_users", cookies=cookie).content
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


def send_expired_passwords_report(cookie):
    """
    Sends an email to administrators letting them know which user accounts have expired passwords
    """
    try:
        # Query the API endpoints on the flask server
        users = requests.get(f"{HOST}/api/expired_passwords", cookies=cookie).content
        users = json.loads(users)
        admins = requests.get(f"{HOST}/api/admin_list", cookies=cookie).content
        admins = json.loads(admins)
    except Exception as err:
        print(err)
        return
    subject = "Expired Passwords"
    # If there are users with expired passwords....
    if len(users):
        # Start with the top row of the table
        expired_list = "<table><tr><th>Name</th><th>Username</th><th>Email Address</th><th>Expired on</th></tr>"
        # Add each user to the table
        for user in users:
            expired_list = expired_list + f"<tr>" \
                                          f"<td>{user['first_name']} {user['last_name']}</td>" \
                                          f"<td>{user['username']}</td>" \
                                          f"<td>{user['email_address']}</td>" \
                                          f"<td>{user['expired_on']}</td>" \
                                          f"</tr>"
        # Close the <table> tag
        expired_list = expired_list + "</table>"
        # Send each admin an email with a list of the users with expired passwords
        for admin in admins:
            message = f"Hello {admin['first_name']} {admin['last_name']},<br><br>Here is a list of all users with " \
                      f"expired passwords:<br><br>{expired_list}<br><br>Regards,<br><br>Your Bookkeeping Buddy"
            send_email(admin['email_address'], subject, message)
    # If there are no users with expired passwords...
    else:
        # Send each admin an email telling them everything is ok
        for admin in admins:
            message = f"Hello {admin['first_name']} {admin['last_name']},<br><br>There are currently no expired " \
                      f"accounts in the system.<br><br>Regards,<br><br>Your Bookkeeping Buddy"
            send_email(admin['email_address'], subject, message)


if __name__ == '__main__':
    cookies = setup()
    send_expiration_emails(cookies)
    send_expired_passwords_report(cookies)
