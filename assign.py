#!/usr/bin/env python3

import pandas as pd
import numpy as np
from hungarian_algorithm.hungarian import *
from web_io import get_sheet
from conf import members_url, honors_url

honors = get_sheet(honors_url)
members = get_sheet(members_url) 

""" Clean up! """
shabbat = False
members['Tribe'] = members['Tribe'].fillna('Israel')
honors['Name'] = honors['Name'].fillna("Delete")
honors = honors[honors.Name != "Delete"]
honors['Tribe'] = honors['Tribe'].fillna('Israel')
honors['Hebrew'] = (honors['Type'] == 'Aliyah')
honors['Shabbat'] = honors['Shabbat'].fillna('Any')
if shabbat:
  honors = honors[honors.Shabbat != 'Exclude']
else:
  honors = honors[honors.Shabbat != 'Only']

print(honors)
print(members)

rank = max(honors.shape[0], members.shape[0])
scores = np.zeros((rank, rank))

this_year = 2015
year_scale = 2

for j in range(members.shape[0]):
  i = 0
  mem = members.iloc[j]
  for i in range(honors.shape[0]):
    honor = honors.iloc[i]
    if honor['Tribe'] != 'Israel' and mem['Tribe'] != honor['Tribe']:
      continue
    if honor['Hebrew'] and not mem['Hebrew']:
      continue
    scores[j, i] = 1.
  scores[j,:] *= (this_year - mem['Last Honor']) * year_scale
  if this_year - mem['Joined'] <= 1:
    scores[j,:] *= year_scale

print(scores)
hung = Hungarian(scores, is_profit_matrix=True)
hung.calculate()

results = hung.get_results()
# Optimal outcome is the members with the highest maximum score being assigned to the maximal part
opt_potential = np.sum(np.sort(np.max(scores, axis=1))[-min(honors.shape[0],members.shape[0]):])

for res in results:
  if res[1] >= honors.shape[0] or res[0] >= members.shape[0]:
    continue
  print("{:20s} is assigned to {:s} for {:s}".format(members.iloc[res[0]].Name, honors.iloc[res[1]].Name, honors.iloc[res[1]].Service))
print("Total score is {:f} of {:f}".format(hung.get_total_potential(), opt_potential))

