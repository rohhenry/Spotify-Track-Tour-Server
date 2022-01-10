import os

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS, cross_origin


import urllib
import requests
from dotenv import load_dotenv

import brain
import spotifyapi
import db

app = Flask(__name__)
CORS(app)

load_dotenv()
if os.getenv('FLASK_ENV') == 'production':
  BACKEND_URL = os.getenv('PRODUCTION_BACKEND_URL')
  FRONTEND_URL = os.getenv('PRODUCTION_FRONTEND_URL')
else:
  BACKEND_URL = os.getenv('DEVELOPMENT_BACKEND_URL')
  FRONTEND_URL = os.getenv('DEVELOPMENT_FRONTEND_URL')

print('HELLO LOGS')
#possible thread saftey issue

@app.route('/')
def serve():
  print('ROOT REACHED')
  return {'message': 'server is running'}

@app.route("/auth/token", methods=['POST'])
@cross_origin()
def token():
  print('TOKEN REACHED')
  userId = request.get_json()['userId']
  user = db.getUser(userId)
  if user:
    refresh_token = user['refresh_token']
    access_token = spotifyapi.refreshToken(refresh_token)
    user['access_token'] = access_token
    db.updateUser(userId, user)
    print('token refreshed')
  else:
    access_token = ''
  print(access_token)
  return jsonify({'access_token': access_token})

@app.route("/auth/login")
@cross_origin()
def login():
  print('LOGIN REACHED')
  url = 'https://accounts.spotify.com/authorize?'
  params = { 
    'response_type':'code',
    'client_id':spotifyapi.CLIENT_ID,
    'scope': spotifyapi.SCOPE,
    'redirect_uri': BACKEND_URL + "/auth/callback",
  }
  return redirect(url + urllib.parse.urlencode(params))

@app.route("/auth/callback")
@cross_origin()
def callback():
  print('CALLBACK REACHED')
  code = request.args.get('code')
  AUTH_URL = 'https://accounts.spotify.com/api/token'
  response = requests.post(AUTH_URL, auth=(spotifyapi.CLIENT_ID, spotifyapi.CLIENT_SECRET), headers={
        'Content-Type': 'application/x-www-form-urlencoded'
  }, 
  data={'code': code, 'redirect_uri': BACKEND_URL + '/auth/callback', 'grant_type': 'authorization_code'})
  response_json = response.json()
  # print(response_json)
  access_token = response_json['access_token']
  refresh_token = response_json['refresh_token']
  #get email from user
  userId = spotifyapi.getUserId(access_token)
  print(type(userId))
  #save access_token to file

  db.createUserIfNotExist(userId, access_token, refresh_token)

  return redirect(FRONTEND_URL + '?' + urllib.parse.urlencode({'userId': userId}))

@app.route("/update", methods=['POST'])
@cross_origin()
def updateModel():
  print('UPDATE REACHED')
  json = request.get_json()
  userId=json['userId']
  ids = json.get('ids')
  if ids:
    db.updateUserAddlist(userId, ids)
    return '', 201
  id=json['id']
  feedback=json['feedback']
  if feedback == 1:
    db.updateUserAddlist(userId, [id])
  else:
    db.updateUserSkiplist(userId, [id])
  return '', 201


@app.route("/recommend", methods=['POST'])
@cross_origin()
def getRecommendation():
  print('UPDATE REACHED')
  json = request.get_json()
  output = brain.getRecommendation(userId=json['userId'])
  return output

@app.route("/search", methods=['POST'])
@cross_origin()
def search():
  print('SEARCH REACHED')
  name = request.get_json()['name'].lower()
  return jsonify(brain.searchByName(name))

@app.route("/refresh_token", methods=['POST'])
@cross_origin()
def refreshToken():
  print('REFRESH TOKENS REACHED')
  userId = request.get_json()['userId']
  user = db.getUser(userId)
  refresh_token = user['refresh_token']
  access_token = spotifyapi.refreshToken(refresh_token)
  user['access_token'] = access_token
  db.updateUser(userId, user)
  print('token refreshed')
  return jsonify({'access_token': access_token})

if __name__ == '__main__':
  app.run(port=5000)