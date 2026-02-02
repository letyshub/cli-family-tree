"""
Data models for the Family Tree application.

Contains the Person class and validation functions.
"""

from datetime import date
from typing import Optional


class ValidationError(Exception):
  """Raised when validation fails for a field."""

  def __init__(self, field: str, message: str):
    self.field = field
    self.message = message
    super().__init__(f"{field}: {message}")


def validate_name(name: str) -> str:
  """Validate and normalize a person's name."""
  if not name or not name.strip():
    raise ValidationError("name", "Name cannot be empty")

  name = name.strip()
  if len(name) > 100:
    raise ValidationError("name", "Name cannot exceed 100 characters")

  return name


def validate_year(year: Optional[int], field_name: str) -> Optional[int]:
  """Validate a year is within acceptable range (1500-2100)."""
  if year is None:
    return None

  if not isinstance(year, int):
    raise ValidationError(field_name, "Year must be an integer")

  if year < 1500 or year > 2100:
    raise ValidationError(field_name, "Year must be between 1500 and 2100")

  return year


def validate_death_year(death_year: Optional[int], birth_year: Optional[int]) -> Optional[int]:
  """Validate death year is not before birth year."""
  if death_year is None:
    return None

  death_year = validate_year(death_year, "death_year")

  if birth_year is not None and death_year is not None and death_year < birth_year:
    raise ValidationError("death_year", "Death year cannot be before birth year")

  return death_year


def validate_gender(gender: Optional[str]) -> Optional[str]:
  """Validate gender is one of the accepted values."""
  if gender is None or gender == "":
    return None

  valid_genders = ["M", "F", "Other"]
  if gender not in valid_genders:
    raise ValidationError("gender", f"Gender must be one of: {', '.join(valid_genders)}")

  return gender


def validate_date(date_str: Optional[str], field_name: str) -> Optional[date]:
  """Validate and parse a date string (YYYY-MM-DD format)."""
  if date_str is None or date_str == "":
    return None

  if isinstance(date_str, date):
    return date_str

  try:
    parts = date_str.split("-")
    if len(parts) != 3:
      raise ValueError()
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    parsed = date(year, month, day)

    if parsed.year < 1500 or parsed.year > 2100:
      raise ValidationError(field_name, "Year must be between 1500 and 2100")

    return parsed
  except (ValueError, TypeError):
    raise ValidationError(field_name, "Date must be in YYYY-MM-DD format")


def validate_death_date(
  death_date: Optional[str],
  birth_date: Optional[date],
  birth_year: Optional[int]
) -> Optional[date]:
  """Validate death date is not before birth date/year."""
  if death_date is None or death_date == "":
    return None

  parsed = validate_date(death_date, "death_date")

  if parsed:
    if birth_date and parsed < birth_date:
      raise ValidationError("death_date", "Death date cannot be before birth date")
    elif birth_year and parsed.year < birth_year:
      raise ValidationError("death_date", "Death date cannot be before birth year")

  return parsed


def validate_city(city: Optional[str]) -> Optional[str]:
  """Validate and normalize a city name."""
  if city is None or city == "":
    return None

  city = city.strip()
  if len(city) > 100:
    raise ValidationError("birth_city", "City name cannot exceed 100 characters")

  return city


class Person:
  """Represents a person in the family tree."""

  def __init__(
    self,
    id: int,
    name: str,
    birth_year: Optional[int] = None,
    death_year: Optional[int] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    death_date: Optional[str] = None,
    birth_city: Optional[str] = None
  ):
    self.id = id
    self.name = validate_name(name)
    self.birth_year = validate_year(birth_year, "birth_year")
    self.birth_date = validate_date(birth_date, "birth_date")
    self.death_year = validate_death_year(death_year, birth_year)
    self.death_date = validate_death_date(death_date, self.birth_date, self.birth_year)
    self.gender = validate_gender(gender)
    self.birth_city = validate_city(birth_city)
    self.parent_ids: list[int] = []
    self.spouse_ids: list[int] = []
    self.child_ids: list[int] = []

  def to_dict(self) -> dict:
    """Convert Person to dictionary for JSON serialization."""
    return {
      "id": self.id,
      "name": self.name,
      "birth_year": self.birth_year,
      "death_year": self.death_year,
      "gender": self.gender,
      "birth_date": self.birth_date.isoformat() if self.birth_date else None,
      "death_date": self.death_date.isoformat() if self.death_date else None,
      "birth_city": self.birth_city,
      "parent_ids": self.parent_ids,
      "spouse_ids": self.spouse_ids,
      "child_ids": self.child_ids
    }

  @classmethod
  def from_dict(cls, data: dict) -> "Person":
    """Create Person from dictionary (JSON deserialization)."""
    person = cls(
      id=data["id"],
      name=data["name"],
      birth_year=data.get("birth_year"),
      death_year=data.get("death_year"),
      gender=data.get("gender"),
      birth_date=data.get("birth_date"),
      death_date=data.get("death_date"),
      birth_city=data.get("birth_city")
    )
    person.parent_ids = data.get("parent_ids", [])
    person.spouse_ids = data.get("spouse_ids", [])
    person.child_ids = data.get("child_ids", [])
    return person

  def __str__(self) -> str:
    years = ""
    if self.birth_date:
      death = self.death_date.isoformat() if self.death_date else "present"
      years = f" ({self.birth_date.isoformat()}-{death})"
    elif self.birth_year:
      death = self.death_year if self.death_year else "present"
      years = f" ({self.birth_year}-{death})"
    gender_str = f" [{self.gender}]" if self.gender else ""
    city_str = f" from {self.birth_city}" if self.birth_city else ""
    return f"{self.name}{years}{gender_str}{city_str}"
