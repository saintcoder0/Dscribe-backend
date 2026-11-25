import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, field_validator

GENDERS = ["Male", "Female", "Other"]
WARDS = ["General Ward", "ICU", "Emergency", "Maternity", "Pediatric"]
DEPARTMENTS = [
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "Pediatrics",
    "General Medicine",
]
DOCTORS = [
    "Dr. Anil Sharma",
    "Dr. Priya Mehta",
    "Dr. Rahul Verma",
    "Dr. Sneha Patel",
    "Dr. Vikram Singh",
]

NAME_PATTERN = re.compile(r"^[A-Za-z]+( [A-Za-z]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IST = timezone(timedelta(hours=5, minutes=30))

REQUIRED_MESSAGES = {
    "name": "Name is required",
    "age": "Age is required",
    "gender": "Please select a valid gender",
    "ward": "Please select a valid ward",
    "department": "Please select a valid department",
    "doctor": "Please select a valid doctor",
    "admission_date": "Admission date is required",
}


class PatientInput(BaseModel):
    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: str

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Any) -> str:
        if value is None or not isinstance(value, str):
            raise ValueError("Name is required")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Name is required")
        if not NAME_PATTERN.fullmatch(trimmed):
            raise ValueError("Name must contain letters only")
        return trimmed

    @field_validator("age", mode="before")
    @classmethod
    def validate_age(cls, value: Any) -> int:
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError("Age is required")
        if isinstance(value, bool):
            raise ValueError("Age must be a number between 0 and 120")
        if isinstance(value, int):
            parsed = value
        elif isinstance(value, str):
            stripped = value.strip()
            if not re.fullmatch(r"-?\d+", stripped):
                raise ValueError("Age must be a number between 0 and 120")
            parsed = int(stripped)
        else:
            raise ValueError("Age must be a number between 0 and 120")

        if parsed < 0 or parsed > 120:
            raise ValueError("Age must be a number between 0 and 120")
        return parsed

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Any) -> str:
        if not isinstance(value, str) or value not in GENDERS:
            raise ValueError("Please select a valid gender")
        return value

    @field_validator("ward", mode="before")
    @classmethod
    def validate_ward(cls, value: Any) -> str:
        if not isinstance(value, str) or value not in WARDS:
            raise ValueError("Please select a valid ward")
        return value

    @field_validator("department", mode="before")
    @classmethod
    def validate_department(cls, value: Any) -> str:
        if not isinstance(value, str) or value not in DEPARTMENTS:
            raise ValueError("Please select a valid department")
        return value

    @field_validator("doctor", mode="before")
    @classmethod
    def validate_doctor(cls, value: Any) -> str:
        if not isinstance(value, str) or value not in DOCTORS:
            raise ValueError("Please select a valid doctor")
        return value

    @field_validator("admission_date", mode="before")
    @classmethod
    def validate_admission_date(cls, value: Any) -> str:
        if value is None or not isinstance(value, str) or not value.strip():
            raise ValueError("Admission date is required")
        stripped = value.strip()
        if not DATE_PATTERN.fullmatch(stripped):
            raise ValueError("Admission date must be a valid date")
        try:
            parsed_date = date.fromisoformat(stripped)
        except ValueError as exc:
            raise ValueError("Admission date must be a valid date") from exc

        today_ist = datetime.now(IST).date()
        if parsed_date > today_ist:
            raise ValueError("Admission date cannot be in the future")
        return parsed_date.isoformat()


class PatientOut(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: str
    status: Literal["Admitted", "Discharged"]


class OptionsOut(BaseModel):
    genders: list[str]
    wards: list[str]
    departments: list[str]
    doctors: list[str]
