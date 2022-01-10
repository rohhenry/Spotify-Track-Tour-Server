import requests
import os

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
BASE_URL = 'https://api.spotify.com/v1/'
SCOPE = "streaming user-read-email user-read-private user-read-playback-state user-modify-playback-state"

def getUserId(token):
    sp = spotipy.Spotify(auth=token)
    id = sp.current_user()['id']
    return id

def getAccessToken():
    AUTH_URL = 'https://accounts.spotify.com/api/token'

    # POST
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data['access_token']

    return access_token

def refreshToken(refresh_token):
    AUTH_URL = 'https://accounts.spotify.com/api/token'
    response = requests.post(AUTH_URL, auth=(CLIENT_ID, CLIENT_SECRET), headers={
            'Content-Type': 'application/x-www-form-urlencoded'
    }, 
    data={'grant_type': 'refresh_token', 'refresh_token': refresh_token})
    response_json = response.json()
    print(response_json)
    access_token = response_json['access_token']
    return access_token
