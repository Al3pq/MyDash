import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from fastapi import FastAPI, HTTPException


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


# DEFINIZIONE MODELLI DATI

# Definisce la struttura di elemento libro inviato con POST
class LibroSchema(BaseModel):
    titolo: str
    autore: str
    pagine_tot: int
    pagine_lette: Optional[int] = 0
    stato: Optional[str] = "In attesa"

# Definisce il dato ISBN
class ScanISBNRequest(BaseModel):
    isbn: str


# FUNZIONI UTILI JSON
def carica_dati():
    with open(FILE_DATI, "r", encoding="utf-8") as file:
        return json.load(file)

def salva_dati(dati):
    with open(FILE_DATI, "w", encoding="utf-8") as file:
        json.dump(dati, file, indent=2, ensure_ascii=False)


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


# Endpoint 3: scansione ISBN e recupereo dati da Open Library -> POST
@app.post("/api/libri/scan")
async def aggiungi_libro_ISBN(req: ScanISBNRequest):
    # Pulizia dati ISBN input da trattini o spazi
    isbn = req.isbn.strip().replace("-","")

    # Invoco API pubblica OpenLibrary
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"

    # Creazione client e richiesta HTTP
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    dati_api = response.json()
    chiave_libro = f"ISBN:{isbn}"

    # Gestione errore mancato ritrovamento libro
    if chiave_libro not in dati_api:
        raise HTTPException(
            status_code=404,
            detail = f"Nessun libro trovato con ISBN: {isbn}"
        )

    info_libro = dati_api[chiave_libro]

    # Estraggo dati inserendo default e unione autori se molteplici
    titolo = info_libro.get("title", "Titolo sconosciuto")
    autori = [a["name"] for a in info_libro.get("authors", [])]
    autore = ", ".join(autori) if autori else "Autore sconosciuto"
    pagine_tot = info_libro.get("number_of_pages", 0)

    # Leggo database JSON esistente
    dati = carica_dati()
    #calcolo id sequenziale
    nuovo_id = len(dati["libri"]) + 1 if dati["libri"] else 1

    # Creo scheda libro da inserire
    nuovo_libro= {
        "id": nuovo_id,
        "titolo": titolo,
        "autore": autore,
        "pagine_tot": pagine_tot,
        "pagine_lette": 0,
        "stato": "In attesa",
        "voto": None
    }

    # salvataggio su file json
    dati["libri"].append(nuovo_libro)
    salva_dati(dati)

    return {
        "message": "Libro trovato e aggiunto",
        "libro": nuovo_libro
    }
