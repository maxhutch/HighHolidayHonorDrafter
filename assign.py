#!/usr/bin/env python3

import pandas as pd
import numpy as np
from hungarian_algorithm.hungarian import *
from web_io import get_sheet
from conf import members_url, honors_url

honors = get_sheet(honors_url)
members = get_sheet(members_url, 0) 

""" Clean up! """
members['Tribe'] = members['Tribe'].fillna('Israel')
honors['Tribe'] = honors['Tribe'].fillna('Israel')
honors['Hebrew'] = honors['Type'] == 'Aliyah'


print(honors)
print(members)

rank = max(honors.shape[0], members.shape[0])
scores = np.zeros((rank, rank))

j = 0
trans = []
for name,mem in members.iterrows():
  trans.append(name)
  for i in range(honors.shape[0]):
    honor = honors.loc[i]
    if honor['Tribe'] != 'Israel' and mem['Tribe'] != honors.loc[i]['Tribe']:
      continue
    if honor['Hebrew'] and not mem['Hebrew']:
      continue
    scores[i, j] = 1.
  j = j + 1

#print(scores)
hung = Hungarian(scores, is_profit_matrix=True)
hung.calculate()

results = hung.get_results()
for res in results:
  if res[1] >= len(trans):
    break
  print("{:s} is assigned to {:s}".format(trans[res[1]], honors.loc[res[0]]['Name']))
print("Total score is {:f}".format(hung.get_total_potential()))

