from ook import *
import matplotlib.pyplot as plt
import pycanum.main as pycan

sys = pycan.Sysam("SP5")

# PARAMETRES EMISSION

techantSortie = 1e-4  # période d'échantillonnage en secondes
temissionBit = 5e-3
N = int(temissionBit/techantSortie)  # nombre de points représentant 1 bit
(tensionMin, tensionMax) = (0, 5)
# message = input("Message à envoyer : ")
message = 'jellooo'
startMan = codageManchester(creationAccroche('a'))
endMan = codageManchester(creationAccroche('z'))

signal = emission(message, tensionMin, tensionMax, N, startMan, endMan)
print(signal)

sys.config_sortie(1, techantSortie*1e6, signal)  # en microsecondes et non périodique
sys.declencher_sorties(1, 0)

# PARAMETRE RECEPTION

techantEntree = 15e-6  # période d'échantillonnage en secondes
tempsReception = 2.5  # en secondes
nbpoints = int(tempsReception/techantEntree)
N_reception = int(temissionBit/techantEntree) # IDEALEMENT IMPAIR POUR MOSTCOMMON()

sys.config_entrees([2], [10])  # attention 10 V max
sys.config_echantillon(techantEntree*1e6, nbpoints)  # période d'échantillonnage en microsecondes
sys.config_quantification(12)


# Emission/acquisition

sys.acquerir()
sys.declencher_sorties(1, 0)
sys.stopper_sorties(1, 0)

# Ce que l'on reçoit
temps = sys.temps()
tensions = sys.entrees()
sys.fermer()


# Résultats

demodule = demodulation(tensions, N_reception, 4, startMan, endMan)
print(demodule)
decode = decodageMan(demodule)
print(decode)
deascii = decodageASCII(decode)
print(deascii)

print(reception(tensions, N_reception, 4, startMan, endMan))

# Ce qu'on envoie aux LEDs

t = [1]*len(signal)
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
plt.scatter(temps[0], tensions[0], label="EA2", s=1)
plt.xlabel("t (s)")
plt.ylabel("u (V)")
plt.grid()
plt.legend()
plt.show()
