#!/usr/bin/env python3

import pandas as pd
import numpy as np
from hungarian_algorithm.hungarian import *
from web_io import get_sheet
from conf import members_url, honors_url, mhu_url, categories_url
from conf import override_url

honors = get_sheet(honors_url)
members = get_sheet(members_url) 
mhus = get_sheet(mhu_url)
cats = get_sheet(categories_url)
override = get_sheet(override_url)


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
print(cats)
print(cats.columns.values)
print(mhus)
name_to_mhu = {}
for i in range(mhus.shape[0]):
  mhu = mhus.iloc[i]
  for name in list(mhu)[1:]:
    name_to_mhu[name] = i
i = mhus.shape[0]
for name in list(members.Name):
  if name in name_to_mhu:
    continue
  name_to_mhu[name] = i
  mhus = mhus.append(pd.DataFrame([{"Family service" : False, "M1": name},]),ignore_index=True)
  i = i + 1
print(mhus)

rank = max(honors.shape[0], mhus.shape[0])
scores_individual = np.zeros((members.shape[0], rank))
scores_mhu = np.zeros((rank, rank))

this_year = 2015

name_to_member = {}
for j in range(members.shape[0]):
  i = 0
  mem = members.iloc[j]
  name_to_member[mem.Name] = j
  for i in range(honors.shape[0]):
    honor = honors.iloc[i]
    if honor['Tribe'] != 'Israel' and mem['Tribe'] != honor['Tribe']:
      continue
    if honor['Hebrew'] and not mem['Hebrew']:
      continue
    scores_individual[j, i] = 1.

  for cat in cats.columns.values:
    if mem.Name in list(cats[cat]):
      scores_individual[j,:] *= float(cats[cat][0])
  if this_year - mem['Joined'] <= 1:
    scores_individual[j,:] *= float(cats["New Members"][0])
  elif (this_year - mem['Last Honor'] == 3):
    scores_individual[j,:] *= 3
  elif (this_year - mem['Last Honor'] == 2):
    scores_individual[j,:] *= 2
  if mem.Name in list(override["Name"]):
    for k in range(override.shape[0]):
      if override.iloc[k]["Name"] == mem.Name:
        over_honor = override.iloc[k]["Honor"]
        over_service = override.iloc[k]["Service"]
    for i in range(honors.shape[0]):
      honor = honors.iloc[i]
      if honor["Name"] == over_honor and honor["Service"] == over_service:
        print("Manually assigning {:s} to {:s} at {:s}".format(mem.Name, over_honor, over_service))
        scores_individual[j,i] = 1000


for i in range(mhus.shape[0]):
  mhu = mhus.iloc[i]
  for name in list(mhu)[1:]:
    if pd.isnull(name):
      break
    scores_mhu[i,:] = np.maximum(scores_mhu[i,:], scores_individual[name_to_member[name],:])

print(scores_individual)
print(scores_mhu)
hung = Hungarian(scores_mhu, is_profit_matrix=True)
hung.calculate()

results = hung.get_results()
# Optimal outcome is the members with the highest maximum score being assigned to the maximal part
opt_potential = np.sum(np.sort(np.max(scores_mhu, axis=1))[-min(honors.shape[0],mhus.shape[0]):])

assignments = {}
for res in results:
  if res[1] >= honors.shape[0] or res[0] >= mhus.shape[0]:
    continue
  winner = "No One"; best = 0
  for name in list(mhus.iloc[res[0]])[1:]:
    if (not pd.isnull(name)) and scores_individual[name_to_member[name], res[1]] > best:
      winner = name
      best = scores_individual[name_to_member[name], res[1]] 
  print("{:20s} is assigned to {:s} for {:s}".format(winner, honors.iloc[res[1]].Name, honors.iloc[res[1]].Service))
  assignments[(honors.iloc[res[1]].Name, honors.iloc[res[1]].Service)] = winner

print("Total score is {:f} of {:f}".format(hung.get_total_potential(), opt_potential))
to_csv = []
for i in range(honors.shape[0]):
  honor = honors.iloc[i]
  to_csv.append((honor.Service, honor.Name, assignments[(honor.Name, honor.Service)] ))
final = pd.DataFrame(to_csv)
final.to_csv("./final_assignments.csv")
  
  

