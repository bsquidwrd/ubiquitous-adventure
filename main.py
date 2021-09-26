from flask import Flask, jsonify, render_template, session, Response
from methods import twitch

app = Flask(__name__)
app.secret_key = 'any random string'


# The root page when going to http://localhost:5000
@app.route("/")
def hello_world():
    username = "bsquidwrd"
    params = {
        "login": username
    }
    # Search for the user
    response = twitch.send_twitch_request(endpoint="users", params=params)
    user_response = None
    for user in response['data']:
        if user['login'] == username:
            user_response = user
    
    # Return page to show that requests are working
    return render_template('index.html', twitch_user=user_response, twitch_auth_url=twitch.get_auth_url())


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


# After completing auth with Twitch, load a basic javascript page then redirect them
@app.route("/auth")
def twitch_auth():
    return render_template('auth.html')


# The main page users are redirected to after authorization
@app.route("/events")
def display_events():
    access_token = session['access_token']
    auth_validation = twitch.validate_auth(access_token)

    session["scopes"] = auth_validation.get("scopes", [])
    session["id"] = auth_validation["user_id"]
    session["login"] = auth_validation["login"]

    users_response = twitch.get_user(session["id"], access_token=session['access_token'])
    user_response = ""
    for user in users_response["data"]:
        if user.get("id") == session["id"]:
            user_response = user
            break

    return render_template('events.html', twitch_user=user_response)


# Used to set variables in the Session for use in code
@app.route("/setvariables/<token_type>/<access_token>")
def set_session_variables(token_type, access_token):
    session['token_type'] = token_type
    session['access_token'] = access_token
    return Response(response="OK", status=200, mimetype="text/plain")
