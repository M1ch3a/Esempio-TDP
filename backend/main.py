import csv
import os
import logging
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Abilita CORS per accesso dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia con l’URL del frontend in produzione
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEWS_API_KEY = "0d082d09a8b44957a862fd3418a738fe"
CSV_FILE_PATH = "subscribers.csv"

# Funzione per leggere gli iscritti dal CSV
def read_subscribers():
    subscribers = set()
    if os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode="r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # Salta intestazione se esiste
            for row in reader:
                if row:
                    subscribers.add(row[0])
    return subscribers

# Funzione per aggiungere un nuovo iscritto
def add_subscriber(email: str):
    with open(CSV_FILE_PATH, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([email])

# Inizializza set degli iscritti
subscribers = read_subscribers()

# Scheduler background
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        send_newsletter_periodically,
        IntervalTrigger(hours=24),
        id='newsletter_job',
        name='Invia newsletter ogni 24 ore',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler avviato.")
    yield
    scheduler.shutdown()
    logger.info("Scheduler fermato.")

app = FastAPI(lifespan=lifespan)

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

@app.post("/subscribe")
def subscribe(email: str = Form(...)):
    if "@" not in email:
        return JSONResponse(status_code=400, content={"message": "Email non valida."})
    
    if email in subscribers:
        return JSONResponse(status_code=400, content={"message": "Email già iscritta."})

    add_subscriber(email)
    subscribers.add(email)
    return {"message": "Iscrizione alla newsletter avvenuta con successo."}

def send_newsletter(news_items=None):
    if news_items is None:
        news = get_mafia_news()
        news_items = news.get("articles", [])

    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_server = "smtp.gmail.com"
    port = 587

    subject = "Ultime notizie sulla mafia"
    body = "\n\n".join([f"{article['title']}\n{article['url']}" for article in news_items])
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            for email in subscribers:
                message["To"] = email
                server.sendmail(sender_email, email, message.as_string())
        logger.info("Newsletter inviata con successo.")
    except Exception as e:
        logger.error(f"Errore nell'invio dell'email: {e}")

def send_newsletter_periodically():
    news = get_mafia_news()
    send_newsletter(news.get("articles", []))

@app.post("/send-newsletter")
def manual_send_newsletter():
    news = get_mafia_news()
    send_newsletter(news.get("articles", []))
    return {"message": "Newsletter inviata agli iscritti."}
