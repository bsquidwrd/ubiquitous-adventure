import os
import hmac
import hashlib
import requests
import json


client_id = os.environ["TWITCH_CLIENT_ID"]
client_secret = os.environ["TWITCH_CLIENT_SECRET"]
twitch_eventsub_secret = os.environ["TWITCH_EVENTSUB_SECRET"]


# The endpoint for all things Event Sub
eventsub_endpoint = "eventsub/subscriptions"


def get_access_token():
    access_token = os.environ.get("TWITCH_ACCESS_TOKEN")
    if access_token:
        return access_token
    return generate_access_token()


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
    os.environ["TWITCH_ACCESS_TOKEN"] = auth_response_json["access_token"]
    return os.environ.get("TWITCH_ACCESS_TOKEN")


def get_auth_headers():
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {get_access_token()}"
    }
    return headers


def validate_auth(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url="https://id.twitch.tv/oauth2/validate", headers=headers)
    response_json = response.json()
    if response.status_code == requests.status_codes.ok & response_json.get('client_id') == client_id:
        return response_json
    return False


# Used to verify a message to ensure it's from Twitch
def verify_signature(request):
    hmac_message = request.headers['Twitch-Eventsub-Message-Id'] + request.headers['Twitch-Eventsub-Message-Timestamp'] + request.data.decode()
    message_signature = "sha256=" + hmac.new(str.encode(twitch_eventsub_secret), str.encode(hmac_message), hashlib.sha256).hexdigest()
    if message_signature == request.headers['Twitch-Eventsub-Message-Signature']:
        return True
    return False


def send_twitch_request(endpoint, body, params, method = "GET", headers = None):
    if not headers:
        headers = get_auth_headers()
    url = f"https://api.twitch.tv/helix/{endpoint}"
    try:
        response = requests.request(method=method, url=url, body=body, headers=headers, params=params)
        return response.json()
    except Exception as e:
        print(e)


def get_scopes_for_event(event_name):
    return get_events().get(event_name["scopes"], "public")


def get_event_types():
    return get_events().keys()


def get_events(event_name=None):
    events = {
        "channel.update": {
            "type": "user",
            "scopes": ['public']
        },
        "channel.follow": {
            "type": "user",
            "scopes": ['public']
        },
        "channel.subscribe": {
            "type": "user",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.end": {
            "type": "user",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.gift": {
            "type": "user",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.subscription.message": {
            "type": "user",
            "scopes": ['channel:read:subscriptions']
        },
        "channel.cheer": {
            "type": "user",
            "scopes": ['bits:read']
        },
        "channel.raid": {
            "type": "user",
            "scopes": ['public']
        },
        "channel.ban": {
            "type": "user",
            "scopes": ['channel:moderate']
        },
        "channel.unban": {
            "type": "user",
            "scopes": ['channel:moderate']
        },
        "channel.moderator.add": {
            "type": "user",
            "scopes": ['channel:moderate']
        },
        "channel.moderator.remove": {
            "type": "user",
            "scopes": ['channel:moderate']
        },
        "channel.channel_points_custom_reward.add": {
            "type": "user",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward.update": {
            "type": "user",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward.remove": {
            "type": "user",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward_redemption.add": {
            "type": "user",
            "scopes": ['channel:read:redemptions']
        },
        "channel.channel_points_custom_reward_redemption.update": {
            "type": "user",
            "scopes": ['channel:read:redemptions']
        },
        "channel.poll.begin": {
            "type": "user",
            "scopes": ['channel:read:polls']
        },
        "channel.poll.progress": {
            "type": "user",
            "scopes": ['channel:read:polls']
        },
        "channel.poll.end": {
            "type": "user",
            "scopes": ['channel:read:polls']
        },
        "channel.prediction.begin": {
            "type": "user",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.progress": {
            "type": "user",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.lock": {
            "type": "user",
            "scopes": ['channel:read:predictions']
        },
        "channel.prediction.end": {
            "type": "user",
            "scopes": ['channel:read:predictions']
        },
        "channel.goal.begin": {
            "type": "user",
            "scopes": ['channel:read:goals']
        },
        "channel.goal.progress": {
            "type": "user",
            "scopes": ['channel:read:goals']
        },
        "channel.goal.end": {
            "type": "user",
            "scopes": ['channel:read:goals']
        },
        "channel.hype_train.begin": {
            "type": "user",
            "scopes": ['channel:read:hype_train']
        },
        "channel.hype_train.progress": {
            "type": "user",
            "scopes": ['channel:read:hype_train']
        },
        "channel.hype_train.end": {
            "type": "user",
            "scopes": ['channel:read:hype_train']
        },
        "stream.online": {
            "type": "user",
            "scopes": ['public']
        },
        "stream.offline": {
            "type": "user",
            "scopes": ['public']
        },
        "user.update": {
            "type": "user",
            "scopes": ['public']
        }
    }
    return events.get(event_name, events)
