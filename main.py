from flask import Flask
from methods import twitch
import requests

app = Flask(__name__)

@app.route("/")
def hello_world():
    params = {
        "login": "bsquidwrd"
    }
    response = requests.get(url="https://api.twitch.tv/helix/users", headers=twitch.get_headers(), params=params)
    response_json = response.json()
    return f"<p>Hello, World! This has been changed</p> User ID for bsquidwrd: {response_json['data'][0]['id']}"
