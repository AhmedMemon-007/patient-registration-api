from typing import Optional
from datetime import date
import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator

US_STATES = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
"IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
"NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA",
"WA","WV","WI","WY","DC"}

ALLOWED_SEX_VALUES = {"Male", "Female", "Other", "Decline to Answer"}

# Optional fields where an LLM/voice agent may send "" instead of omitting
# the field entirely. These get normalized to None before validation runs,
# so Optional[...] fields don't reject an empty string as invalid input.
OPTIONAL_STRING_FIELDS = {
    "email", "address_line_2", "insurance_provider",
    "insurance_member_id", "emergency_contact_name",
    "emergency_contact_phone", "preferred_language"
}


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def blank_strings_to_none(cls, data):
        if isinstance(data, dict):
            for field in OPTIONAL_STRING_FIELDS:
                if field in data and data[field] == "":
                    data[field] = None
        return data

    @field_validator("first_name", "last_name")
    @classmethod
    def name_format(cls, v):
        if not re.match(r"^[A-Za-z'\-\s]{1,50}$", v):
            raise ValueError("Name must be 1-50 alphabetic characters, hyphens, or apostrophes")
        return v.strip()

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("sex")
    @classmethod
    def sex_enum(cls, v):
        if v not in ALLOWED_SEX_VALUES:
            raise ValueError(f"sex must be one of {ALLOWED_SEX_VALUES}")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def phone_format(cls, v):
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("Phone number must be a valid 10-digit US number")
        return digits

    @field_validator("state")
    @classmethod
    def state_valid(cls, v):
        v = v.upper()
        if v not in US_STATES:
            raise ValueError("Invalid US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v):
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP must be 5-digit or ZIP+4 format")
        return v


class PatientUpdate(BaseModel):
    """
    Mirrors PatientCreate but every field is optional (only fields the
    client actually sends get validated/updated). The same validation
    rules apply here as on create -- previously this model had NO
    validators at all, so a PUT request could silently set an invalid
    sex, state, ZIP, or phone number. Each validator below is guarded
    with `if v is None: return v` since any field may be omitted.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def blank_strings_to_none(cls, data):
        if isinstance(data, dict):
            for field in OPTIONAL_STRING_FIELDS:
                if field in data and data[field] == "":
                    data[field] = None
        return data

    @field_validator("first_name", "last_name")
    @classmethod
    def name_format(cls, v):
        if v is None:
            return v
        if not re.match(r"^[A-Za-z'\-\s]{1,50}$", v):
            raise ValueError("Name must be 1-50 alphabetic characters, hyphens, or apostrophes")
        return v.strip()

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v):
        if v is None:
            return v
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("sex")
    @classmethod
    def sex_enum(cls, v):
        if v is None:
            return v
        if v not in ALLOWED_SEX_VALUES:
            raise ValueError(f"sex must be one of {ALLOWED_SEX_VALUES}")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def phone_format(cls, v):
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("Phone number must be a valid 10-digit US number")
        return digits

    @field_validator("state")
    @classmethod
    def state_valid(cls, v):
        if v is None:
            return v
        v = v.upper()
        if v not in US_STATES:
            raise ValueError("Invalid US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def zip_format(cls, v):
        if v is None:
            return v
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP must be 5-digit or ZIP+4 format")
        return v