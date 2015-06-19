from io import BytesIO
import requests
import pandas as pd


def get_sheet(url, index_col = None):
  r = requests.get(url)
  data = r.content
  if index_col is not None:
    df = pd.read_csv(BytesIO(data), index_col=index_col)
  else:
    df = pd.read_csv(BytesIO(data))
  return df 
