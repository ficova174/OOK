import numpy as np
import Levenshtein

# Partie émission

def codageBinaire(nombre:int, taillePaquet:int) -> str:  # attention on lit de gauche à droite
    nombreBin = ''
    while nombre > 0:
        nombreBin += str(nombre % 2)
        nombre //= 2
    while len(nombreBin) < taillePaquet:  # cas code ASCII trop faible, on veut toutes nos lettres sur 8 valeurs pour le décodage
        nombreBin += '0'
    return nombreBin

def encodage(message:str, taillePaquet:int) -> str:
    # on le code en chaine de caractères pour utiliser .find() dans le décodage
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre)  # ASCII décimal (int)
        messageBin += codageBinaire(lettre, taillePaquet)  # car codage base 4 renvoit une liste
    return messageBin

def creationAccroche(lettre:str) -> str:
    accroche = ''
    for k in range(8):  # car 8 valeurs possibles de id
        id = codageBinaire(k, 3)  # Sera codé sur 3 bits (8 valeurs possibles)
        accroche += encodage(lettre, 8) + id  # Chaque accroche est répétée et identifiée
    return accroche

# Codage Manchester (IEEE 802.3)
def codageManchester(messageBin:str) -> str:
    clock = [k%2 for k in range(1, 2*len(messageBin)+1)]  # On commence à 1 pour que clock commence par 1
    messageMan = ""
    for k in range(len(messageBin)):
        for i in range(2*k, 2*(k+1)):
            if int(messageBin[k]) != clock[i]:
                messageMan += "1"
            else:
                messageMan += "0"
    return messageMan

def ook(messageMan:str, tensionMin:int, tensionMax:int, N:int) -> list:
    tension = []
    for byte in messageMan:
        if byte == '0':
            tension += [tensionMin]*N
        elif byte == '1':
            tension += [tensionMax]*N
        else:
            print('Erreur : le message binaire est corrompu, une valeur autre que 0 et 1 a été trouver')
            return []
    return np.array(tension, dtype=np.float32)

def emission(message:str, tensionMin:int, tensionMax:int, N:int, startMan:str, endMan:str) -> list:
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan
    return ook(messageMan, tensionMin, tensionMax, N)


# Partie réception
# ATTENTION le message sera à l'envers car les infos envoyées en premières seront reçues en première

def codageBaseDix(messageBin:str) -> int:  # ATTENTION message à l'endroit (droites petites puissances) comme dit précédemment
    asciiDecimal = 0
    for k in range(len(messageBin)):
        asciiDecimal += int(messageBin[k]) * (2 ** k)  # A VERIFIER (n-k) au lieu de k
    return asciiDecimal

def mostCommon(liste:list, type:str):
    dict = {}
    for element in liste:
        if element not in dict:
            dict[element] = 1
        else:
            dict[element] += 1
    
    elementMax = liste[0]
    nbApparitionMax = 0
    for element in dict:
        if dict[element] > nbApparitionMax:
            elementMax = element
            nbApparitionMax = dict[element]
    
    if type == "float":
        return elementMax
    elif type == "int":
        return int(elementMax)
    elif type == "string":
        return str(elementMax)
    else:
        print("Mauvais datatype sélectionné : choisir int, float ou str")

# La fonction ne fait pas des paquets parfait mais elle découpe la liste de la manière la plus optimale possible
def decoupeListe(dividedSignal:list, tension:list, size:int):
    lenT = len(tension)
    if lenT <= size:
        dividedSignal.append(tension)
    else:
        lenT2 = lenT//2
        decoupeListe(dividedSignal, tension[:lenT2], size)
        decoupeListe(dividedSignal, tension[lenT2:], size)

def voltageToBinary(tension:list, N_reception:int, nb_bits:int) -> str:
    signalBinMan = ''
    dividedSignal = [] # On utilise l'effet de bord
    size = N_reception * nb_bits
    decoupeListe(dividedSignal, tension, size)
    for morceau in dividedSignal:
        tensionMax = np.max(morceau)
        tensionMin = np.min(morceau)

        if tensionMax == 0:
            signalBinMan += '0'*len(morceau)
        elif (tensionMax - tensionMin) < 0.5:
            print(f'Attention le morceau CODANT {morceau} dans voltageToBinary ne possède pas de variation de tension')
            signalBinMan += '0'*len(morceau) # Arbitraire on aurait pu prendre 1
        else:
            morceau = morceau/tensionMax
            min = tensionMin/tensionMax
            milieu = (1 + min)/2
            for i in range(len(morceau)):
                if morceau[i] > milieu:  # Et si notre tension tombe pile sur le milieu ??
                    signalBinMan += '1'
                else:
                    signalBinMan += '0'
    return signalBinMan

def chercheMotifLevenshtein(signalBinMan:str, motif:str, maxErreursMotif:int, N_reception:int) -> list:
    # Calcule la distance de Levenshtein entre accrocheBinMan envoyé et accrocheBinMan reçue
    # motif = motifBinManDouble
    maxErreurs = maxErreursMotif*N_reception # car les id d'accroche ont le droit d'avoir des 
    lenAccroche = len(motif) + 3*N_reception

    listeIndicesAccroche = []
    for indice in range(len(signalBinMan) - lenAccroche): # on enleve taille dernière accroche
        if Levenshtein.distance(signalBinMan[indice:indice+lenAccroche], motif) <= maxErreurs:
            listeIndicesAccroche.append(indice)
    return listeIndicesAccroche

""" def chercheMotifErreurs(signalBinMan:list, motif:list, maxErreursMotif:int) -> list:
    # motif = motifBinManDouble
    if maxErreursMotif < 1 or type(maxErreursMotif) != int or maxErreursMotif >= len(motif):
        print('Erreur valeur maxErreursMotif')
        return -1
    
    listeIndicesAccroche = []
    for indice in range(len(signalBinMan)):
        compteurErreurs = 0
        k = 0
        while (compteurErreurs < maxErreursMotif) and (k < len(motif)) and (indice <= len(signalBinMan) - len(motif)):
            if signalBinMan[indice+k] != motif[k]:
                compteurErreurs += 1
            k += 1
        if (k == len(motif)) and (compteurErreurs < maxErreursMotif):
            listeIndicesAccroche.append(indice)
    return listeIndicesAccroche """

def position(signalBinMan:str, N_reception:int, motif:str, role:str, maxErreursMotif:int) -> int:
    positionAccroche = []
    N_reception8 = 8*N_reception
    N_reception11 = 11*N_reception
    listeIndicesAccroche = chercheMotifLevenshtein(signalBinMan, motif, maxErreursMotif, N_reception)
    
    if listeIndicesAccroche == []:
        print(f"Erreur pas d'accroche {role} trouvée")
        return -1
    for indiceAccroche in listeIndicesAccroche:
        accrocheID = signalBinMan[indiceAccroche+N_reception8:indiceAccroche+N_reception11]
        idBin = ''
        for indiceID in range(0, 2*N_reception, N_reception):
            idBin += mostCommon(accrocheID[indiceID:indiceID+N_reception], 'int')
        id = codageBaseDix(idBin)
        if 0 <= id < 8:
            if role == 'start':
                start = indiceAccroche + (8 - id)*N_reception11  # 11 = taille de chaque répétition avec son id, 8 = nombre de répétition de l'accroche
                positionAccroche.append(start)
            elif role == 'end':
                end = indiceAccroche - id*N_reception11
                positionAccroche.append(end)
            else:
                print(f'Erreur : {role} n\'est pas un role valide (start ou end)')
                return -1
        else:
            print('Erreur : id pas dans intervalle (pas grave)')
    return mostCommon(positionAccroche, 'int') # Donne l'élément le plus commun de la liste

def detectionAccroche(signalBinMan:str, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    # rajouter décodage du code correcteur + si trop de bruit, redemander l'envoie des données
    startDoublonsMan = ''
    endDoublonsMan = ''

    for k in range(len(startMan)):
        startDoublonsMan += N_reception * startMan[k]
        endDoublonsMan += N_reception * endMan[k]
    
    motifStart = startDoublonsMan[:N_reception*8]
    motifEnd = endDoublonsMan[:N_reception*8]

    with open("start.txt", "w", encoding="utf-8") as f:
        for element in motifStart:
            f.write(f"{element}")

    start = position(signalBinMan, N_reception, motifStart, 'start', maxErreursMotif)
    end = position(signalBinMan, N_reception, motifEnd, 'end', maxErreursMotif)

    return signalBinMan[start:end]

def demodulation(tension:list, N_reception:int, nb_bits:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    tension = tension[0] # super bizarre sys.entree me renvoie une liste avec une seule liste tension à l'intérieur (liste de liste)
    tension = tension[::-1] # pour remettre le message à l'endroit
    tension = np.array([np.round(element, 1) for element in tension]) # on arrondit les éléments pour la suite
    
    with open("tension.txt", "w", encoding="utf-8") as f:
        for element in tension:
            f.write(f"{element}\n")

    signalBinMan = voltageToBinary(tension, N_reception, nb_bits)

    with open("acqui.txt", "w", encoding="utf-8") as f:
        for element in signalBinMan:
            f.write(f"{element}\n")

    messageBinManDouble = detectionAccroche(signalBinMan, N_reception, startMan, endMan, maxErreursMotif) # chaque bit est répété N_reception fois par rapport au message Man envoyé, on veut enlever les doublons

    messageBinMan = '' # on enlève les doublons
    valeursBit = [int(messageBinManDouble[0])]
    for indice in range(1, len(messageBinManDouble)):
        if indice % N_reception == 0:
            messageBinMan += mostCommon(valeursBit, 'str') # Donne l'élément le plus commun de la liste
            valeursBit = [int(messageBinManDouble[indice])]
        else:
            valeursBit.append(int(messageBinManDouble[indice]))
    return messageBinMan

def decodageMan(messageBinMan:str) -> str:
    messageBin = ''
    for k in range(0, len(messageBinMan), 2): # car un 0 est codé par N points et pas de 2 car on saute la transition
        if messageBinMan[k] == '0': # transition 0 --> 1
            messageBin += '1'
        else: # transition 1 --> 0
            messageBin += '0'
    return messageBin

def decodageASCII(messageBin:str) -> str:
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tension:list, N_reception:int, nb_bits:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    return decodageASCII(decodageMan(demodulation(tension, N_reception, nb_bits, startMan, endMan, maxErreursMotif)))
