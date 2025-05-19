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
    """
    messageBin = ''
    for lettre in message:
        lettre = ord(lettre) # ASCII décimal (int)
        messageBin += codageBinaire(lettre)
    return messageBin

def creationAccroche(lettre:str, nombreRepetitions) -> str:
    """
    on créée une succesion improbable
    """
    return encodage(lettre)*nombreRepetitions

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

def ook(messageMan:str, tensionMax:int, N:int) -> list:
    """
    transforme le message codé (Manchester) en valeurs de tension pour les LEDS
    on utilise la modulation on-off keying (OOK)
    """
    tension = []
    for bit in messageMan:
        if bit == '0':
            tension += [0]*N
        elif bit == '1':
            tension += [tensionMax]*N
        else:
            print('Erreur : le message binaire est corrompu, une valeur autre que 0 et 1 a été trouver')
            return []
    return np.array(tension, dtype=np.float32)

def emission(message:str, tensionMax:int, N:int, start:str, end:str) -> list:
    messageMan = codageManchester(start + encodage(message) + end) # accroches ajoutées au message
    return ook(messageMan, tensionMax, N)

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

        if tensionMax == 0 or (tensionMax - tensionMin) < 0.5:
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

def decodageMan(signalBinMan:str) -> str:
    """
    se référer à l'illustration sur Wikipedia de la page sur le codage Manchester (version anglophone)
    """
    signalBin = ''
    for indice in range(len(signalBinMan-1)):
        if signalBinMan[indice] == '0' and signalBinMan[indice+1] == '1':
            signalBin += '1'
        elif signalBinMan[indice] == '1' and signalBinMan[indice+1] == '0':
            signalBin += '0'
        else:
            print('Transition non définie dans decodageMan()')
    return signalBin

def chercheIndiceAccroche(signalBin:str, accroche:str, role:str, maxErreursAccroche:int) -> int:
    """
    lors de la transmission du message, des erreurs apparaissent causées par différents facteurs
    pour trouver lorsque le message débute et finit on utilise des accroches,
    on doit alors autoriser quelques erreurs sur ces accroches
    """
    if role != 'start' and role != 'end':
        print('Erreur dans le rôle des accroches dans chercheIndiceAccroche()')
        return []

    indiceAccroche = float.inf
    accrocheBits = bitarray(accroche)
    for indice in range(len(signalBin)-len(accroche)):
        signalBits = bitarray(signalBin[indice:indice+len(accroche)])
        nombreErreurs = (signalBits ^ accrocheBits).count() # ^ représente l'opérateur XOR
        if nombreErreurs <= maxErreursAccroche and role == 'start':
            indiceAccroche = indice+len(role)
        elif nombreErreurs <= maxErreursAccroche and role == 'end':
            indiceAccroche = indice

    if indiceAccroche == float.inf:
        print('Accroche non trouvée')

    return indiceAccroche

def detectionAccroche(signalBin:str, start:str, end:str, maxErreursAccroche:int) -> str:
    """
    slice le signal binaire pour ne garder que le message sans les accroches
    """
    start = chercheIndiceAccroche(signalBin, start, 'start', maxErreursAccroche)
    end = chercheIndiceAccroche(signalBin, end, 'end', maxErreursAccroche)
    
    if end <= start:
        print("Erreur dans la position des accroches trouvées")

    return signalBin[start:end]

def demodulation(tension:list, N_reception:int, start:str, end:str, maxErreursAccroche:int) -> str:
    """
    on extraie le message binaire (sans les accroches) de la liste des tensions
    """
    tension = tension[0] #sys.entree me renvoie une liste avec un tableau unidimensionnel de tension à l'intérieur
    tension = np.round(tension, 2) # on arrondit les éléments pour la suite

    signalBinMan = voltageToBinary(tension, N_reception)
    signalBin = decodageMan(signalBinMan)
    messageBin = detectionAccroche(signalBin, start, end, maxErreursAccroche)

    return messageBin

def decodageASCII(messageBin:str) -> str:
    """
    message binaire -> texte ASCII
    """
    messageTransmis = ''
    for posLettre in range(0, len(messageBin), 8):
        messageTransmis += chr(codageBaseDix(messageBin[posLettre:posLettre+8]))
    return messageTransmis

def reception(tension:list, N_reception:int, start:str, end:str, maxErreursAccroche:int) -> str:
    return decodageASCII(demodulation(tension, N_reception, start, end, maxErreursAccroche))
