"""Application configuration and validation constants."""

from __future__ import annotations

import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./patients.db")

# Optional write-protection API Key
API_KEY = os.getenv("API_KEY", "").strip() or None

# Vapi Integration Keys
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "").strip() or None
VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "").strip() or None
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "f87a7c69-c6a9-4bfe-91c6-a9e90c0b39ea").strip()
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000").strip().rstrip("/")

# Groq LLM Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip() or None
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else "openai").strip().lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()

# Valid 2-letter US states and DC
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

# Spoken state name to 2-letter abbreviation mapping
STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
    "wyoming": "WY", "district of columbia": "DC", "washington dc": "DC",
}

# Regular expressions for validation
NAME_RE = re.compile(r"^[A-Za-z]+(?:[ '\-][A-Za-z]+)*$")
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
MEMBER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{0,49}$")
PHONE_DIGITS_RE = re.compile(r"\D+")

# Sex mapping for spoken/casual voice responses
SEX_ALIASES = {
    "male": "Male",
    "m": "Male",
    "man": "Male",
    "boy": "Male",
    "female": "Female",
    "f": "Female",
    "woman": "Female",
    "girl": "Female",
    "other": "Other",
    "non-binary": "Other",
    "decline": "Decline to Answer",
    "decline to answer": "Decline to Answer",
    "prefer not to say": "Decline to Answer",
    "prefer not to answer": "Decline to Answer",
    "skip": "Decline to Answer",
}
