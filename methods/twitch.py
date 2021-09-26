import hashlib
import hmac
import os
import requests
from requests.api import request
from urllib.parse import urlencode


# Define and set variables for various information we need
client_id = os.environ["TWITCH_CLIENT_ID"]
client_secret = os.environ["TWITCH_CLIENT_SECRET"]
twitch_eventsub_secret = os.environ["TWITCH_EVENTSUB_SECRET"]

auth_redirect_uri = "http://localhost:5000/auth"


# The endpoint for all things Event Sub
eventsub_endpoint = "eventsub/subscriptions"


# Get the App Access Token. If one not generated, generate it
def get_access_token():
    access_token = os.environ.get("TWITCH_ACCESS_TOKEN")
    if access_token:
        return access_token
    return generate_access_token()


# Generate App Access Token and set OS variable
def generate_access_token():
    # Generate an access token for authenticating requests
    auth_body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    auth_response = requests.post("https://id.twitch.tv/oauth2/token", auth_body)

    # Setup Headers for future requests
    auth_response_json = auth_response.json()

    # Set Environment variable
    access_token = auth_response_json["access_token"]
    os.environ["TWITCH_ACCESS_TOKEN"] = access_token
    return access_token


# Central way to get headers for requests to Twitch
def get_auth_headers(access_token = None):
    if access_token == None:
        access_token = get_access_token()
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    return headers


# Validate Access Token
def validate_auth(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url="https://id.twitch.tv/oauth2/validate", headers=headers)
    response_json = response.json()
    if response.ok and response_json.get('client_id') == client_id:
        return response_json
    return False


# Used to verify a message to ensure it's from Twitch
def verify_signature(request):
    hmac_message = request.headers['Twitch-Eventsub-Message-Id'] + request.headers['Twitch-Eventsub-Message-Timestamp'] + request.data.decode()
    message_signature = "sha256=" + hmac.new(str.encode(twitch_eventsub_secret), str.encode(hmac_message), hashlib.sha256).hexdigest()
    if message_signature == request.headers['Twitch-Eventsub-Message-Signature']:
        return True
    return False


# Generic way to send requests to Twitch for ease of use
def send_twitch_request(endpoint, body=None, params=None, method = "GET", headers = None):
    # If no special headers are passed, use auth headers
    if not headers:
        headers = get_auth_headers()
    url = f"https://api.twitch.tv/helix/{endpoint}"
    try:
        # Assemble request data
        # This can be used as parameters, so we can choose which parts to use
        request_data = {
            "method": method,
            "url": url,
            "headers": headers
        }
        # If we want to pass in parameters, set the variable to pass
        if params:
            request_data["params"] = params

        # If we want to pass in body (json), set the variable to pass
        if body:
            request_data["json"] = body

        # Make the request
        response = requests.request(**request_data)

        # Twitch doesn't return data when sending DELETE so just return if the call succeeded
        if method == "DELETE":
            return response.ok
        
        # Translate the body into JSON
        response_json = response.json()
        # Twitch sends error if there was an error, so try and interpret it for eventsub/subscriptions
        if response_json.get("error") and endpoint == eventsub_endpoint:
            error_type = response_json["error"]
            error_message = response_json["message"]
            condition_type = list(body['condition'].keys())[0]
            condition_id = body['condition'][condition_type]
            # Print information so we know what failed
            print(f"{endpoint}\t|\t{error_type}\t|\t{condition_type} = {condition_id}\t\t\t|\t{body['type']}: {error_message}")
        # Return the response
        return response_json
    except Exception as e:
        raise e


# Method to easily get the scopes needed for an event
def get_scopes_for_event(event_name):
    return get_events(event_name).get("scopes", ["public"])


# Get all event types
def get_event_types():
    return get_events().keys()


# Get all events, or a specific one
def get_events(event_name=None):
    events = {
        "channel.update": {
            "type": "broadcaster_user_id",
            "scopes": ['public']
        },
        "channel.follow": {
            "type": "broadcaster_user_id",
            "scopes": ['public']
        },
        "channel.subscribe": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.end": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.gift": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.message": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.cheer": {
            "type": "broadcaster_user_id",
            "scopes": ['bits:read']
        },
        "channel.raid": {
            "type": "to_broadcaster_user_id",
            "scopes": ['public']
        },
        "channel.ban": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:moderate']
        },
        "channel.unban": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:moderate']
        },
        "channel.moderator.add": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:moderate']
        },
        "channel.moderator.remove": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:moderate']
        },
        "channel.channel_points_custom_reward.add": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward.update": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward.remove": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward_redemption.add": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward_redemption.update": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:redemptions']
        },
        "channel.poll.begin": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:polls']
        },
        "channel.poll.progress": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:polls']
        },
        "channel.poll.end": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:polls']
        },
        "channel.prediction.begin": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.progress": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.lock": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.end": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:predictions']
        },
        "channel.goal.begin": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:goals']
        },
        "channel.goal.progress": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:goals']
        },
        "channel.goal.end": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:goals']
        },
        "channel.hype_train.begin": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:hype_train']
        },
        "channel.hype_train.progress": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:hype_train']
        },
        "channel.hype_train.end": {
            "type": "broadcaster_user_id",
            "scopes": ['channel:read:hype_train']
        },
        "stream.online": {
            "type": "broadcaster_user_id",
            "scopes": ['public']
        },
        "stream.offline": {
            "type": "broadcaster_user_id",
            "scopes": ['public']
        },
        "user.update": {
            "type": "user_id",
            "scopes": ['public']
        }
    }
    return events.get(event_name, events)


# Generic-ish body to send to request a subscription setup
def get_subscription_body(user_id, event_name):
    event_info = get_events(event_name)
    return {
        "type": f"{event_name}",
        "version": "1",
        "condition": {
            f"{event_info['type']}": f"{user_id}"
        },
        "transport": {
            "method": "webhook",
            "callback": "https://example.com/webhooks/callback",
            "secret": twitch_eventsub_secret
        }
    }


# Subscribe a user to all available events
def subscribe_user(user_id):
    for event in get_event_types():
        body = get_subscription_body(user_id, event)
        send_twitch_request(endpoint=eventsub_endpoint, method="POST", body=body)



# Generate authorization URL
def get_auth_url():
    # https://id.twitch.tv/oauth2/authorize?client_id=<your client ID>&redirect_uri=<your registered redirect URI>&response_type=<type>&scope=<space-separated list of scopes>
    scopes = []
    for event in get_event_types():
        event_scopes = get_scopes_for_event(event)
        for event_scope in event_scopes:
            if event_scope.lower() != "public" and event_scope.lower() not in scopes:
                scopes.append(event_scope)

    query_params = {
        "client_id": client_id,
        "redirect_uri": auth_redirect_uri,
        "response_type": "token",
        "force_verify": "true",
        "scope": " ".join(scopes)
    }
    formatted_query_params = urlencode(query_params)
    return f"https://id.twitch.tv/oauth2/authorize?{formatted_query_params}"


# Get a user from Twitch on ID, with an option access_token
# If no access_token is passed in, use the one generated on app start
def get_user(id, access_token=None):
    params = {
        "id": id
    }
    if access_token:
        headers = get_auth_headers(access_token)
    else:
        headers = get_auth_headers()
    return send_twitch_request(endpoint="users", method="GET", params=params, headers=headers)
