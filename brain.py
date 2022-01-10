import numpy as np
import pandas as pd

from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error

import db

#constants
DATASET_PATH = 'dataset/tracksOrderedByPopularity.csv'
CHUNK_SIZE = 50000

#hyperparameters
alpha = 0.05
degree = 2
interaction_only = True
sampling_strategy = "greedy"
use_popularity_heuristic = True
popularity_heuristic_threshold = 15000

feature_names = ['danceability','energy','speechiness','acousticness','instrumentalness','valence']

def isEnglish(s):
  if type(s) != str:
    return False
  return s.isascii()

def searchByName(name):
  max_res = 5
  res = []
  with pd.read_csv(DATASET_PATH, chunksize=CHUNK_SIZE, usecols=(['id', 'popularity', 'artists', 'name'])) as reader:
    num_res = 0
    for chunk in reader:
      mask = chunk['name'].str.contains(name, regex=False, case=False, na=False)
      match = chunk[mask]
      if num_res >= max_res:
        break
      if not match.empty:
        res.append(match)
        num_res += len(match)
  if not res:
    return []
  return pd.concat(res).sort_values(by=['popularity'], ascending=False).head(max_res).to_dict(orient='records')

def createTrainingExamplesFromUser(user):
  addlist = user['addlist']
  skiplist = user['skiplist']
  x_train = []
  y_train = []
  poly = PolynomialFeatures(degree=degree, interaction_only=interaction_only)
  print('reading csv')
  with pd.read_csv(DATASET_PATH, chunksize=CHUNK_SIZE, usecols=(feature_names + ['id'])) as reader:
    for chunk in reader:
      matches = chunk[chunk['id'].isin(addlist)]
      if not matches.empty:
        x = matches[feature_names].to_numpy()
        x_train.append(x)
        y_train.append(np.full(len(matches), 1))
      matches = chunk[chunk['id'].isin(skiplist)]
      if not matches.empty:
        x = matches[feature_names].to_numpy()
        x_train.append(x)
        y_train.append(np.full(len(matches), -1))
  print('processed into numpy')
  x_np = np.concatenate(x_train, axis=0)
  del x_train
  x_np = poly.fit_transform(x_np)
  print("training shape", x_np.shape)
  y_np = np.concatenate(y_train, axis=0)
  del y_train
  y_np = balanceClasses(y_np)
  return x_np, y_np

# sampling methods
def chooseNext(predictions, indexes, strategy):
  print('choosing next')
  utility = predictions
  scaled_utility = utility + abs(utility.min())
  scaled_utility = scaled_utility ** 4
  scaled_utility = scaled_utility / scaled_utility.sum()
  if strategy == 'thompson':
    i = np.random.choice(len(utility), p=scaled_utility)
  elif strategy == 'greedy':
    i = np.argmax(utility)
  print(i, indexes[i])
  df = pd.read_csv(DATASET_PATH, skiprows=range(1, indexes[i]+1), nrows=1)
  choice  = df.iloc[0][['name', 'artists', 'id']].to_dict()
  confidence = utility[i]
  return choice, confidence

#balances the classes
def balanceClasses(y):
  positives = y[y >= 0]
  negatives = y[y < 0]
  factor = len(y)/2
  balanced = np.concatenate([(factor/max(len(positives),1)) * positives, (factor/max(len(negatives),1) * negatives)])
  return balanced

def getRecommendation(userId):
  print('fetching user')
  user = db.getUser(userId)
  print('creating training examples')
  x_np, y_np = createTrainingExamplesFromUser(user)

  print('Loading models')
  model = Ridge(alpha=alpha, fit_intercept=True)

  model.fit(x_np, y_np)

  #metrics calculations
  metrics = {}
  score= model.score(x_np, y_np)
  if np.isnan(score):
    score = 0
  metrics['score'] = score
  predictions_train = model.predict(x_np)
  mae = mean_absolute_error(y_np, predictions_train)
  metrics['mae'] = mae
  metrics['n'] = len(x_np)
  print(metrics)
  del x_np, y_np, predictions_train

  #chunking to save memory
  print('Making predictions')
  predictions_list = []
  indexes = []
  poly = PolynomialFeatures(degree=degree, interaction_only=interaction_only)
  with pd.read_csv(DATASET_PATH, chunksize=CHUNK_SIZE, nrows=(popularity_heuristic_threshold if use_popularity_heuristic else None), usecols=(feature_names + ['id', 'name'])) as reader:
    for chunk in reader:
      #clean data
      #filtering only english tracks
      chunk = chunk[chunk['name'].apply(isEnglish)]
      # and dont predict songs which have been seen before
      print('before', len(chunk), end=' ')
      chunk = chunk[~chunk['id'].isin(user['addlist'])]
      chunk = chunk[~chunk['id'].isin(user['skiplist'])]
      print('after', len(chunk))
      indexes.extend(chunk.index.to_list())
      print('indexlength', len(indexes))
      print(indexes[:10])
      x_chunk = poly.fit_transform(chunk[feature_names])
      prediction_chunk = model.predict(x_chunk).reshape(len(x_chunk),)
      predictions_list.append(prediction_chunk)
  predictions = np.concatenate(predictions_list)

  del predictions_list
  #get recommendation
  recommendation, confidence = chooseNext(predictions, indexes, sampling_strategy)

  return {'recommendation': recommendation, 'metrics': metrics, 'confidence': confidence, 'weights': model.coef_.tolist()}

print('BRAIN LOADED')

# print(createTrainingExamplesFromUser(db.getUser('12175261097')))
# print(searchByName('abracadabra'))
# print(updateModelAndPredict('12175261097', '6epn3r7S14KUqlReYr77hA', 1))
# print(updateModelAndPredict('12175261097', '38DgNqC7TQkZ3Ih5Vz6K0Q', -1))
# print(getRecommendation('12175261097'))
