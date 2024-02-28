import datetime
from professeur import Professeur
from cours import Cours
from edt import EDT
from edt_generator import EDT_GENERATOR, Ant
import asyncio

MIDI_LUNDI = [
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]

MIDI_MARDI = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]

MIDI_MERCREDI = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]

MIDI_JEUDI = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]

MIDI_VENDREDI = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]


PROF1 = [
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # Lundi 
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # Mardi
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # Mercredi
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # Jeudi
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # Vendredi
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]
PROF2 = [
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Lundi
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Mardi
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Mercredi
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Jeudi
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],  # Vendredi
    [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]
PROF3 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]
PROF4 = [
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Lundi
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mardi
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Mercredi
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Jeudi
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Vendredi
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]
PROF5 = [
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # Lundi
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # Mardi
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # Mercredi
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # Jeudi
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],  # Vendredi
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]
PROF6 = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Lundi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Mardi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Mercredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Jeudi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Vendredi
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Samedi
]

prof1 = Professeur(PROF1)
prof2 = Professeur(PROF2)
prof3 = Professeur(PROF3)
prof4 = Professeur(PROF4)
prof5 = Professeur(PROF5)
prof6 = Professeur(PROF6)

prof_midi_lundi = Professeur(MIDI_LUNDI, "Midi")
prof_midi_mardi = Professeur(MIDI_MARDI, "Midi")
prof_midi_mercredi = Professeur(MIDI_MERCREDI, "Midi")
prof_midi_jeudi = Professeur(MIDI_JEUDI, "Midi")
prof_midi_vendredi = Professeur(MIDI_VENDREDI, "Midi")

Cours(prof_midi_lundi, 1, name='Midi1', color='grey')
Cours(prof_midi_mardi, 1, name='Midi2', color='grey')
Cours(prof_midi_mercredi, 1, name='Midi3', color='grey')
Cours(prof_midi_jeudi, 1, name='Midi4', color='grey')
Cours(prof_midi_vendredi, 1, name='Midi5', color='grey')

print(Professeur.ALL)
# Cours(prof1, 3)
# Cours(prof1, 3)
# Cours(prof1, 3)
Cours(prof1, 3)
Cours(prof1, 2)
Cours(prof1, 2)

# Cours(prof2, 3)
# Cours(prof2, 3)
# Cours(prof2, 2)
Cours(prof2, 2)
Cours(prof2, 2)
Cours(prof2, 1)
Cours(prof2, 1)

# Cours(prof3, 2)
# Cours(prof3, 2)
Cours(prof3, 1.5)
Cours(prof3, 1)
Cours(prof3, 1.5)

# Cours(prof4, 2)
Cours(prof4, 2)
Cours(prof4, 1)
Cours(prof4, 1)

# Cours(prof5, 3)
# Cours(prof5, 3)
Cours(prof5, 1)
Cours(prof5, 1)

# Cours(prof6, 3.5)
Cours(prof6, 1)
Cours(prof6, 1)

debut = datetime.datetime.now()
async def main(): await EDT_GENERATOR.generate_edts(15, int(len(Cours.ALL) * 2.2))
ants = asyncio.run(main())
print("Temps d'execution total: ", datetime.datetime.now() - debut)

# for ant in ants[-3:]:
#     print(ant.edt.get_score())

# print('-------------------\n')

# max_phero = max([max(value) for value in EDT_GENERATOR.LEARNING_TABLE.values()])
# for key, value in EDT_GENERATOR.LEARNING_TABLE.items():
#     if max_phero in value:
#         print(key)
#print(f'max: {max_phero}-------------------\n')

ant = Ant(1, 0)
ant = asyncio.run(ant.visit(get_better=True))
print("Meilleur score:", ant.edt.get_score())


# V1
# NOTE: fourmie multi-thread, mais mauvaise gestion de la vision (inversement des proba), génération peut-etre pas optimale
# C'est étonnant que les fourmis soient si lentes:
#    - 1 fourmie = 0.15s;
#    - 10 fourmies = 1.6s;
#    - 50 fourmies = 7.5s;
#    - 100 fourmies = 18s;
#    - 200 fourmies = 32s;
#    - 500 fourmies = 1min 36s;
#    - 1000 fourmies = 2min 55s;
#    - 2000 fourmies = 6min 22s;

#    - 1 fourmie * 10 iterations = 1.5s;
#    - 1 fourmie * 50 iterations = 11s;
#    - 1 fourmie * 100 iterations = 22s;
#    - 1 fourmie * 200 iterations = 49s;
#    - 1 fourmie * 500 iterations = 2min 2s;
# lineaire Alors que multi thread ?

# Scores trouvées; pas forcément les meilleurs:
# 10, 100 -> ~ 80 en 3min
# 15, 80 -> ~ 79 en 3min
# 10, 150 -> ~ 80 en 3min 40
# 30, 50 -> 78 en 5.30min
# 15, 100 -> 77 en 4min 30

# V2 en async et amélioration vue: 50 fourmies en environ 5s
# 30, 100 -> 8min 18s

# 30, 5 - better -> 83.5 (p: 83.0072463768116) en 23s
# 100, 5 - better -> 79.5 (p: 83.07608695652173) en 1min 12s
# Conclusion 1: le get_better n'est pas super efficace

# 15, 10 - better -> 80.6 (p: 81.91666666666666) en 17s
# 30, 10 - better -> 77.8 (p: 84.16666666666666) en 33s
# 75, 10 - better -> 81.5 (p: 85.25362318840578) en 1min 20s


# V3: Correction de la diversité et du get better
# V4: Ajout de différentes fonctions de calcul de la proba des phéromones

# print('min:', min([len(elmt) for elmt in EDT_GENERATOR.LEARNING_TABLE.values()]))
# print('avg:', sum([len(elmt) for elmt in EDT_GENERATOR.LEARNING_TABLE.values()]) / len(EDT_GENERATOR.LEARNING_TABLE))
# print('max:', max([len(elmt) for elmt in EDT_GENERATOR.LEARNING_TABLE.values()]))

# V5: Batching des fourmis (après utilisation temps qui semble être divisé par 2)
# 1 fourmie     | 0.22s       | 1 * 1f
# 10 fourmies   | 0.78s       | 1 * 10f
# 50 fourmies   | 4s          | 5 * 10f
# 100 fourmies  | 9s          | 10 * 10f
# 200 fourmies  | 14s         | 20 * 10f
# 500 fourmies  | 46s         | 50 * 10f
# 1000 fourmies | 1min 41s    | 100 * 10f
# 2000 fourmies | 7min 29s    | 200 * 10f ?? 

# Observation du facteur de diversité ):

# Apliqué sur P et V avec mean (75 fourmies, 10 itérations):
# 0   -> 83.55
# 0.1 -> 83.54
# 0.2 -> 82.80
# 0.3 -> 82.30
# 0.4 -> 82.14
# 0.5 -> 82.50
# 0.6 -> 82.80
# 0.7 -> 82.26
# 0.8 -> 82.80
# 0.9 -> 85.67, 82.95, 84.14
# 1   -> 82.64

# Apliqué sur P et V avec mean (200 fourmies, 10 itérations):
# 0   -> 83.96, 83.13, 84
# 0.1 -> 85, 84.1, 84.52
# 0.9 -> 83.83, 82.87, 82.71
# 1   -> 77 ??

# Apliqué sur V avec mean (200 fourmies, 10 itérations):
# 0   -> 83.16, 82.29, 83.22
# 0.1 -> 84.09, 83.74, 83.80
# 0.9 -> 82.71, 82.54
# 1   -> 85.16, 82.64, 86.44

# Apliqué sur V avec mean (50 fourmies, 50 itérations):
# 0 -> 82.96, 82.87
# 1 -> 84.67, 84.87

# Apliqué sur V avec mean (100 fourmies, 50 itérations):
# 0 -> 85.41, 83.42
# 1 -> 85.69, 84.12

# Il y a un soucis avec le get better, des fois il regressse

main_params = [(50, 20)]
diversity_param = [0, 0.1, 0.5, 0.9, 1]
stats = {}
"""{ main_param: { diversity: [{'score': int, 'time': timedelta, 'total_created_edt': int, 'total_distinct_edt': int, 'avg_try_by_distinct_edt': float, 'max_nb_try': int, 'min_nb_try': int} * 3] } }"""
# for main_param in main_params:
#     for diversity in diversity_param:
#         for _ in range(3):
#             debut = datetime.datetime.now()
#             print(f'({main_param[0]}, {main_param[1]}) - {diversity} -> ', end='')
#             EDT_GENERATOR.DIVERSITY_COEF = diversity
#             EDT_GENERATOR.reset()

#             async def main(): await EDT_GENERATOR.generate_edts(main_param[0], main_param[1])
#             ants = asyncio.run(main())
#             best_ant = Ant(1, 0)
#             best_ant = best_ant.visit(get_better=True)
#             print(f'{best_ant.edt.get_score()}')
#             if main_param not in stats:
#                 stats[main_param] = {}

#             if diversity not in stats[main_param]:
#                 stats[main_param][diversity] = []

#             stats[main_param][diversity].append({
#                 'score': best_ant.edt.get_score(),
#                 'time': datetime.datetime.now() - debut,
#                 'total_created_edt': sum(EDT_GENERATOR.CREATED_EDT.values()),
#                 'total_distinct_edt': len(EDT_GENERATOR.CREATED_EDT.keys()),
#                 'avg_try_by_distinct_edt': sum(EDT_GENERATOR.CREATED_EDT.values()) / len(EDT_GENERATOR.CREATED_EDT),
#                 'max_nb_try': max(EDT_GENERATOR.CREATED_EDT.values()),
#                 'min_nb_try': min(EDT_GENERATOR.CREATED_EDT.values()),
#             })

# print(stats)
# print('\n\n')
# ziped = {}
# for data in EDT_GENERATOR.LEARNING_TABLE:
#     ziped[data] = {'moy': sum(EDT_GENERATOR.LEARNING_TABLE[data]) / len(EDT_GENERATOR.LEARNING_TABLE[data]), 'max': max(EDT_GENERATOR.LEARNING_TABLE[data]), 'min': min(EDT_GENERATOR.LEARNING_TABLE[data])}

# ziped_sort = sorted(list(ziped.keys()), key=lambda x: x[1] * 100 + x[2])
# for data in ziped_sort:
#     print(data, ziped[data])
# print(EDT_GENERATOR.CREATED_EDT)
# for main_param, diversities in stats.items():
#     print(f'\n\n{main_param}:')
#     for diversity, values in diversities.items():
#         print(f'\n{diversity}:')
#         for value in values:
#             print(f'\n{value}')

# # En retirant les moins bonnes solutions
# On remarque que avec un grand nombre de fourmies + un grand nombre d'itérations, la diversité a un meilleur impact (à 1)
# On remarque qu'une diversité de 0.1 est la plus efficace quand peu de répétitions
# On remarque qu'avec un grand nombre de répétitions, la diversité à 0.5 est la plus efficace
# ---> Meilleurs stats: (30, 20) à d = 1 -> 84.22, 84.14, 83.26     # Ancien
# (30, 20):
            # 0 -> 82.68, 82.29, 82.26
            # 0.1 -> 83.64, 83.08, 82.51
            # 0.5 -> 83.23, 83.19, 82.40
            # 1 -> 82.88, 83.83, 82.80

# En gardant les moins bonnes solutions mais sans en ajouter

print(ant.edt.jsonify())
print(ant.edt)
print(ant.edt.get_score())
print(len(ant.edt.placed_cours))
print('-------------------\n')
print([(cours, cours.professeur) for cours in ant.placed_courses if cours not in ant.edt.placed_cours])

print()
