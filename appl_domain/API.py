from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta

today = datetime.today().date()

bp = Blueprint('api', __name__)


@bp.route('/get_expired_users', methods='GET')
def get_expired_users():
    if request.method == 'GET':
        # Create empty list to hold users
        user_list = []
        # Get a handle on the datbase
        db = get_db()
        # Get the users from the database
        users = db.execute(
            "SELECT * FROM users"
        ).fetchall()  # TODO: write a better select statement

        # Loop over the users and find users with passwords about to expire
        for user in users:
            # Get the date the password was last refreshed
            password_refresh_date = date.fromisoformat(user['password_refresh_date'])
            # Calculate the date when it will expire
            password_expires = password_refresh_date + timedelta(days=180)
            # Find out how many days it will be before the password expires
            days_before_expiration = (password_expires - today).days
            # If the user is in the time window, add them to the list of users to be emailed
            if 3 >= days_before_expiration >= 0:
                user_list.append([
                    user['first_name'],
                    user['last_name'],
                    user['email_address'],
                    days_before_expiration
                ])