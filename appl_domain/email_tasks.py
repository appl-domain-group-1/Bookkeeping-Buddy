import smtplib
import ssl
from email.message import EmailMessage
from email.mime.text import MIMEText

from flask import url_for

from appl_domain.db import get_db

EMAIL_PASSWORD = 'gfiwyydznrfioixh'
SENDER = 'noreply.bookkeepingbuddy@gmail.com'
SITE_URL = 'http://eexley1.pythonanywhere.com'


def send_email(to, subject, message):
    # Create empty email object
    email = EmailMessage()
    # Set email info
    email['From'] = SENDER
    email['Subject'] = subject
    # Set the content of the email
    email.set_content(MIMEText(message, 'html'))
    # Set the email destination
    email['To'] = to

    # Create SSL context
    context = ssl.create_default_context()
    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(SENDER, EMAIL_PASSWORD)
        smtp.sendmail(SENDER, email["To"], email.as_string())

    # Reference:
    # https://towardsdatascience.com/how-to-easily-automate-emails-with-python-8b476045c151#bc59
    # User: noreply.bookkeepingbuddy@gmail.com   Pass: xEcN5GxFjCBqq29


def email_registration(username, first_name, last_name):
    # Get a handle on the database
    db = get_db()
    # Get a list of all the administrators
    admins = db.execute(
        "SELECT * FROM users WHERE role = ?", (2,)
    ).fetchall()

    # Email subject
    subject = 'Account Verification'

    # Craft the URL to be sent in the email
    endpoint = url_for('auth.approve_user', username=username)
    # Loop through each admin and send the email
    for admin in admins:
        # Content to be sent in the email
        message = f"Hello {admin['first_name']} {admin['last_name']},<br><br>{first_name} {last_name} has requested " \
                  f"for their account to be approved.<br><br><a href='{SITE_URL}{endpoint}'>Click here to activate " \
                  f"the account</a>.<br><br>If you wish to reject this request, simply ignore this email.<br><br>" \
                  f"Regards,<br><br>Your Bookkeeping Buddy"

        send_email(admin["email_address"], subject, message)


def send_approval(username):
    # Get a handle on the DB
    db = get_db()
    # Get user info
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    # Email subject
    subject = 'Account approved'

    # Craft endpoint to be linked in the email
    endpoint = url_for('auth.login')
    # Content to be sent in the email
    message = f"Hello {user['first_name']} {user['last_name']},<br><br>Your new account on Bookkeeping Buddy has " \
              f"been activated!<br><br><a href='{SITE_URL}{endpoint}'>Click here to log in.</a><br><br>Regards," \
              f"<br><br>Your Bookkeeping Buddy"

    send_email(user["email_address"], subject, message)


def email_journal_adjust(username, first_name, last_name, journal_date):
    # Get a handle on the database
    db = get_db()
    # Get a list of all the administrators
    manager = db.execute(
        "SELECT * FROM users WHERE role = ?", (1,)
    ).fetchall()

    # Email subject
    subject = 'Adjusted Journal Entry'

    # Craft the URL to be sent in the email
    endpoint = url_for('journaling.journal', username=username)
    # Loop through each admin and send the email
    for manager in manager:
        # Content to be sent in the email
        message = f"Hello {manager['first_name']} {manager['last_name']},<br><br>{first_name} {last_name} has " \
                  f"adjusted journal entry at {journal_date} and requests approval.<br><br>" \
                  f"<a href='{SITE_URL}{endpoint}'>Click here to log in.</a><br><br>" \
                  f"Regards,<br><br>Your Bookkeeping Buddy"

        send_email(manager["email_address"], subject, message)
