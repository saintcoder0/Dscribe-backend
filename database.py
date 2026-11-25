import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

logger = logging.getLogger("patient_admission")

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "hospital").strip() or "hospital"

client: MongoClient | None = None
patients_collection = None

if MONGO_URI:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    patients_collection = db["patients"]


def get_patients_collection():
    if patients_collection is None:
        raise RuntimeError(
            "Database is not configured. Set MONGO_URI in environment variables."
        )
    return patients_collection


def ping_database() -> None:
    if not MONGO_URI or client is None:
        msg = "MONGO_URI environment variable is missing. Set it in backend/.env before starting the server."
        logger.error(msg)
        raise RuntimeError(msg)
    try:
        client.admin.command("ping")
        logger.info("Connected to MongoDB (database: %s)", DB_NAME)
    except PyMongoError as exc:
        logger.error("Failed to connect to MongoDB: %s", exc)
        raise RuntimeError(f"Failed to connect to MongoDB: {exc}") from exc
