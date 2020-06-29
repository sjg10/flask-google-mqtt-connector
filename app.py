import os
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
from website.app import create_app

if __name__ == "__main__":
    print("Insecure mode ACTIVE")
    app = create_app({
        'SECRET_KEY': 'secret',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
    })
    app.run(host="0.0.0.0", debug=True)
