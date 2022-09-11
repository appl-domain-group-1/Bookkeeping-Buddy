import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from appl_domain.db import get_db
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    """
    Called on a view to make it force the user to log in first. Checks if the current session of the app has a valid
    user. If not, sends them to the login page.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """
    Allow a user to register for a new account
    """
    if request.method == 'POST':
        # Get today's date
        today = datetime.now()

        # Get elements from form
        password = request.form['password']
        email_address = request.form['email_address']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        address = request.form['address']
        DOB = request.form['DOB']
        first_pet = request.form['first_pet']
        city_born = request.form['city_born']
        year_graduated_hs = request.form['year_graduated_hs']

        # Generate username: First initial, last name, account created MM, account created YY
        username = f"{first_name[0]}{last_name}{today.month:02d}{str(today.year)[2:]}"

        # Format today's date for the database (YYYY-MM-DD)
        today = f"{today.year}-{today.month:02d}-{today.day:02d}"

        db = get_db()
        error = None

        # If password is blank or does not meet requirements, return an error
        if not password:
            error = 'Password is required'
        if (len(password) < 8) or \
                not (password[0].isalpha()) or \
                not (any(character.isdigit() for character in password)) or \
                not (any(character not in "!@#$%^&*") for character in password):
            error = 'Password must contain at least 8 characters, start with a letter, contain a number, and contain ' \
                    'a special character from this list: !@#$%^&*'

        # Other field validation
        if not (
                email_address or first_name or last_name or address or DOB or first_pet or city_born or year_graduated_hs):
            error = 'Please fill out all information'  # TODO: Perform other field validation

        # If we got no error, we're good to proceed
        if error is None:
            try:
                # Insert a new row into the DB with the new values
                """
                Explanation of values, datatypes, and ranges:
                
                    - username [str]: Generated by system. First initial, last name, account created MM, account created YY
                    - email_address [str]: Input by user
                    - first_name [str]: Input by user
                    - last_name [str]: Input by user
                    - active [int]: 0 for inactive account, 1 for active account. Defaults to 0 for new accounts
                    - role [int]: 0 for user, 1 for manager, 2 for admin. Defaults to 0 until changed by admin
                    - password [str]: Hashed representation of user input. Never stored in plain text.
                    - address [str]: Input by user
                    - DOB [str]: Input by user. Should be in YYYY-MM-DD format
                    - old_passwords [bytes]: List of old passwords used by this user. SQLite cannot handle a Python list
                        datatype, so this must be converted to bytes.
                    - password_refresh_date [str]: Date when password was last updated (YYYY-MM-DD). Set to the date 
                        account was created, then is updated each time a user updates their password
                    - creation_date [str]: Date when account was created (YYYY-MM-DD)
                    - first_pet [str]: Name of first pet. Security question #1
                    - city_born [str]: City where user was born. Security question #2
                    - year_graduated_hs [str]: Year user graduated highschool. Security question #3
                """
                db.execute(
                    "INSERT INTO users (username, email_address, first_name, last_name, active, role, password, "
                    "address, DOB, old_passwords, password_refresh_date, creation_date, first_pet, city_born, "
                    "year_graduated_hs) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, email_address, first_name, last_name, 0, 0, generate_password_hash(password), address,
                     DOB, bytes([]), today, today, first_pet, city_born, year_graduated_hs)
                )
                # Write the change to the database
                db.commit()
            # Catch cases where a username already exists
            except (db.InternalError, db.IntegrityError):  # TODO: Probably won't need this error since usernames are not user-supplied.
                error = f"User with username {username} already exists."
            else:
                # TODO: Should show the new user a page saying their account is awaiting approval from an admin
                if g.user and g.user['role'] == 2:
                    return redirect(url_for("auth.manage_users"))
                else:
                    return redirect(url_for("auth.login"))
        # Display any errors we encountered on the page
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    View to allow a user to log into the system
    """
    if request.method == 'POST':
        # Get username from the form
        username = request.form['username']
        # Get password from the form
        password = request.form['password']
        # Load the database
        db = get_db()
        # Placeholder for errors
        error = None
        # Get the matching row from the database
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        # If we are given a blank username, throw an error
        if user is None:
            error = "Incorrect username"
        # If the password hash in the form doesn't match what's in the database, throw an error
        elif not check_password_hash(user['password'], password):
            error = "Incorrect password"
        # If the account is inactive, throw an error
        elif not user['active']:
            error = "Account not activated. Contact your administrator."

        # If we don't have any errors, we're good to proceed
        if error is None:
            # Session represents the cookie that is sent to the user's browser. Clear it first
            session.clear()
            # Add the logged-in user's ID to the cookie
            session['username'] = user['username']
            # Add the logged-in user's role to the cookie
            session['role'] = user['role']
            # Send the logged-in user back to the main screen of the application
            return redirect(url_for('mainpage'))

        # Display any errors we encountered on the page
        flash(error)

    return render_template('auth/login.html')


@bp.route('forgot_password', methods=('GET', 'POST'))
def forgot_password():
    """
    View to allow a user to reset forgotten password
    """
    if request.method == 'POST':
        # Get username from the form
        username = request.form['username']
        # Get email from the form
        email_address = request.form['email_address']
        # Get security questions from the form
        first_pet = request.form['first_pet']
        city_born = request.form['city_born']
        year_graduated_hs = request.form['year_graduated_hs']

        # Get a handle on the database
        db = get_db()
        # Get the row for this user
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        year = user['year_graduated_hs']
        print(f"Username: {username == user['username']}")
        print(f"email: { email_address == user['email_address']}")
        print(f"pet: {first_pet == user['first_pet']}")
        print(f"city: {city_born == user['city_born']}")
        print(f"Year: {year_graduated_hs == year}")

        # Check the credentials
        if user and (username == user['username']) and \
                (email_address == user['email_address']) and \
                (first_pet == user['first_pet']) and \
                (city_born == user['city_born']) and \
                (year_graduated_hs == str(user['year_graduated_hs'])):
            print("$$$$$$$$$ DATA CHECKS OUT $$$$$$$$$") #  TODO: What happens now?
        else:
            flash("Could not verify information.")
    return render_template('auth/forgot_password.html')


@bp.route('/manage_users', methods=('GET', 'POST'))
@login_required
def manage_users():
    """
    Allows administrators to manage users of the system
    """
    user_list = None
    if request.method == 'GET':
        # Get all users from the DB
        db = get_db()
        user_list = db.execute(
            "SELECT * FROM users"
        ).fetchall()
        # Display them on the page
    return render_template('auth/manage_users.html', users=user_list)


@bp.route('/delete_user/<username>', methods=('GET', 'POST'))
@login_required
def delete_user(username):
    """
    Allows administrators to delete users
    """
    error = None
    if request.method == 'GET':
        if g.user['role'] != 2:
            flash("Operation not permitted")
            return redirect(url_for('mainpage'))
        elif g.user['username'] == username:
            flash(f"Can't delete yourself!")
            return redirect(url_for('auth.manage_users'))
        else:
            # Get a handle on the database
            db = get_db()
            # Delete the row
            try:
                db.execute(
                    "DELETE FROM users WHERE username = ?", (username,)
                )
                # Commit the change
                db.commit()
            except (db.InternalError, db.IntegrityError):
                error = f"User with username {username} not found!"
            if error is None:
                flash(f"User {username} deleted!")
            return redirect(url_for('auth.manage_users'))



@bp.route('/edit_user/<username>', methods=('GET', 'POST'))
@login_required
def edit_user(username):
    """
    Allows administrators to edit info of a single user
    """
    # Get matching user from the DB
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if request.method == 'GET':
        # Display user info on the page
        return render_template('auth/edit_user.html', user=user)

    if request.method == 'POST':
        # Get the info from the form fields
        email = request.form['email_address']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        if request.form.get("active"):
            active = 1
        else:
            active = 0
        role = request.form['role']
        address = request.form['address']
        DOB = request.form['DOB']
        first_pet = request.form['first_pet']
        city_born = request.form['city_born']
        yr_graduated = request.form['year_graduated_hs']
        # Get a handle on the database
        db = get_db()
        try:
            # Update columns
            db.execute(
                "UPDATE users SET email_address = ?, first_name = ?, last_name = ?, active = ?, role = ?, address = ?, DOB = ?, "
                "first_pet = ?, city_born = ?, year_graduated_hs = ? WHERE username = ?", (email, first_name, last_name,
                                                                                           active, role, address, DOB,
                                                                                           first_pet, city_born,
                                                                                           yr_graduated, username)
            )
            # Write changes
            db.commit()
            flash("Record updated!")
        except Exception:
            print(f"Error: {Exception.__traceback__.tb_next}")
        # Get fresh info from the DB
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return render_template('auth/edit_user.html', user=user)


# This decorator registers a function that runs before the view function regardless of what URL is requested
@bp.before_app_request
def load_logged_in_user():
    """
    Checks if the username is in the session (the user's cookie), gets the info from the DB, and stores it in g.user.
    This persists through the length of the request.
    """
    # Get the username from the cookie
    username = session.get('username')

    # If the username is blank, clear the current user from the current session of the app
    if username is None:
        g.user = None
    # If the cookie contains a username, find it in the database
    else:
        g.user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


@bp.route('/logout')
def logout():
    """
    View called when a user logs out of the system
    """
    # Clear the user's cookie
    session.clear()
    # Send them back to the main page (but now logged out)
    return redirect(url_for('mainpage'))
