# ----- 1 - IMPORTATIONS ------------------------------------
import socket
import threading
from contextlib import asynccontextmanager

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

# Exemple d'id client a facturer: 45215252813

# ----- 2 - CONSTANTES --------------------------------------
"""
CONSTANTES LIEES A LA CONNEXION AU SERVEUR
"""
HOST = "localhost"
PORT = 7470


# ----- 3 - CLASSES ET FONCTIONS ----------------------------
class ServeurCantine:
    """
    Gère une connexion socket persistante vers le serveur de facturation.
    Reconnexion automatique si la connexion est perdue.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self.lock = threading.Lock()  # une seule requête écrit sur le socket à la fois

    def _connect(self):
        self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.host, self.port))

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def envoyer_id(self, id_client: str):
        out = (id_client + "\r\n").encode("utf8")
        with self.lock:
            for tentative in range(2):  # 2e tentative = reconnexion
                try:
                    if self.sock is None:
                        self._connect()
                    self.sock.sendall(out)
                    return
                except OSError:
                    self.close()
                    if tentative == 1:
                        raise


serveur = ServeurCantine(HOST, PORT)


# ----- 4 - API ---------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    serveur.close()


app = FastAPI(title="API Cantine", lifespan=lifespan)


@app.get("/cantine/{id_client}")
def envoyer_id(id_client: Annotated[str, Path(pattern=r"^\S{11}$", examples=["45215252813"])]):
    """Reçoit un ID client via le lien et l'envoie au serveur de facturation."""
    try:
        serveur.envoyer_id(id_client)
    except OSError:
        raise HTTPException(status_code=503, detail="Serveur de facturation injoignable")
    return {"id": id_client, "statut": "envoyé"}

# Exemple http://localhost:8000/cantine/45215252813
