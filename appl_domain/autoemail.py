import smtplib
import ssl

from flask import url_for, Blueprint
from appl_domain.db import get_db

from email.message import EmailMessage
from email.mime.text import MIMEText

bp = Blueprint('email', __name__, url_prefix='/')


def email_registration(username, first_name, last_name):
    db = get_db()
    admins = db.execute(
        "SELECT * FROM users WHERE role = ?", (2,)
    ).fetchall()

    email_password = 'gfiwyydznrfioixh'
    email_sender = 'noreply.bookkeepingbuddy@gmail.com'

    subject = 'Account Verification'
    url = url_for('auth.edit_user', username=username)
    msg = MIMEText(f"""{first_name} {last_name} has requested for their account to be approved.\n 
        <a href="http://localhost:5000{url}">Click here to activate the account.</a>""", 'html')

    email = EmailMessage()
    email['From'] = email_sender
    email['Subject'] = subject
    email.set_content(msg)
    context = ssl.create_default_context()

    for admin in admins:
        email['To'] = admin["email_address"]
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email["To"], email.as_string())

    # https://towardsdatascience.com/how-to-easily-automate-emails-with-python-8b476045c151#bc59
    # User: noreply.bookkeepingbuddy@gmail.com   Pass: xEcN5GxFjCBqq29

    # @bp.route('/email/<username>')
    # def email(username):
    #    db = get_db()
    #    # Get matching user from the DB
    #    user = db.execute(
    #        "SELECT * FROM users WHERE username = ?", (username,)
    #    ).fetchone()

    #    admins = db.execute(
    #        "SELECT * FROM users WHERE role = ?", (2,)
    #    ).fetchall()

    #    for admin in admins:
    #        email_registration(user, admin["email_address"])
        # Generate email body
        # email_body = flask.render_template('email.html', user=user)
        # Send email
    #    return flask.render_template('auth/email.html', user=user)
