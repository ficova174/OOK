import numpy as np
from bitarray import bitarray

# Partie émission

def codageBinaire(nombre:int) -> str:
    """
    nombre décimal -> nombre en binaire
    attention on code de gauche à droite (petites puissances à gauche)
    """
    nombreBin = ''
    while nombre > 0:
        nombreBin += str(nombre % 2)
        nombre //= 2
    while len(nombreBin) < 8: # on veut une taille fixe, on ajoute des 0
        nombreBin += '0'
    return nombreBin

def encodage(message:str) -> str:
    """
    message texte (str) -> message en binaire (str)
    on demande la taille des paquets car on utilisera cette fonction pour coder des strings de longueur variable (accroche et ID)
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre)
    return messageBin

def creationAccroche(lettre1:str, lettre2:str, repetitions:int) -> tuple:
    """
    on créée une succesion improbable
    on lui donne un identifiant pour estimer le début du message (fonction detectionAccroche())
    """
    return (encodage(lettre1)*repetitions, encodage(lettre2)*repetitions)

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

def ook(messageMan:str, tensionMin:int, tensionMax:int, N:int) -> np.ndarray:
    """
    transforme le message codé (Manchester) en valeurs de tension pour les LEDS
    on utilise la modulation on-off keying (OOK)
    """
    tension = []
    for bit in messageMan:
        if bit == '0':
            tension += [tensionMin]*N
        elif bit == '1':
            tension += [tensionMax]*N
        else:
            print('Erreur : le message binaire est corrompu, une valeur autre que 0 et 1 a été trouver')
            return np.array([])
    return np.array(tension, dtype=np.float32)

def emission(message:str, tensionMin:int, tensionMax:int, N:int, startMan:str, endMan:str) -> np.ndarray:
    messageMan = startMan + codageManchester(message) + endMan
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

def mostCommon(liste:list | str, type:str) -> (None | float | int | str):
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

def decoupeListe(dividedSignal:list, tension:np.ndarray, size:int):
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

def voltageToBinary(tension:np.ndarray, N_reception:int) -> str:
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

def chercheIndicesAccroche(signalBinMan:str, motif:str, maxErreursMotif:int) -> int:
    """
    on cherche l'accroche, or celle-ci n'a pas été transmise parfaitement
    on doit alors accepter un certains nombre d'erreurs dans le motif de l'accroche (id pas de problème)
    on utilise une méthode inspirée de la distance de Hamming pour connaitre ce nombre d'erreurs
    on renvoie la liste des indices de début des motifs avec autant ou moins d'erreurs que maxErreurMotif
    chaque bit est répété N_reception fois (la période d'échantillonage)
    """
    indiceAccroche = -1
    motifBits = bitarray(motif)
    compteur = 0
    for indice in range(len(signalBinMan)-len(motif)):
        signalBits = bitarray(signalBinMan[indice:indice+len(motif)])
        nombreErreurs = (signalBits ^ motifBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursMotif:
            indiceAccroche = indice
            compteur += 1
    if compteur != 1:
        print('Plus d\'une accroche trouvée')
    if indiceAccroche == -1:
        print('Pas d\'accroche trouvée')
    return indiceAccroche

def detectionAccroche(signalBinMan:str, startDoublonsMan:str, endDoublonsMan:str, maxErreursMotif:int) -> tuple:
    startPos = chercheIndicesAccroche(signalBinMan, startDoublonsMan, maxErreursMotif)
    endPos = chercheIndicesAccroche(signalBinMan, endDoublonsMan, maxErreursMotif)
    
    if endPos <= startPos:
        print("Erreur dans la position des accroches trouvées")

    return (startPos, endPos)

def demodulation(tension:np.ndarray, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int):
    """
    on extraie le message binaire (sans les accroches) de la liste des tensions
    on enlève les répétitions causé par la fréquence d'échantillonnage N_reception
    si les valeurs sont légérement différente, on prend la plus commune
    """
    tension = tension[0] #sys.entree me renvoie une liste avec un tableau unidimensionnel de tension à l'intérieur
    tension = np.array([np.round(element, 1) for element in tension]) # on arrondit les éléments pour la suite

    signalBinManDouble = voltageToBinary(tension, N_reception)

    startDoublonsMan = ""
    endDoublonsMan = ""

    for k in range(len(startMan)):
        startDoublonsMan += N_reception * startMan[k]
        endDoublonsMan += N_reception * endMan[k]

    (startPos, endPos) = detectionAccroche(signalBinManDouble, startDoublonsMan, endDoublonsMan, maxErreursMotif) # chaque bit est répété N_reception fois par rapport au message Man envoyé

    messageBinMan = '' # on enlève les doublons

    valeursBit = [int(signalBinManDouble[startPos+len(startDoublonsMan)])]
    indiceModulo = 1
    for indice in range(startPos+len(startDoublonsMan), endPos-1): # -1 ???
        if indiceModulo % N_reception == 0:
            messageBinMan += mostCommon(valeursBit, 'str')
            valeursBit = [int(signalBinManDouble[indice])]
        else:
            valeursBit.append(int(signalBinManDouble[indice]))
        indiceModulo += 1
    messageBinMan += mostCommon(valeursBit, 'str')
    
    return messageBinMan

def decodageMan(messageBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    et à l'utilisation de XOR
    """
    horloge = [k%2 for k in range(1, len(messageBinMan)+1)] # On commence à 1 pour que l'horloge commence par 1
    messageBinTemp = ''

    for indice in range(len(messageBinMan)):
        if horloge[indice] == messageBinMan[indice]:
            messageBinTemp += '0'
        else:
            messageBinTemp += '1'
    
    if type(int(len(messageBinTemp))/2) != int:
        print('len(messageBinTemp) n\'est pas paire')

    messageBin = ''
    for indice in range(0, len(messageBinTemp), 2): # Manchester double taille donc forcément paire
        messageBin += messageBinTemp[indice]

    return messageBin

def decodageASCII(messageBin:str) -> str:
    """
    message binaire -> texte ASCII
    """
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tension:np.ndarray, N_reception:int, startMan:str, endMan:str, maxErreursMotif:int) -> str:
    messageBinMan = demodulation(tension, N_reception, startMan, endMan, maxErreursMotif)
    messageBin = decodageMan(messageBinMan)
    return decodageASCII(messageBin)
