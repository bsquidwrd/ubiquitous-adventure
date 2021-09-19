from flask import Flask, jsonify
from methods import twitch
import requests
import json

app = Flask(__name__)

@app.route("/")
def hello_world():
    params = {
        "login": "bsquidwrd"
    }
    response = twitch.send_twitch_request(endpoint="users", params=params)
    for user in response['data']:
        twitch.subscribe_user(user['id'])
    return f"<p>Hello, World! This has been changed</p> User ID for {params['login']}: {response['data'][0]['id']}"


@app.route("/list")
def list_subscriptions():
    response = twitch.send_twitch_request(endpoint = twitch.eventsub_endpoint)
    return jsonify(response)


@app.route("/delete")
def delete_subscriptions():
    subscriptions = twitch.send_twitch_request(endpoint = twitch.eventsub_endpoint)
    for subscription in subscriptions['data']:
        twitch.send_twitch_request(endpoint=twitch.eventsub_endpoint, method="DELETE", params={"id": subscription["id"]})
    return f"Deleted subscriptions"
