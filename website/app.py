import os
import time
from flask import Flask
from werkzeug.security import gen_salt
from .models import db, User, OAuth2Client, default_devices
from .oauth2 import config_oauth
from .routes import bp, basic_auth

def create_app(config=None):
    app = Flask(__name__)

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    app.config['BASIC_AUTH_USERNAME'] = os.environ["ADMIN_USERNAME"]
    app.config['BASIC_AUTH_PASSWORD'] = os.environ["ADMIN_PASSWORD"]
    
    setup_app(app)
    return app

def add_default_client(app):
    form = {}
    form["username"] = os.environ["GOOGLE_DEFAULT_USERNAME"]
    form["client_name"] = "GOOGLE"
    form["client_uri"] = "https://googleusercontent.com"
    form["grant_types"] = ["authorization_code","refresh_token"]
    form["redirect_uris"] = ["https://oauth-redirect.googleusercontent.com/r/" + os.environ["GOOGLE_PROJECT_ID"]]
    form["response_types"] = ["code"]
    form["scope"] = "intents"
    form["token_endpoint_auth_method"] = "client_secret_post"
    with app.app_context():
        # Add/update the default user
        user = User.query.filter_by(username = form["username"]).first()
        userexists = (user != None)
        user = User(username=form["username"])
        if not userexists:
            db.session.add(user)

        # Add/update the default client to access that user
        client_id = os.environ["GOOGLE_CLIENT_ID"]
        client = OAuth2Client.query.filter_by(client_id = client_id).first()
        clientexists = (client != None)

        client_id_issued_at = int(time.time())
        client = OAuth2Client(
            client_id=client_id,
            client_id_issued_at=client_id_issued_at,
            user_id=user.id,
        )

        client_metadata = {
            "client_name": form["client_name"],
            "client_uri": form["client_uri"],
            "grant_types": form["grant_types"],
            "redirect_uris": form["redirect_uris"],
            "response_types": form["response_types"],
            "scope": form["scope"],
            "token_endpoint_auth_method": form["token_endpoint_auth_method"]
        }
        client.set_client_metadata(client_metadata)

        if form['token_endpoint_auth_method'] == 'none':
            client.client_secret = ''
        else:
            client.client_secret = os.environ["GOOGLE_CLIENT_SECRET"]

        if not clientexists:
            db.session.add(client)

        # Commit to DB
        db.session.commit()


def setup_app(app):
    # Create tables if they do not exist already
    @app.before_first_request
    def create_tables():
        db.create_all()
        add_default_client(app)
        default_devices()

    db.init_app(app)
    basic_auth.init_app(app)
    config_oauth(app)
    app.register_blueprint(bp, url_prefix='')
