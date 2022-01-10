import pandas as pd
df = pd.read_csv('dataset/tracks.csv').sort_values(by=['popularity'], ascending=False)
df.to_csv('dataset/tracksOrderedByPopularity.csv')