from ooktest import *
import matplotlib.pyplot as plt
import pycanum.main as pycan

sys = pycan.Sysam("SP5")

# PARAMETRES EMISSION

techantSortie = 1e-3 # période d'échantillonnage en secondes
temissionBit = 1e-2
N = int(temissionBit/techantSortie) # nombre de points représentant 1 bit
(tensionMin, tensionMax) = (0, 5)
# message = input("Message à envoyer : ")
message = 'jellooo'
(start, end) = creationAccroches('a', 'z', 10)
(startMan, endMan) = (codageManchester(start), codageManchester(end))

signal = emission(message, tensionMin, tensionMax, N, startMan, endMan)

sys.config_sortie(1, techantSortie*1e6, signal) # en microsecondes et non périodique
sys.declencher_sorties(1, 0)

# PARAMETRES RECEPTION

techantEntree = 1e-3 # période d'échantillonnage en secondes
tempsReception = 5 # en secondes
nbpoints = int(tempsReception/techantEntree)
N_reception = int(temissionBit/techantEntree) # IDEALEMENT IMPAIR POUR MOSTCOMMON()
maxErreursMotif = int((N_reception*len(startMan))/10)

sys.config_entrees([2], [10]) # attention 10 V max
sys.config_echantillon(techantEntree*1e6, nbpoints) # période d'échantillonnage en microsecondes
sys.config_quantification(12)


# Emission/acquisition

sys.acquerir()
sys.declencher_sorties(1, 0)
sys.stopper_sorties(1, 0)

# Ce que l'on reçoit
temps = sys.temps()
tension = sys.entrees()
sys.fermer()


# Résultats

print(reception(tension, N_reception, startMan, endMan, maxErreursMotif))

# Ce qu'on envoie aux LEDs

t = [1.0]*len(signal)
c=1
for k in range(len(t)):
    t[k] = techantSortie*c
    c += 1

plt.figure()
plt.scatter(t, signal, label="SA1", s=1)
plt.xlabel("t (s)")
plt.ylabel("u (V)")
plt.grid()
plt.legend()

# Ce que l'on reçoit

plt.figure()
plt.scatter(temps[0], tension[0], label="EA2", s=1)
plt.xlabel("t (s)")
plt.ylabel("u (V)")
plt.grid()
plt.legend()
plt.show()
