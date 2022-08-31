import os

import flask
from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'appl_domain.sqlite'),
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

    # Initialize the database
    import appl_domain.db as db
    db.init_app(app)

    @app.route('/')
    def mainpage():
        return flask.render_template('index.html', z="This is the main page")

    @app.route('/login')
    def login_page():
        x = 5
        y = 6
        z = x + y
        return flask.render_template("auth/login.html", z=z)

    import appl_domain.list_users as list_users
    app.register_blueprint(list_users.bp)

    import appl_domain.auth as auth
    app.register_blueprint(auth.bp)

    return app
