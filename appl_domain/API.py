from flask import (
    Blueprint, request, jsonify, g
)
from werkzeug.exceptions import abort
from appl_domain.db import get_db
from datetime import date, datetime, timedelta
from appl_domain.auth import login_required

# Get today's date
today = datetime.today().date()

# Blueprint to be registered with Flask application
bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/expiring_users', methods=['GET'])
@login_required
def expiring_users():
    # Restrict only to accounts with role 3 (API access)
    if request.method == 'GET' and g.user['role'] == 3:
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


@bp.route('/expired_passwords', methods=['GET'])
@login_required
def expired_passwords():
    # Restrict only to accounts with role 3 (API access)
    if request.method == 'GET' and g.user['role'] == 3:
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
            # If the user is in the time window, add them to the list of users to be emailed
            if password_expires <= today:
                user_list.append({
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'username': user['username'],
                    'email_address': user['email_address'],
                    'expired_on': password_expires.strftime("%b %d, %Y")
                })
        return jsonify(user_list)
    else:
        # Send 403 - Forbidden response
        abort(403)


@bp.route('/admin_list', methods=['GET'])
def admin_list():
    # Restrict only to accounts with role 3 (API access)
    if request.method == 'GET' and g.user['role'] == 3:
        # Create empty list to hold admins
        list_of_admins = []
        # Get a handle on the database
        db = get_db()
        # Get list of admins from the database
        admins = db.execute(
            "SELECT * FROM users WHERE role = 2"
        ).fetchall()

        # Loop over each row and get the necessary info
        for admin in admins:
            list_of_admins.append({
                'first_name': admin['first_name'],
                'last_name': admin['last_name'],
                'email_address': admin['email_address']
            })
        return jsonify(list_of_admins)
    else:
        # Send 403 - Forbidden
        abort(403)
