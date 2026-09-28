# ----- 1 - IMPORTATIONS ------------------------------------
import socket
from fastapi import FastAPI, HTTPException

#Exemple d'id client a facturer:45215252813

# ----- 2 - CONSTANTES --------------------------------------
"""
CONSTANTE LIER A LA CONNEXION AU SERVEUR
"""
HOST = 'localhost'
PORT = 7470
client_socket = None

# ----- 3 - FONCTIONS --------------------------------------
"""
FONCTION DE VERIFICATION DE L'ID AVANT ENVOIE
"""
def check_id(id):
    if len(id) != 11 or (" " in id):
        return False
    return True

"""
FONCTION DE CONNEXION AU SERVEUR
"""
def connexion():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("Client connecté !")

"""
FONCTION D'ENVOIE DE L'ID AU SERVEUR (RECONNEXION SI LA CONNEXION EST PERDUE)
"""
def envoyer_id(id):
    out = (id+"\r\n").encode("utf8")
    try:
        if client_socket is None:
            connexion()
        client_socket.send(out)
    except OSError:
        connexion()
        client_socket.send(out)

# ----- 4 - PROGRAMME PRINCIPAL ------------------------------
"""
API : RECOIT L'ID PAR LE LIEN ET L'ENVOIE AU SERVEUR
"""
app = FastAPI()

@app.get("/cantine/{id}")
async def cantine(id: str):
    if not check_id(id):
        raise HTTPException(status_code=422, detail="ID Incorrect, veuillez entrer un ID de taille 11")
    try:
        envoyer_id(id)
    except OSError:
        raise HTTPException(status_code=503, detail="Connection echouée")
    print("ID: ", id, " a étais envoyé \n")
    return {"id": id, "statut": "envoyé"}

# Lancement : uvicorn main:app --reload
# Exemple http://localhost:8000/cantine/45215252813
