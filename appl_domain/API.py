from flask import (
    Blueprint, request, jsonify
)
from werkzeug.exceptions import abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta

# Get today's date
today = datetime.today().date()

# Blueprint to be registered with Flask application
bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/get_expired_users', methods=['GET'])
def get_expired_users():
    # Restrict to local traffic only
    if (request.remote_addr == '127.0.0.1') and (request.method == 'GET'):
        # Create empty list to hold users
        user_list = []
        # Get a handle on the database
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
                user_list.append({
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'email_address': user['email_address'],
                    'days_before_expiration': days_before_expiration
                })
        return jsonify(user_list)
    else:
        # Send 403 - Forbidden response
        abort(403)
