from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# CORS per permettere accesso dal sito web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione: metti l'URL vero del tuo sito
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEWS_API_KEY = "29301ef09e5c426a96143b785681a53b"

@app.get("/news")
def get_mafia_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "mafia OR camorra OR ndrangheta",
        "language": "it",
        "pageSize": 10,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
    }
    response = requests.get(url, params=params)
    return response.json()
