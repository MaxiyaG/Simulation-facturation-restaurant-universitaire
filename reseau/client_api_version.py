# ----- 1 - IMPORTATIONS ------------------------------------
import socket
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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


class IdClient(BaseModel):
    id: str = Field(..., pattern=r"^\S{11}$", examples=["45215252813"])


# ----- 4 - API ---------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    serveur.close()


app = FastAPI(title="API Cantine", lifespan=lifespan)


@app.post("/cantine", status_code=201)
def envoyer_id(payload: IdClient):
    """Reçoit un ID client et l'envoie au serveur de facturation."""
    try:
        serveur.envoyer_id(payload.id)
    except OSError:
        raise HTTPException(status_code=503, detail="Serveur de facturation injoignable")
    return {"id": payload.id, "statut": "envoyé"}

