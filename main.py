import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse





#Inizzializzare applicazione FastAPI
app = FastAPI(title="MyDash - Reading Tracker API")

#Configurazione CORS per sbloccare le chiamate dal browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permette a qualsiasi origine (compreso il tuo index.html) di chiamare le API
    allow_credentials=True,
    allow_methods=["*"], # Permette tutti i metodi (GET, POST, ecc.)
    allow_headers=["*"], # Permette tutti gli header
)

FILE_DATI = "dati.json"

#Configurazione rotta su index
@app.get("/")
def home():
    return FileResponse("index.html")

# MODELLO DATI
# Definisce la struttura di elemento libro inviato con POST

class LibroSchema(BaseModel):
    titolo: str
    autore: str
    pagine_tot: int
    pagine_lette: Optional[int] = 0
    stato: Optional[str] = "In attesa"


# FUNZIONI UTILI JSON
def carica_dati():
    with open(FILE_DATI, "r", encoding="utf-8") as file:
        return json.load(file)

def salva_dati(dati):
    with open(FILE_DATI, "w", encoding="utf-8") as file:
        json.dump(dati, file, indent=2, ensure_ascii=false)


# ROTTE API
# Endpoint 1: ottenere lista libri -> GET
@app.get("/api/libri")
def get_libri():
    dati = carica_dati()
    return dati["libri"]

# Endpoint 2: aggiungere un libro -> POST
@app.post("/api/libri")
def crea_libro(libro: LibroSchema):
    dati = carica_dati()

    #calcolo id sequenziale
    nuovo_id = len(dati["libri"]) + 1 if dati["libri"] else 1

    #conversione modello Pydantic in dizionario Python
    nuovo_libro = libro.dict()
    nuovo_libro["id"] = nuovo_id
    nuovo_libro["valutazione"] = None

    #aggiungi e salva
    dati["libri"].append(nuovo_libro)
    salva_dati(dati)

    return {"message":"Libro aggiunto con successo", "libro": nuovo_libro}