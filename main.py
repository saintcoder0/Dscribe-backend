import logging
import os
import re
from contextlib import asynccontextmanager

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import DESCENDING, ReturnDocument

from database import get_patients_collection, ping_database
from schemas import (
    DEPARTMENTS,
    DOCTORS,
    GENDERS,
    REQUIRED_MESSAGES,
    WARDS,
    OptionsOut,
    PatientInput,
    PatientOut,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ping_database()
    yield


app = FastAPI(title="Patient Admission Management API", lifespan=lifespan)

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origin=raw_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["content-type", ""],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc", ())
        field = str(loc[-1]) if loc else "body"
        if field in errors:
            continue
        if err.get("type") == "missing" and field in REQUIRED_MESSAGES:
            errors[field] = REQUIRED_MESSAGES[field]
        else:
            msg = str(err.get("msg", "Invalid value"))
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, ") :]
            errors[field] = msg
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )


def serialize_patient(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "age": doc["age"],
        "gender": doc["gender"],
        "ward": doc["ward"],
        "department": doc["department"],
        "doctor": doc["doctor"],
        "admission_date": doc["admission_date"],
        "status": doc["status"],
    }


def parse_object_id(patient_id: str) -> ObjectId:
    try:
        return ObjectId(patient_id)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        ) from exc


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/options", response_model=OptionsOut)
def get_options():
    return {
        "genders": GENDERS,
        "wards": WARDS,
        "departments": DEPARTMENTS,
        "doctors": DOCTORS,
    }


@app.get("/api/patients", response_model=list[PatientOut])
def list_patients(
    search: str | None = Query(default=None),
    ward: str | None = Query(default=None),
    department: str | None = Query(default=None),
    doctor: str | None = Query(default=None),
):
    collection = get_patients_collection()
    query: dict = {}

    if search and search.strip():
        query["name"] = {"$regex": re.escape(search.strip()), "$options": "i"}
    if ward and ward.strip():
        query["ward"] = ward.strip()
    if department and department.strip():
        query["department"] = department.strip()
    if doctor and doctor.strip():
        query["doctor"] = doctor.strip()

    docs = collection.find(query).sort("_id", DESCENDING)
    return [serialize_patient(doc) for doc in docs]


@app.post(
    "/api/patients",
    response_model=PatientOut,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(payload: PatientInput):
    collection = get_patients_collection()
    doc = payload.model_dump()
    doc["status"] = "Admitted"
    result = collection.insert_one(doc)
    created = collection.find_one({"_id": result.inserted_id})
    return serialize_patient(created)


@app.put("/api/patients/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, payload: PatientInput):
    collection = get_patients_collection()
    oid = parse_object_id(patient_id)
    updated = collection.find_one_and_update(
        {"_id": oid},
        {"$set": payload.model_dump()},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return serialize_patient(updated)


@app.patch("/api/patients/{patient_id}/discharge", response_model=PatientOut)
def discharge_patient(patient_id: str):
    collection = get_patients_collection()
    oid = parse_object_id(patient_id)
    updated = collection.find_one_and_update(
        {"_id": oid},
        {"$set": {"status": "Discharged"}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return serialize_patient(updated)


@app.delete("/api/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str):
    collection = get_patients_collection()
    oid = parse_object_id(patient_id)
    result = collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
