import time
import sys
import os
from flask import Blueprint, request, session, url_for
from flask import render_template, redirect, jsonify
from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from .models import db, User, OAuth2Client
from .oauth2 import authorization, require_oauth
from .intents import api_delegate

bp = Blueprint(__name__, 'home')

@bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = User.query.filter_by(username=os.environ["GOOGLE_DEFAULT_USERNAME"]).first()
    resp = authorization.create_authorization_response(grant_user=user)
    return resp

@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')

@bp.route('/api', methods = ['POST'])
@require_oauth('intents')
def api(): 
    user = current_token.user
    print("API REQ:", request.json, flush = True)
    payload = api_delegate(request.json)
    if payload:
        payload["agentUserId"] = str(user.id)
        response = {"payload": payload}
        if "requestId" in request.json:
            response["requestId"] = request.json["requestId"]
        return jsonify(response)
    return "Bad request", 400
