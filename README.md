# Google Actions To Home MQTT Connector

## Description
If you are running a home MQTT server (possibly with Tasmota devices, but this can be adapted), and having gone down the route of full stack 3rd party solutions (such as TP-Link, Alexa, or even the DIY HomeAssistant or NodeRed), you might want to connect Google Home and its voice capabilities to control your MQTT devices. Then this is what you need.

## Background and License
Based off of authlib's example Oauth server example, and so inherits a BSD 3-clause license, is free for you to reuse and edit, but no guarantee is provided and any further work must hold the same license. (See LICENSE for full details).

- Authlib Repo: <https://github.com/lepture/authlib>
- Authlib Example Repo: <https://github.com/authlib/example-oauth2-server>
## Requirements

 - Docker compose
 - A local SSL secured webserver
 - An MQTT server you want to control

## Setup 
### Home Server Setup
You will require a home webserver, with an SSL port forwarded to port 5000 on the host computer. This could be done by following (e.g.) <https://medium.com/@mightywomble/how-to-set-up-nginx-reverse-proxy-with-lets-encrypt-8ef3fd6b79e5>
### Google Actions Setup

 1. Create a new project on the Google Actions Dashboard (https://console.actions.google.com)
 2. Choose any name for the project, note it down.
 3. Choose "Smart Home" project to start building.
 4. Name your action anything you want (this will be the name you see when setting up on a device.
 5. Setup account linking as follows:
 6. Client ID must be a random string, typically 32 hex characters. Note it down.
 7. Client secret must be a random string typically 32 hex characters. Note it down.
 8. Authorization URL is https://YOUR_IP_OR_DOMAIN:YOUR_OUTWARD_PORT/oauth/authorize
 9. Token URL is https://YOUR_IP_OR_DOMAIN:YOUR_OUTWARD_PORT/oauth/token
 10. Configure the client and set scope to intents.
 11. Add an action and set Fulfillment URL to https://YOUR_IP_OR_DOMAIN:YOUR_OUTWARD_PORT/api and save
 12. Also click test, this will then make the action available on your devices (via the Home App > Add > Setup device> Have something already set up and your action will appear as [test] Action Name.
 13. Further users can be added to also use this app via the actions console ...>Manage User access On Google Cloud Platform. Other users can be added as owners there by email address to gain access.

### Bridge setup
Download the repo and copy web-variables.env.eg to web-variables.env and fill in.
|Variable|Description  |
|--|--|
|GOOGLE_CLIENT_ID|The client ID used above|
|GOOGLE_CLIENT_SECRET|The secret used above|
|GOOGLE_DEFAULT_USERNAME|Any name|
|GOOGLE_PROJECT_ID|The project name above|
|MQTT_USERNAME|The username of your local mqtt server|
|MQTT_PASSWORD|The password for your local mqtt server|
|MQTT_ADDRESS|The address of your local mqtt server. Note even if this is the same machine use the absolute IP not localhost, as docker point localhost inside itself, not to the host machine|
|MQTT_PORT|The port of your local mqtt server (typically 1883)|

Also edit the devices in `website/devices.py` to be your own. We assume a %prefix%/%topic% format for Tasmota MQTT (https://tasmota.github.io/docs/MQTT/), but this can be modified in `intents.py`

## Running
Run a `docker-compose build` followed by `docker-compose up -d` to run and register the service to always restart. Use docker compose to control and monitor the app (https://docs.docker.com/compose/)
