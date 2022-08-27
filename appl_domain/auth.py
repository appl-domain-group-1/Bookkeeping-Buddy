import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from appl_domain.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """
    View to allow a user to register for a new account
    """
    if request.method == 'POST':
        # TODO: the tutorial allows the username to be set by the user, but we'll set it automatically. Change this.
        username = request.form['username']
        password = request.form['username']
        db = get_db()
        error = None

        # If username is blank, return an error
        if not username:  # TODO: This won't be required in the final version
            error = 'Username is required'
        # If password is blank, return an error
        if not password:
            error = 'Password is required'
        # TODO: perform other password validation here (number of characters, number of digits, etc.)

        # If we got no error, we're good to proceed
        if error is None:
            try:
                # Insert a new row into the DB with the new values
                db.execute(  # TODO: This only stores username and password in the DB. We want lots more info.
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                # Write the change to the database
                db.commit()
            # Catch cases where a username already exists
            except db.InternalError:  # TODO: Probably won't need this error since usernames are not user-supplied.
                error = f"User {username} is already registered."
            else:
                # TODO: Should show the new user a page saying their account is awaiting approval from an admin
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
            "SELECT * FROM users WHERE username = ?", (username)
        ).fetchone()

        # If we are given a blank username, throw an error
        if user is None:
            error = "Incorrect username"
        # If the password hash in the form doesn't match what's in the database, throw an error
        elif not check_password_hash(user['password'], password):
            error = "Incorrect password"

        # If we don't have any errors, we're good to proceed
        if error is None:
            # Session represents the cookie that is sent to the user's browser. Clear it first
            session.clear()
            # Add the logged-in user's ID to the cookie
            session['username'] = user['username']
            # Send the logged-in user back to the main screen of the application
            return redirect(url_for('index'))

        # Display any errors we encountered on the page
        flash(error)

    return render_template('auth/login.html')


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
    return redirect(url_for('index'))


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