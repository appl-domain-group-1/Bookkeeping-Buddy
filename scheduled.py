"""
This file contains the different scheduled tasks that need to be run independent of the Flask server

For PythonAnywhere, this file will need to be added to the nightly cron jobs
"""
import json
import requests
from appl_domain.email_tasks import send_email, SITE_URL


def send_expiration_emails():
    """
    Sends emails to all users with expired passwords
    """
    try:
        # Query the API on the flask server
        users = requests.get("http://127.0.0.1:5000/api/expiring_users").content
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


def send_expired_passwords_report():
    """
    Sends an email to administrators letting them know which user accounts have expired passwords
    """
    try:
        # Query the API endpoints on the flask server
        users = requests.get("http://127.0.0.1:5000/api/expired_passwords").content
        users = json.loads(users)
        admins = requests.get("http://127.0.0.1:5000/api/admin_list").content
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
    send_expiration_emails()
    send_expired_passwords_report()
