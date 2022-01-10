import pandas as pd
from firebase_admin import credentials, firestore, initialize_app

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
Users = db.collection('Users')

print(Users.document('exampleuseerid').get().to_dict())

def createUserIfNotExist(userId, access_token, refresh_token):
    if not Users.document(userId).get().exists:
        Users.document(userId).set({'access_token': access_token, 'refresh_token': refresh_token, 'addlist': [], 'skiplist': []})

def getUser(userId):
    return Users.document(userId).get().to_dict()

def updateUser(userId, user):
    return Users.document(userId).update(user)
def updateUserAddlist(userId, tracks):
    return Users.document(userId).update({'addlist': firestore.ArrayUnion(tracks)})
def updateUserSkiplist(userId, tracks):
    return Users.document(userId).update({'skiplist': firestore.ArrayUnion(tracks)})
