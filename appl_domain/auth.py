import functools
import re

from appl_domain.email_tasks import email_registration, send_approval
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash
from appl_domain.db import get_db
from datetime import date, datetime, timedelta
import json
from PIL import Image
from io import BytesIO

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
        today = datetime.today().date()

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
        username = f"{first_name[0]}{last_name}{today:%m}{today:%y}"

        db = get_db()
        error = None

        # Validate format of high school graduation year
        if not year_graduated_hs:
            error = 'Please enter the year you graduated high school'
        elif not (any(character.isdigit() for character in year_graduated_hs)):
            error = 'High school graduation year must be a number'
        elif (today.year - 18) <= int(year_graduated_hs) <= (today.year - 118):
            error = 'Invalid year of graduation'

        # Validate format of city user was born in
        if not city_born:
            error = 'Please enter the city you were born in'
        elif (len(city_born) > 32) or \
                not city_born.isalpha():
            error = 'Please enter a valid city name'

        # Validate format of name of user's first pet
        if not first_pet:
            error = 'Please enter the name of your first pet'
        elif (len(first_pet) > 16) or \
                not first_pet.isalpha():
            error = 'Please do not enter special characters in the pet name field'

        # Validate format of user's date of birth
        if not DOB:
            error = 'Date of birth is required'
        elif DOB:
            try:
                correct_date = bool(datetime.strptime(DOB, "%Y-%m-%d"))
            except ValueError:
                correct_date = False
            if not correct_date:
                error = 'Date of birth must be formatted as YYYY-MM-DD'

        # Validate format of user's address
        if not address:
            error = 'Please enter your address'
        elif (len(address) > 32) or \
                not (any(character.isalpha() for character in address)) or \
                not (any(character.isdigit() for character in address)) or \
                (any(character in "!@#$%^&*()-+?_=,<>/" for character in address)):
            error = 'Please enter a valid street address'

        # Validate format of user's last name
        if not last_name:
            error = 'Please enter your last name'
        if (len(last_name) > 32) or \
                not last_name.isalpha():
            error = 'Please do not enter special characters in the last name field'

        # Validate format of user's first name
        if not first_name:
            error = 'Please enter your first name'
        elif (len(first_name) > 16) or \
                not first_name.isalpha():
            error = 'Please do not enter special characters in the first name field'

        # Regex used for email format validation
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # Validate format of user's email address
        if not email_address:
            error = 'Please enter your email address'
        elif not (re.fullmatch(email_regex, email_address)):
            error = "Invalid email address"

        # If password is blank or does not meet requirements, return an error
        if not password:
            error = 'Password is required'
        elif (len(password) < 8) or \
                not (password[0].isalpha()) or \
                not (any(character.isdigit() for character in password)) or \
                not (any(character not in "!@#$%^&*") for character in password):
            error = 'Password must contain at least 8 characters, start with a letter, contain a number, and contain ' \
                    'a special character from this list: !@#$%^&*'

        # If we got no error, we're good to proceed
        if error is None:
            try:
                # Insert a new row into the DB with the new values
                """
                Explanation of values, datatypes, and ranges:
                
                    - username [str]: Generated by system. 
                        First initial + last name + account created month (2 digits) + account created year (2 digits)
                    - email_address [str]: Input by user
                    - first_name [str]: Input by user
                    - last_name [str]: Input by user
                    - active [int]: 0 for inactive account, 1 for active account. Defaults to 0 for new accounts
                    - role [int]: 0 for user, 1 for manager, 2 for admin, 3 for API access. Defaults to 0 until 
                        changed by an administrator
                    - password [str]: Hashed representation of user input. Never stored in plain text.
                    - address [str]: Input by user
                    - DOB [str]: Input by user. Should be in YYYY-MM-DD format
                    - old_passwords [str]: List of old passwords used by this user. SQLite cannot handle a Python list
                        datatype, so this must be converted to JSON
                    - password_refresh_date [str]: Date when password was last updated (YYYY-MM-DD). Set to the date 
                        account was created, then is updated each time a user updates their password
                    - creation_date [str]: Date when account was created (YYYY-MM-DD)
                    - first_pet [str]: Name of first pet. Security question #1
                    - city_born [str]: City where user was born. Security question #2
                    - year_graduated_hs [str]: Year user graduated highschool. Security question #3
                    - incorrect_login_attempts [int]: Number of times login has been attempted to this account with
                        incorrect password. Default: 0. When == 3, account is suspended
                """
                # Format today's date as a string for the database (YYYY-MM-DD)
                today = f"{today.year}-{today.month:02d}-{today.day:02d}"
                # Hash the new password
                password = generate_password_hash(password)
                db.execute(
                    "INSERT INTO users (username, email_address, first_name, last_name, active, role, password, "
                    "address, DOB, old_passwords, password_refresh_date, creation_date, first_pet, city_born, "
                    "year_graduated_hs, incorrect_login_attempts) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (username, email_address, first_name, last_name, 0, 0, password, address,
                     DOB, json.dumps([password]), today, today, first_pet, city_born, year_graduated_hs, 0)
                )
                # Write the change to the database
                db.commit()

                # Email admins to let them know that a new account is waiting to be approved
                email_registration(username, first_name, last_name)

            # Catch cases where a username already exists
            except (db.InternalError,
                    db.IntegrityError):
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
        # Ensure that user account isn't locked
        elif user['incorrect_login_attempts'] >= 3:
            error = "Account suspended due to too many incorrect login attempts. Contact an administrator."
            db.execute("UPDATE users SET active = ? WHERE username = ?", (0, username))
            db.commit()
        # Ensure that the account doesn't have a suspend start date
        elif user['suspend_start_date']:
            # If today's date is between the start and end dates, do not allow user to log in
            if (date.fromisoformat(user['suspend_start_date']) <= date.today()) and \
                    (date.today() < date.fromisoformat(user['suspend_end_date'])):
                error = f"Account suspended until {date.fromisoformat(user['suspend_end_date'])}. Contact an " \
                        f"administrator for assistance. "
            # If the end date is in the past, wipe the start and end dates
            elif date.today() > date.fromisoformat(user['suspend_end_date']):
                db.execute(
                    "UPDATE users SET suspend_start_date = NULL, suspend_end_date = NULL WHERE username = ?",
                    (username,)
                )
                db.commit()
        # If the password hash in the form doesn't match what's in the database, throw an error
        elif not check_password_hash(user['password'], password):
            if user['incorrect_login_attempts'] < 2:
                error = f"Incorrect password. {2 - user['incorrect_login_attempts']} attempts remaining."
                db.execute(
                    "UPDATE users SET incorrect_login_attempts = ? WHERE username = ?",
                    (user['incorrect_login_attempts'] + 1, username))
                db.commit()
            else:
                error = "Account suspended due to too many incorrect login attempts. Contact an administrator."
                db.execute(
                    "UPDATE users SET incorrect_login_attempts = ?, active = ? WHERE username = ?",
                    (user['incorrect_login_attempts'] + 1, 0, username))
                db.commit()
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
            # Reset the user's incorrect login attempts
            db.execute(
                "UPDATE users SET incorrect_login_attempts = ? WHERE username = ?", (0, username))
            db.commit()
            # Send the logged-in user back to the main screen of the application
            return redirect(url_for('mainpage'))

        # Display any errors we encountered on the page
        flash(error)

    return render_template('auth/login.html')


@bp.route('forgot_password', methods=('GET', 'POST'))
def forgot_password():
    """
    View to allow a user to begin the password reset process. Asks them to provide username, email address, and answer
    three security questions
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

        # Ensure that a user with that username was found in the database
        if user:
            # Check the provided email address against what's in the database
            if email_address != user['email_address']:
                flash("Email address incorrect")
                return render_template('auth/forgot_password.html')
            # Check security question answers against the database
            if (first_pet != user['first_pet']) or \
                    (city_born != user['city_born']) or \
                    (year_graduated_hs != str(user['year_graduated_hs'])):
                flash("Security questions incorrect")
                return render_template('auth/forgot_password.html')
            # If the checks pass begin to reset the password
            # First, clear the cookie
            session.clear()
            # Add the logged-in user's ID to the cookie
            session['username'] = user['username']
            # Set the user in the current session
            g.user = user
            # Send the user to a new page to reset their password
            return redirect(url_for('auth.reset_password'))
        # If there was no matching record in the database for that user, boot them back to the previous screen
        else:
            flash("Could not find user with that login.")
    return render_template('auth/forgot_password.html')


@bp.route('reset_password', methods=('GET', 'POST'))
@login_required
def reset_password():
    """
    View to allow logged-in users to reset their password
    """
    # Placeholder in case an error occurs during the process
    error = None
    if request.method == 'POST':
        # Get the entries from the page
        password1 = request.form['password1']
        password2 = request.form['password2']
        # Ensure that they match
        if password1 != password2:
            error = "Passwords must match!"
        # Ensure new passwords are not blank
        if not password1 or not password2:
            error = "You must enter a new password"
        # Ensure that passwords meet requirements
        for password in (password1, password2):
            if (len(password) < 8) or \
                    not (password[0].isalpha()) or \
                    not (any(character.isdigit() for character in password)) or \
                    not (any(character not in "!@#$%^&*") for character in password):
                error = 'Password must contain at least 8 characters, start with a letter, contain a number, and ' \
                        'contain a special character from this list: !@#$%^&*'
        # If we didn't get an error, reset the password
        if error is None:
            # Get a handle on the DB
            db = get_db()
            try:
                # Fetch the row for this user
                user = db.execute(
                    "SELECT * FROM users WHERE username = ?", (g.user['username'],)
                ).fetchone()
                # Get list of old passwords and decode it from JSON
                old_passwords = json.loads(user['old_passwords'])
                # Ensure the new password isn't in the list of old passwords
                found = False
                for password in old_passwords:
                    if check_password_hash(password, password1):
                        found = True
                        break
                # If the password is in the list of old passwords, throw an error
                if found:
                    flash("Old passwords may not be reused!")
                    return render_template('auth/reset_password.html')
                # If the new password was not in the old_passwords list, add it and set it as the new current password
                else:
                    # Hash the new password
                    new_password = generate_password_hash(password1)
                    # Add it to the list
                    old_passwords.append(new_password)
                    # Convert the list to JSON
                    old_passwords = json.dumps(old_passwords)
                    # Get today's date so we can update password refresh date to today
                    today = datetime.now()
                    # Format today's date for the database (YYYY-MM-DD)
                    today = f"{today.year}-{today.month:02d}-{today.day:02d}"
                    # Update the database
                    try:
                        db.execute(
                            "UPDATE users SET password = ?, old_passwords = ?, password_refresh_date = ? WHERE username = ?",
                            (new_password, old_passwords, today, user['username'])
                        )
                        # Write changes
                        db.commit()
                    except (db.InternalError, db.IntegrityError):
                        error = "Database error. Contact an administrator for assistance."
                # Clear the user's cookie to log them out
                session.clear()
                # Tell user to log in with new password
                flash("Password changed! Please log in with your new password")
                # Send them to the login page
                return redirect(url_for('auth.login'))
            except (db.InternalError, db.IntegrityError):
                error = "Database error. Contact an administrator for assistance."
    if error:
        flash(error)
    return render_template('auth/reset_password.html')


@bp.route('/manage_users', methods=('GET',))
@login_required
def manage_users():
    """
    Allows administrators to manage users of the system
    """
    if g.user['role'] == 2:
        user_list = None
        if request.method == 'GET':
            # Get all users from the DB
            db = get_db()
            user_list = db.execute(
                "SELECT * FROM users"
            ).fetchall()
            # Display them on the page
        return render_template('auth/manage_users.html', users=user_list)
    else:
        abort(403)


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


@bp.route('/reset_user/<username>', methods=('GET', 'POST'))
@login_required
def reset_user(username):
    """
    Allows administrators to reset status of suspended users
    """
    error = None
    if request.method == 'GET':
        # Only allow admins to do this
        if g.user['role'] != 2:
            flash("Operation not permitted")
            return redirect(url_for('mainpage'))
        else:
            # Get a handle on the database
            db = get_db()
            # Update the row
            try:
                db.execute(
                    "UPDATE users SET active = ?, incorrect_login_attempts = ? WHERE username = ?", (1, 0, username)
                )
                # Commit the change
                db.commit()
            except (db.InternalError, db.IntegrityError):
                error = f"User with username {username} not found!"
            if error is None:
                flash(f"User {username} reactivated!")
            return redirect(url_for('auth.manage_users'))


@bp.route('/edit_user/<username>', methods=('GET', 'POST'))
@login_required
def edit_user(username):
    """
    Allows administrators to edit info of a single user
    """
    if g.user['role'] == 2:
        # Get matching user from the DB
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        # Get the date the user's password will expire. This is a string.
        password_refresh_date = user['password_refresh_date']
        # Convert the string to a datetime object
        password_refresh_date = datetime.fromisoformat(password_refresh_date)
        # Calculate the date when it will expire
        password_expires = password_refresh_date + timedelta(days=180)
        # Convert this date to a string for use on the page
        password_expires = password_expires.date().__str__()

        if request.method == 'GET':
            # Display user info on the page
            return render_template('auth/edit_user.html', user=user, password_expires=password_expires)

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

            # Placeholder variables
            error = None
            suspend_start_date = None
            suspend_end_date = None
            # If we got both suspend dates, add them to the database
            if request.form['suspend_start_date'] and request.form['suspend_end_date']:
                suspend_start_date = request.form['suspend_start_date']
                suspend_end_date = request.form['suspend_end_date']
            # If user doesn't give us both a start and an end date, don't commit either
            if (request.form['suspend_start_date'] and not request.form['suspend_end_date']) or (request.form['suspend_end_date'] and not request.form['suspend_start_date']):
                error = "To set a suspension period, you must supply both a start date and an end date."
            # Only write to the database if there are no errors
            if error is None:
                # Get a handle on the database
                db = get_db()
                try:
                    # Update columns
                    db.execute(
                        "UPDATE users SET email_address = ?, first_name = ?, last_name = ?, active = ?, role = ?, "
                        "address = ?, DOB = ?, suspend_start_date = ?, suspend_end_date = ? WHERE username = ?",
                        (email, first_name, last_name, active, role, address, DOB, suspend_start_date, suspend_end_date,
                         username)
                    )
                    # Write changes
                    db.commit()
                    flash("Record updated!")
                except Exception:
                    print(f"Error: {Exception.__traceback__.tb_next}")
            else:
                flash(error)

            # Get fresh info from the DB
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return render_template('auth/edit_user.html', user=user, password_expires=password_expires)
    else:
        abort(403)


@bp.route('/my_account', methods=('GET', 'POST'))
@login_required
def my_account():
    """
     View to allow a user to edit information about their account (change password, upload photo, etc.)
     """

    if request.method == 'GET':
        # Get the date the user's password will expire. This is a string.
        password_refresh_date = g.user['password_refresh_date']
        # Convert the string to a datetime object
        password_refresh_date = datetime.fromisoformat(password_refresh_date)
        # Calculate the date when it will expire
        password_expires = password_refresh_date + timedelta(days=180)
        # Convert this date to a string for use on the page
        password_expires = password_expires.date().__str__()
        # render the template
        return render_template('auth/my_account.html', password_expires=password_expires)

    if request.method == 'POST':
        # Get handle on DB
        db = get_db()
        # Get the info from the form fields
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email_address']
        address = request.form['address']
        uploaded_pic = request.files['uploaded_pic']
        # Make sure a picture was supplied
        if uploaded_pic.filename:
            # Ensure that the pic uploaded is of the correct type
            if uploaded_pic.mimetype not in ['image/jpeg', 'image/png']:
                flash("Improper profile picture format. Profile pictures must be JPEG or PNG")
                return redirect(url_for('auth.my_account'))
            # Ensure we know what type of image it is
            image_type = None
            if uploaded_pic.mimetype == 'image/jpeg':
                image_type = "JPEG"
            if uploaded_pic.mimetype == 'image/png':
                image_type = "PNG"
            # Open image using Pillow library for manipulation
            uploaded_pic = Image.open(uploaded_pic)
            # Resize the picture to save DB size
            uploaded_pic.thumbnail((200, 200))
            # Create a temporary byte buffer for the image
            temp_buffer = BytesIO()
            # Write the uploaded image to the temporary byte buffer
            uploaded_pic.save(temp_buffer, format=image_type)
            # Save the new image in the database
            uploaded_pic = temp_buffer.getvalue()
            db.execute(
                "UPDATE users SET picture = ?, email_address = ?, first_name = ?, last_name = ?, address = ? WHERE username = ?",
                (uploaded_pic, email, first_name, last_name, address, g.user['username'])
            )
            db.commit()
        else:
            db.execute(
                "UPDATE users SET email_address = ?, first_name = ?, last_name = ?, address = ? WHERE username = ?",
                (email, first_name, last_name, address, g.user['username'])
            )
            db.commit()
        # Tell the user it worked
        flash("Profile updated!")
        return redirect(url_for('auth.my_account'))


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


@bp.route('/approve_user/<username>')
@login_required
def approve_user(username):
    if g.user and g.user['role'] == 2:
        # Get a handle on the DB
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username =?", (username,)
        ).fetchone()
        if not user:
            flash("User not found in database!")
            return redirect(url_for('mainpage'))
        elif user and user['active'] == 0:
            # Update the user's row
            db.execute(
                "UPDATE users SET active = ? WHERE username =?", (1, username)
            )
            db.commit()
            # Tell admin it's approved
            flash("Account approved!")
            # Email the user to let them know
            send_approval(username)
            return redirect(url_for('mainpage'))
        else:
            flash("User already activated!")
            return redirect(url_for('mainpage'))
    else:
        return abort(403)
