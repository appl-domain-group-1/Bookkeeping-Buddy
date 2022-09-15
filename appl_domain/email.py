import smtplib
import ssl
from flask import url_for
from appl_domain.db import get_db
from email.message import EmailMessage
from email.mime.text import MIMEText

EMAIL_PASSWORD = 'gfiwyydznrfioixh'
SENDER = 'noreply.bookkeepingbuddy@gmail.com'
SITE_URL = 'http://localhost:5000'  # TODO: Change this when we go live
def email_registration(username, first_name, last_name):
    # Get a handle on the database
    db = get_db()
    # Get a list of all the administrators
    admins = db.execute(
        "SELECT * FROM users WHERE role = ?", (2,)
    ).fetchall()

    # Craft the URL to be sent in the email
    endpoint = url_for('auth.approve_user', username=username)

    # Create empty email object
    email = EmailMessage()
    # Set email info
    email['From'] = SENDER
    email['Subject'] = 'Account verification'
    # Create SSL context
    context = ssl.create_default_context()

    # Loop through each admin and send the email
    for admin in admins:
        # Content to be sent in the email
        msg = MIMEText(
            f"Hello {admin['first_name']} {admin['last_name']},<br><br>{first_name} {last_name} has requested for "
            f"their account to be approved.<br><br><a href='{SITE_URL}{endpoint}'>Click here to activate the "
            f"account</a>.<br><br>If you wish to reject this request, simply ignore this email.<br><br>Regards,<br><br>"
            f"Your Bookkeeping Buddy", 'html')
        # Set the content of the email
        email.set_content(msg)
        # Set the email destination
        email['To'] = admin["email_address"]
        # Send it
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER, EMAIL_PASSWORD)
            smtp.sendmail(SENDER, email["To"], email.as_string())

    # https://towardsdatascience.com/how-to-easily-automate-emails-with-python-8b476045c151#bc59
    # User: noreply.bookkeepingbuddy@gmail.com   Pass: xEcN5GxFjCBqq29


def send_approval(username):
    # Get a handle on the DB
    db = get_db()
    # Get user info
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    # Craft endpoint
    endpoint = url_for('auth.login')

    # Create empty email object
    email = EmailMessage()
    # Set email info
    email['From'] = SENDER
    email['Subject'] = 'Account approved'
    # Create SSL context
    context = ssl.create_default_context()
    # Content to be sent in the email
    msg = MIMEText(
        f"Hello {user['first_name']} {user['last_name']},<br><br>Your new account on Bookkeeping Buddy has been "
        f"activated!<br><br><a href='{SITE_URL}{endpoint}'>Click here to log in.</a><br><br>Regards,<br><br>Your "
        f"Bookkeeping Buddy", 'html')
    email.set_content(msg)
    email['To'] = user["email_address"]
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(SENDER, EMAIL_PASSWORD)
        smtp.sendmail(SENDER, email["To"], email.as_string())
