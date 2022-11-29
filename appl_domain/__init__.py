import base64
import os
from datetime import datetime, timedelta

import flask
from flask import Flask, g

import appl_domain.dashboard


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'appl_domain.sqlite'),
        CORS_HEADERS='Content-Type'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.template_filter('make_image')
    def make_image(image):
        return str(base64.b64encode(image), "utf-8")

    # Initialize the database
    import appl_domain.db as db
    db.init_app(app)

    @app.route('/')
    def mainpage():
        # Only populate "my info" and dashboard if a user is logged in
        if g.user:
            # Items for dashboard
            assets = dashboard.get_assets()
            liabilities = dashboard.get_liabilities()
            current_ratio = dashboard.get_current_ratio()
            working_capital = dashboard.get_working_capital()
            debt_to_equity = dashboard.get_debt_to_equity()
            equity_ratio = dashboard.get_equity_ratio()

            # Items for "My Info"
            my_journal_entries = dashboard.get_journal_entries(g.user['username'])
            # Get the date the user's password will expire. This is a string.
            password_refresh_date = g.user['password_refresh_date']
            # Convert the string to a datetime object
            password_refresh_date = datetime.fromisoformat(password_refresh_date)
            # Calculate the date when it will expire
            password_expires = password_refresh_date + timedelta(days=180)
            next_suspension = dashboard.get_next_suspension(g.user['username'])

            return flask.render_template('index.html',
                                         assets=assets,
                                         liabilities=liabilities,
                                         current_ratio=current_ratio,
                                         working_capital=working_capital,
                                         debt_to_equity=debt_to_equity,
                                         equity_ratio=equity_ratio,
                                         my_journal_entries=my_journal_entries,
                                         password_expires=password_expires,
                                         next_suspension=next_suspension)
        else:
            return flask.render_template('index.html')

    @app.route('/login')
    def login_page():
        return flask.render_template("auth/login.html")

    import appl_domain.auth as auth
    app.register_blueprint(auth.bp)

    import appl_domain.API as api
    app.register_blueprint(api.bp)

    import appl_domain.fin_accts as fin_accts
    app.register_blueprint(fin_accts.bp)

    import appl_domain.journaling as journaling
    app.register_blueprint(journaling.bp)

    import appl_domain.statements as statements
    app.register_blueprint(statements.bp)

    return app
