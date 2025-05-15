import numpy as np
from bitarray import bitarray

# Partie émission

def codageBinaire(nombre:int, taillePaquet:int) -> str:
    """
    nombre décimal -> nombre en binaire
    attention on code de gauche à droite (petites puissances à gauche)
    """
    nombreBin = ''
    while nombre > 0:
        nombreBin += str(nombre % 2)
        nombre //= 2
    while len(nombreBin) < taillePaquet: # on veut une taille fixe, on ajoute des 0
        nombreBin += '0'
    return nombreBin

def encodage(message:str, taillePaquet:int) -> str:
    """
    message texte (str) -> message en binaire (str)
    on demande la taille des paquets car on utilisera cette fonction pour coder des strings de longueur variable (accroche et ID)
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre, taillePaquet)
    return messageBin

def creationAccroche(lettre:str) -> str:
    """
    on créée une succesion improbable
    on lui donne un identifiant pour estimer le début du message (fonction detectionAccroche())
    """
    accroche = ''
    for k in range(8): # car 8 valeurs possibles de id
        id = codageBinaire(k, 3) # id codé sur 3 bits (8 valeurs possibles)
        accroche += encodage(lettre, 8) + id # accroche est répétée et possède un identifiant unique
    return accroche

# Codage Manchester (IEEE 802.3)
def codageManchester(messageBin:str) -> str:
    """
    pour synchroniser l'émetteur et le récepteur (savoir combien de 0 ou de 1 on reçoit d'affilé) on utilise le codage Manchester
    le message codé est synchrone, il contient l'horloge en lui en plus du message
    pour chaque bit du message, l'horloge fait une transition (donc deux valeurs)
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    horloge = [k%2 for k in range(1, 2*len(messageBin)+1)] # On commence à 1 pour que l'horloge commence par 1
    messageMan = ""
    for indiceBit in range(len(messageBin)):
        for indiceHorloge in range(2*indiceBit, 2*(indiceBit+1)):
            if int(messageBin[indiceBit]) != horloge[indiceHorloge]:
                messageMan += "1"
            else:
                messageMan += "0"
    return messageMan

def ook(messageMan:str, tensionMin:int, tensionMax:int, N:int) -> list:
    """
    transforme le message codé (Manchester) en valeurs de tension pour les LEDS
    on utilise la modulation on-off keying (OOK)
    """
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
    messageMan = startMan + codageManchester(encodage(message, 8)) + endMan # accroches ajoutées au message
    return ook(messageMan, tensionMin, tensionMax, N)

# Partie réception

def codageBaseDix(byte:str) -> int:
    """
    nombre binaire -> nombre décimal
    attention on code de gauche à droite (petites puissances à gauche)
    """
    asciiDecimal = 0
    for bit in range(len(byte)):
        asciiDecimal += int(byte[bit]) * (2 ** bit) # A VERIFIER (n-k) au lieu de k
    return asciiDecimal

def mostCommon(liste:list, type:str):
    """
    trouve l'élément le plus commun d'une liste
    on peut choisir le datatype renvoyé
    """
    if liste == []:
        print('Erreur : la liste est vide')
        return -1
    
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
    elif type == "str":
        return str(elementMax)
    else:
        print("Mauvais datatype sélectionné : choisir int, float ou str")

def decoupeListe(dividedSignal:list, tension:list, size:int):
    """
    découpe la liste des tension reçues en morceau de tailles prédéfinis
    la fonction ne fait pas des paquets parfait mais elle découpe la liste de la manière la plus optimale possible
    elle fonction en utilisant l'effet de bord des listes
    """
    lenT = len(tension)
    if lenT <= size:
        dividedSignal.append(tension)
    else:
        lenT2 = lenT//2
        decoupeListe(dividedSignal, tension[:lenT2], size)
        decoupeListe(dividedSignal, tension[lenT2:], size)

def voltageToBinary(tension:list, N_reception:int) -> str:
    """
    cette fonction normalise les valeurs de tensions reçues
    on découpe la liste tension car des variations de luminosité ambiante rendraient la fonction inopérante
    le principal défi est d'avoir des variations importantes dans chacun des morceaux sinon on perd de l'information
    la taille des morceaux dépend de son nombre de bits et de la fréquence d'échantillonnage
    """
    signalBinMan = ''
    dividedSignal = []
    nb_bits = 4 # expérimentalement on ne voit jamais plus de 2 bits valant 0 ou 1 émis d'affilé
    size = N_reception * 2 * nb_bits # car Manchester double la taille du message
    decoupeListe(dividedSignal, tension, size)

    for morceau in dividedSignal:
        tensionMax = np.max(morceau)
        tensionMin = np.min(morceau)

        if tensionMax == 0:
            signalBinMan += '0'*len(morceau)
        elif (tensionMax - tensionMin) < 0.5:
            print(f'Attention le morceau {morceau} dans voltageToBinary ne possède pas de variation de tension')
            signalBinMan += '0'*len(morceau) # Arbitraire on aurait pu prendre 1
        else:
            morceau = morceau/tensionMax
            min = tensionMin/tensionMax
            milieu = (1 + min)/2
            for i in range(len(morceau)):
                if morceau[i] > milieu:
                    signalBinMan += '1'
                else:
                    signalBinMan += '0'
    return signalBinMan

def chercheIndicesAccroche(signalBinMan:str, motif:str, maxErreursMotif:int) -> list:
    """
    on cherche l'accroche, or celle-ci n'a pas été transmise parfaitement
    on doit alors accepter un certains nombre d'erreurs dans le motif de l'accroche (id pas de problème)
    on utilise une méthode inspirée de la distance de Hamming pour connaitre ce nombre d'erreurs
    on renvoie la liste des indices de début des motifs avec autant ou moins d'erreurs que maxErreurMotif
    chaque bit est répété N_reception fois (la période d'échantillonage)
    """
    # motif = motifBinMan
    listeIndicesAccroche = []
    motifBits = bitarray(motif)
    for indice in range(len(signalBinMan)-len(motif)):
        signalBits = bitarray(signalBinMan[indice:indice+len(motif)])
        nombreErreurs = (signalBits ^ motifBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursMotif:
            listeIndicesAccroche.append(indice)
    return listeIndicesAccroche

def position(signalBinMan:str, N_reception:int, motif:str, role:str, maxErreursMotif:int) -> int:
    """
    prédis la position de début/fin du message dans signalBinMan grâce à l'identifiant des accroches
    en effet on connait la taille des motifs et le nombre total de (motif + id) -> 8
    """
    positionAccroche = []
    N_reception16 = 16*N_reception # 2*8 car codage Manchester double taille accroche
    N_reception22 = 22*N_reception
    listeIndicesAccroche = chercheIndicesAccroche(signalBinMan, motif, maxErreursMotif)
    
    if listeIndicesAccroche == []:
        print(f"Erreur pas d'accroche {role} trouvée")
        return -1
    for indiceAccroche in listeIndicesAccroche:
        accrocheID = signalBinMan[indiceAccroche+N_reception16:indiceAccroche+N_reception22]
        idBin = ''
        for indiceID in range(0, 2*N_reception, N_reception):
            idBin += mostCommon(accrocheID[indiceID:indiceID+N_reception], 'str')
        id = codageBaseDix(idBin)
        if 0 <= id < 8:
            if role == 'start':
                start = indiceAccroche + (8 - id)*N_reception22 # 22 = taille de chaque accroche après codage Manchester, 8 = nombre de motifs de l'accroche
                positionAccroche.append(start)
            elif role == 'end':
                end = indiceAccroche - id*N_reception22
                positionAccroche.append(end)
            else:
                print(f'Erreur : {role} n\'est pas un rôle valide (start ou end)')
                return -1
        else:
            print('Erreur : id pas dans intervalle (pas grave)')
    print(f"{role} : {positionAccroche}")
    return mostCommon(positionAccroche, 'int')

def detectionAccroche(signalBinMan:str, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    """
    slice le signal binaire (toujours codé en Manchester) pour ne garder que le message sans les accroches
    """
    startDoublonsMan = ""
    endDoublonsMan = ""

    for k in range(len(startMan)):
        startDoublonsMan += N_reception * startMan[k]
        endDoublonsMan += N_reception * endMan[k]
    
    motifStart = startDoublonsMan[:N_reception*16] # car codage Manchester a doublé la taille de l'accroche
    motifEnd = endDoublonsMan[:N_reception*16]

    start = position(signalBinMan, N_reception, motifStart, 'start', maxErreursMotif)
    end = position(signalBinMan, N_reception, motifEnd, 'end', maxErreursMotif)
    
    if end >= start:
        print("Erreur dans la position des accroches trouvées")

    return signalBinMan[start:end]

def demodulation(tension:list, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    """
    on extraie le message binaire (sans les accroches) de la liste des tensions
    on enlève les répétitions causé par la fréquence d'échantillonnage N_reception
    si les valeurs sont légérement différente, on prend la plus commune
    """
    tension = tension[0] #sys.entree me renvoie une liste avec un tableau unidimensionnel de tension à l'intérieur
    tension = np.array([np.round(element, 1) for element in tension]) # on arrondit les éléments pour la suite
    print(len(tension))

    signalBinMan = voltageToBinary(tension, N_reception)

    messageBinManDouble = detectionAccroche(signalBinMan, N_reception, startMan, endMan, maxErreursMotif) # chaque bit est répété N_reception fois par rapport au message Man envoyé

    messageBinMan = '' # on enlève les doublons

    valeursBit = [int(messageBinManDouble[0])]
    for indice in range(1, len(messageBinManDouble)):
        if indice % N_reception == 0:
            messageBinMan += mostCommon(valeursBit, 'str')
            valeursBit = [int(messageBinManDouble[indice])]
        else:
            valeursBit.append(int(messageBinManDouble[indice]))
    return messageBinMan

def decodageMan(messageBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    messageBin = ''
    for k in range(0, len(messageBinMan), 2): # pas de 2 car on saute la transition
        if messageBinMan[k] == '0': # transition 0 --> 1
            messageBin += '1'
        else: # transition 1 --> 0
            messageBin += '0'
    return messageBin

def decodageASCII(messageBin:str) -> str:
    """
    message binaire -> texte ASCII
    """
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tension:list, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    return decodageASCII(decodageMan(demodulation(tension, N_reception, startMan, endMan, maxErreursMotif)))
