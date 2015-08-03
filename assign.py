#!/usr/bin/env python3

import pandas as pd
import numpy as np
from hungarian_algorithm.hungarian import *
from web_io import get_sheet
from conf import members_url, honors_url, mhu_url, categories_url
from conf import override_url

honors = get_sheet(honors_url)
print("Read honors")
members = get_sheet(members_url) 
mhus = get_sheet(mhu_url)
cats_new = get_sheet(categories_url)
override = get_sheet(override_url)


""" Clean up! """
shabbat = False
members['Tribe'] = members['Tribe'].fillna('Israel')
members['Last Honor'] = members['Last Honor'].fillna(2013)
honors['Name'] = honors['Name'].fillna("Delete")
honors = honors[honors.Name != "Delete"]
honors['Weight'] = honors['Weight'].fillna(1.0)
honors['Tribe'] = honors['Tribe'].fillna('Israel')
honors['Hebrew'] = (honors['Type'] == 'Aliyah')
honors['Shabbat'] = honors['Shabbat'].fillna('Any')
mhus['Family service'] = mhus['Family service'].fillna(False)

cats_new = cats_new.fillna(0.0)
if shabbat:
  honors = honors[honors.Shabbat != 'Exclude']
else:
  honors = honors[honors.Shabbat != 'Only']

cats_new = cats_new.drop("Last honored", 1)

cats_d = {}
for cat in cats_new.columns.values:
  if cat == 'Name' or cat == 'Last honored':
    continue
  cats_d[cat] = [cats_new.iloc[0][cat] ,]
for i in range(2, cats_new.shape[0]):
  for cat in cats_new.columns.values:
    if cat == 'Name' or cat == 'Last honored':
      continue
    if cats_new.iloc[i][cat] == 1:
      cats_d[cat].append(cats_new.iloc[i]["Name"])
max_len = max([len(cats_d[k]) for k in cats_d])
for k in cats_d:
  while len(cats_d[k]) < max_len:
    cats_d[k].append("")

#print(cats_d["New Members"])
#print(cats_d["Does not come for HH"])
cats = pd.DataFrame(cats_d)
#print(cats)

print("Starting with {:d} members".format(members.shape[0]))


""" Remove overrides """
assignments = {}
honors_all = honors.copy()
for k in range(override.shape[0]):
  assignments[(override.iloc[k]["Honor"], override.iloc[k]["Service"])] = override.iloc[k]["Name"]
  members = members[members["Name"] != override.iloc[k]["Name"]]
  honors = honors[
             (honors["Name"] != override.iloc[k]["Honor"])
           | (honors["Service"] != override.iloc[k]["Service"])]

print("Now {:d} members".format(members.shape[0]))
""" Remove zero-score categories """
to_drop = []
for cat in cats.columns.values:
  if float(cats[cat][0]) > 0:
    continue
  to_drop.append(cat)   
  for name in list(cats[cat])[2:]:
    if name in list(members.Name):
      members = members[members["Name"] != name] 
for cat in to_drop:
  cats = cats.drop(cat, 1)

print("Down to {:d} members".format(members.shape[0]))

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

rank = max(honors.shape[0], mhus.shape[0])
scores_individual = np.zeros((members.shape[0], rank))
scores_mhu = np.zeros((rank, rank))

this_year = 2015

name_to_member = {}
cat_counts = {}
assigned_counts = {}
for cat in cats.columns.values:
  cat_counts[cat] = 0
  assigned_counts[cat] = 0
cat_counts["Three year"] = 0
cat_counts["Two year"] = 0
assigned_counts["Three year"] = 0
assigned_counts["Two year"] = 0


print("Scoring {:d} members".format(members.shape[0]))
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
    scores_individual[j, i] = honor["Weight"]

  if (this_year - mem['Last Honor'] == 3):
    mult = 3
    cat_counts["Three year"] += 1
  elif (this_year - mem['Last Honor'] == 2):
    mult = 2
    cat_counts["Two year"] += 1
  else:
    mult = 1.

  for cat in cats.columns.values:
    if mem.Name in list(cats[cat]):
      cat_counts[cat] = cat_counts[cat] + 1
      this_mult = float(cats[cat][0])
      if this_mult == 0:
        mult = 0
        break
      mult = max(this_mult, mult)

  scores_individual[j,:] *= mult

ii = 0
for i in range(mhus.shape[0]):
  mhu = mhus.iloc[i]
  for name in list(mhu)[1:]:
    if pd.isnull(name):
      break
    if name in name_to_member:
      scores_mhu[i,:] = np.maximum(scores_mhu[i,:], scores_individual[name_to_member[name],:])
  if not mhu["Family service"]:
    continue

  for j in range(honors.shape[0]):
    honor = honors.iloc[j]
    if honor.Service == "RH1" or honor.Service == "RH2" or honor.Service == "YK - Torah":
      scores_mhu[i,j] = 0.

print("Solving Hungarian for N={:d}".format(rank))
hung = Hungarian(scores_mhu, is_profit_matrix=True)
hung.calculate()
results = hung.get_results()

# Optimal outcome is the members with the highest maximum score being assigned to the maximal part
opt_potential = np.sum(np.sort(np.max(scores_mhu, axis=1))[-min(honors.shape[0],mhus.shape[0]):])

for res in results:
  if res[1] >= honors.shape[0] or res[0] >= mhus.shape[0]:
    continue
  winner = "No One"; best = 0
  for name in list(mhus.iloc[res[0]])[1:]:
    if (not pd.isnull(name)) and (name in name_to_member) and scores_individual[name_to_member[name], res[1]] > best:
      winner = name
      best = scores_individual[name_to_member[name], res[1]] 
  for cat in cats.columns.values:
    if winner in list(cats[cat]):
      assigned_counts[cat] = assigned_counts[cat] + 1
  if best == 3:
    assigned_counts["Three year"] += 1
  if best == 2:
    assigned_counts["Two year"] += 1

  #print("{:20s} is assigned to {:s} for {:s}".format(winner, honors.iloc[res[1]].Name, honors.iloc[res[1]].Service))
  assignments[(honors.iloc[res[1]].Name, honors.iloc[res[1]].Service)] = winner

print("Total score is {:f} of {:f}".format(hung.get_total_potential(), opt_potential))
for cat in list(cats.columns.values) + ["Three year", "Two year"]:
  print("{:20s}: {:3d} of {:3d} assigned".format(cat, assigned_counts[cat], cat_counts[cat]))

to_csv = []
for i in range(honors_all.shape[0]):
  honor = honors_all.iloc[i]
  to_csv.append((honor.Service, honor.Name, assignments[(honor.Name, honor.Service)] ))
final = pd.DataFrame(to_csv)
final.to_csv("./final_assignments.csv")

