import os
import time
from flask import Flask
from werkzeug.security import gen_salt
from .models import db, User, OAuth2Client
from .oauth2 import config_oauth
from .routes import bp


def create_app(config=None):
    app = Flask(__name__)

    # load default configuration
    app.config.from_object('website.settings')

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

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
        user = User.query.filter_by(username = form["username"]).first()
        if not user:
            print("Added default user ", form["username"])
            user = User(username=form["username"])
            db.session.add(user)
            db.session.commit()
        client_id = os.environ["GOOGLE_CLIENT_ID"]
        client_id_issued_at = int(time.time())
        # TODO: try not to add if already exists
        # TODO: work out if we can make the docker-compose persist the db
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

        db.session.add(client)
        db.session.commit()


def setup_app(app):
    # Create tables if they do not exist already
    @app.before_first_request
    def create_tables():
        db.create_all()

    db.init_app(app)
    config_oauth(app)
    app.register_blueprint(bp, url_prefix='')
    add_default_client(app) # TODO: work out why this seems to add two!
