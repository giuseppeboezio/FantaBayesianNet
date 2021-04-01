from ScrapingPlayer import ScrapingPlayer
from ScrapingPlayer import Player
from ScrapingPlayer import PlayerEncoder
import pandas as pd
import numpy as np

# -------------------------------------------------------------------------------------------- #
# ------------------------- URLs to GET DATA for 6 FOOTBALL PLAYERS -------------------------- #
# -------------------------------------------------------------------------------------------- #

urlTmPlayers = list()
urlFgPlayers = list()
namePlayers = list()
statsPlayers = list()


urlTmPlayers.append("https://www.transfermarkt.it/luis-muriel/leistungsdaten/spieler/119228/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=945")

urlTmPlayers.append("https://www.transfermarkt.it/ciro-immobile/leistungsdaten/spieler/105521/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=929")

urlTmPlayers.append("https://www.transfermarkt.it/simy/leistungsdaten/spieler/194549/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=968")

urlTmPlayers.append("https://www.transfermarkt.it/hirving-lozano/leistungsdaten/spieler/316889/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=746")

urlTmPlayers.append("https://www.transfermarkt.it/alvaro-morata/leistungsdaten/spieler/128223/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=987")

urlTmPlayers.append("https://www.transfermarkt.it/zlatan-ibrahimovic/leistungsdaten/spieler/3455/saison/2020/plus/1#IT1")
urlFgPlayers.append("http://www.fantagiaveno.it/calciatori.asp?id=975")


# get raw data for each player
for i in range(len(urlTmPlayers)):

    player = ScrapingPlayer(urlTmPlayers[i], urlFgPlayers[i])
    namePlayer, statsPlayer = player.getData()

    namePlayers.append(namePlayer)
    statsPlayers.append(statsPlayer.sort_values(by=['matchday']))



# -------------------------------------------------------------------------------------------- #
# --------------------------------------- PREPROCESSING -------------------------------------- #
# -------------------------------------------------------------------------------------------- #

# compute deployability setting it True for at most 3 players in each matchday

# build a dict containing scores in each matchday that are not 'sv' and are at least 6
gradesMatchday = dict.fromkeys(range(1, max(statsPlayers[0]['matchday'])+1), [])
for i in range(len(statsPlayers)):
    for matchday, score in zip(statsPlayers[i]['matchday'], statsPlayers[i]['score']):
        if score >= 6 and np.isnan(score)==False:
            gradesMatchday[matchday] = gradesMatchday[matchday] + [Player(i,score)]

# order each list of scores in decreasing way and take at most 3 values
for values in gradesMatchday.values():
    values.sort(reverse=True)
    if len(values) > 3:
        del values[3:]

# compute deployability for each player
for i in range(len(statsPlayers)):
    deployability = list()
    for matchday in statsPlayers[i]['matchday']:
        if Player(i,None) in gradesMatchday[matchday]:
            deployability.append(True)
        else:
            deployability.append(False)
    statsPlayers[i]['deployability'] = deployability

import json
print(json.dumps(gradesMatchday, indent=4, cls=PlayerEncoder))

# preprocess columns needed
for statPlayer in statsPlayers:

    # remove postponed matches
    statPlayer.drop(statPlayer[statPlayer.postponed == True].index, inplace=True)

    # change available in True/False
    statPlayer['available'] = statPlayer['available'].apply(lambda x : True if x == 'Available' else False)

    # change goal in True/False
    statPlayer['goal'] = statPlayer['goal'].apply(lambda x: True if x > 0 else False)

    # change assist in True/False
    statPlayer['assist'] = statPlayer['assist'].apply(lambda x: True if x > 0 else False)

    # change minutes into ranges [0-15], [16-45], [46-90]
    bins = [0, 16, 46, 95]
    labels = ['0-15', '16-45', '46-90']
    statPlayer['time_range'] = pd.cut(statPlayer['minutes'], bins=bins, labels=labels, right=False)

    # change scores into sv, [<=5.5], [6-7], [7.5-9], [>=9.5]
    statPlayer['score'].fillna(value=-5, inplace=True)
    bins = [-5, -4, 6, 7.5, 9.5, 25]
    labels = ['sv', '<=5.5', '6-7', '7.5-9', '>=9.5']
    statPlayer['grade_range'] = pd.cut(statPlayer['score'],  bins=bins, labels=labels, right=False)

# save only needed stats into a csv
for namePlayer, statPlayer in zip(namePlayers, statsPlayers):
    variables = ['matchday','grade_range', 'goal', 'assist', 'yellow_card', 'red_card', 'available', 'starter', 'time_range', 'difficulty_match', 'deployability']
    statPlayer[variables].to_csv('../data/stats_'+namePlayer+'.csv', index=False)
