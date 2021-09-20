from flask import Flask, jsonify
from methods import twitch

app = Flask(__name__)


# The root page when going to http://localhost:5000
@app.route("/")
def hello_world():
    params = {
        "login": "bsquidwrd"
    }
    # Search for the user
    response = twitch.send_twitch_request(endpoint="users", params=params)
    for user in response['data']:
        # For each user in the response, subscribe to their events
        twitch.subscribe_user(user['id'])
    # Return page to show that requests are working
    return f"<p>Hello, World! This has been changed</p> User ID for {params['login']}: {response['data'][0]['id']}"


# List view for seeing the first 100 subscriptions
@app.route("/list")
def list_subscriptions():
    response = twitch.send_twitch_request(endpoint = twitch.eventsub_endpoint)
    return jsonify(response)


# This will delete the first 100 subscriptions, just for ease of cleaning up
@app.route("/delete")
def delete_subscriptions():
    subscriptions = twitch.send_twitch_request(endpoint = twitch.eventsub_endpoint)
    for subscription in subscriptions['data']:
        # Delete each subscription
        twitch.send_twitch_request(endpoint=twitch.eventsub_endpoint, method="DELETE", params={"id": subscription["id"]})
    return f"Deleted subscriptions"
