import os
import hmac
import hashlib
import requests
import json

from requests.api import request


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


def send_twitch_request(endpoint, body=None, params=None, method = "GET", headers = None):
    if not headers:
        headers = get_auth_headers()
    url = f"https://api.twitch.tv/helix/{endpoint}"
    try:
        request_data = {
            "method": method,
            "url": url,
            "headers": headers
        }
        if params:
            request_data["params"] = params

        if body:
            request_data["json"] = body

        response = requests.request(**request_data)
        if method == "DELETE":
            return True
        response_json = response.json()
        if response_json.get("error") and endpoint == eventsub_endpoint:
            error_type = response_json["error"]
            error_message = response_json["message"]
            condition_type = list(body['condition'].keys())[0]
            condition_id = body['condition'][condition_type]
            print(f"{endpoint}\t|\t{error_type}\t|\t{condition_type} = {condition_id}\t\t\t|\t{body['type']}: {error_message}")
        return response_json
    except Exception as e:
        raise e


def get_scopes_for_event(event_name):
    return get_events().get(event_name["scopes"], "public")


def get_event_types():
    return get_events().keys()


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

def subscribe_user(user_id):
    for event in get_event_types():
        body = get_subscription_body(user_id, event)
        send_twitch_request(endpoint=eventsub_endpoint, method="POST", body=body)
