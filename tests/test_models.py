"""Tests for family_tree.models module."""

from datetime import date

import pytest

from family_tree.models import (
  Person,
  ValidationError,
  validate_name,
  validate_year,
  validate_death_year,
  validate_gender,
  validate_date,
  validate_death_date,
  validate_city,
)


class TestValidationError:
  def test_stores_field_and_message(self):
    err = ValidationError("name", "cannot be empty")
    assert err.field == "name"
    assert err.message == "cannot be empty"
    assert "name: cannot be empty" in str(err)


class TestValidateName:
  def test_valid_name(self):
    assert validate_name("John") == "John"

  def test_strips_whitespace(self):
    assert validate_name("  Alice  ") == "Alice"

  def test_empty_string_raises(self):
    with pytest.raises(ValidationError, match="Name cannot be empty"):
      validate_name("")

  def test_whitespace_only_raises(self):
    with pytest.raises(ValidationError, match="Name cannot be empty"):
      validate_name("   ")

  def test_exceeds_100_chars_raises(self):
    with pytest.raises(ValidationError, match="cannot exceed 100"):
      validate_name("A" * 101)

  def test_exactly_100_chars(self):
    name = "A" * 100
    assert validate_name(name) == name


class TestValidateYear:
  def test_valid_year(self):
    assert validate_year(2000, "birth_year") == 2000

  def test_none_returns_none(self):
    assert validate_year(None, "birth_year") is None

  def test_boundary_1500(self):
    assert validate_year(1500, "birth_year") == 1500

  def test_boundary_2100(self):
    assert validate_year(2100, "birth_year") == 2100

  def test_below_range_raises(self):
    with pytest.raises(ValidationError, match="between 1500 and 2100"):
      validate_year(1499, "birth_year")

  def test_above_range_raises(self):
    with pytest.raises(ValidationError, match="between 1500 and 2100"):
      validate_year(2101, "birth_year")

  def test_non_integer_raises(self):
    with pytest.raises(ValidationError, match="must be an integer"):
      validate_year("abc", "birth_year")


class TestValidateDeathYear:
  def test_none_returns_none(self):
    assert validate_death_year(None, 1990) is None

  def test_valid_death_after_birth(self):
    assert validate_death_year(2000, 1990) == 2000

  def test_death_equals_birth(self):
    assert validate_death_year(1990, 1990) == 1990

  def test_death_before_birth_raises(self):
    with pytest.raises(ValidationError, match="cannot be before birth"):
      validate_death_year(1980, 1990)

  def test_birth_year_none(self):
    assert validate_death_year(2000, None) == 2000


class TestValidateGender:
  def test_valid_male(self):
    assert validate_gender("M") == "M"

  def test_valid_female(self):
    assert validate_gender("F") == "F"

  def test_valid_other(self):
    assert validate_gender("Other") == "Other"

  def test_none_returns_none(self):
    assert validate_gender(None) is None

  def test_empty_string_returns_none(self):
    assert validate_gender("") is None

  def test_invalid_raises(self):
    with pytest.raises(ValidationError, match="must be one of"):
      validate_gender("X")


class TestValidateDate:
  def test_valid_date(self):
    result = validate_date("2000-06-15", "birth_date")
    assert result == date(2000, 6, 15)

  def test_none_returns_none(self):
    assert validate_date(None, "birth_date") is None

  def test_empty_string_returns_none(self):
    assert validate_date("", "birth_date") is None

  def test_date_object_passthrough(self):
    d = date(2000, 1, 1)
    assert validate_date(d, "birth_date") is d

  def test_invalid_format_raises(self):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
      validate_date("2000/06/15", "birth_date")

  def test_too_few_parts_raises(self):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
      validate_date("2000-06", "birth_date")

  def test_year_out_of_range_raises(self):
    with pytest.raises(ValidationError, match="between 1500 and 2100"):
      validate_date("1400-01-01", "birth_date")

  def test_invalid_day_raises(self):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
      validate_date("2000-02-30", "birth_date")


class TestValidateDeathDate:
  def test_none_returns_none(self):
    assert validate_death_date(None, None, None) is None

  def test_empty_string_returns_none(self):
    assert validate_death_date("", None, None) is None

  def test_valid_death_date(self):
    result = validate_death_date("2020-01-01", date(2000, 1, 1), 2000)
    assert result == date(2020, 1, 1)

  def test_death_before_birth_date_raises(self):
    with pytest.raises(ValidationError, match="cannot be before birth date"):
      validate_death_date("1999-01-01", date(2000, 1, 1), None)

  def test_death_before_birth_year_raises(self):
    with pytest.raises(ValidationError, match="cannot be before birth year"):
      validate_death_date("1999-01-01", None, 2000)

  def test_no_birth_info(self):
    result = validate_death_date("2020-06-15", None, None)
    assert result == date(2020, 6, 15)


class TestValidateCity:
  def test_valid_city(self):
    assert validate_city("London") == "London"

  def test_strips_whitespace(self):
    assert validate_city("  Paris  ") == "Paris"

  def test_none_returns_none(self):
    assert validate_city(None) is None

  def test_empty_string_returns_none(self):
    assert validate_city("") is None

  def test_exceeds_100_chars_raises(self):
    with pytest.raises(ValidationError, match="cannot exceed 100"):
      validate_city("A" * 101)


class TestPerson:
  def test_basic_creation(self):
    p = Person(1, "John Doe")
    assert p.id == 1
    assert p.name == "John Doe"
    assert p.birth_year is None
    assert p.death_year is None
    assert p.gender is None
    assert p.parent_ids == []
    assert p.spouse_ids == []
    assert p.child_ids == []

  def test_full_creation(self):
    p = Person(
      1, "John Doe",
      birth_year=1990, death_year=2050, gender="M",
      birth_city="London"
    )
    assert p.birth_year == 1990
    assert p.death_year == 2050
    assert p.gender == "M"
    assert p.birth_city == "London"

  def test_creation_with_dates(self):
    p = Person(1, "Jane", birth_date="2000-06-15", death_date="2080-12-31")
    assert p.birth_date == date(2000, 6, 15)
    assert p.death_date == date(2080, 12, 31)

  def test_invalid_name_raises(self):
    with pytest.raises(ValidationError):
      Person(1, "")

  def test_to_dict(self):
    p = Person(1, "Alice", birth_year=1990, gender="F", birth_city="NYC")
    d = p.to_dict()
    assert d["id"] == 1
    assert d["name"] == "Alice"
    assert d["birth_year"] == 1990
    assert d["gender"] == "F"
    assert d["birth_city"] == "NYC"
    assert d["parent_ids"] == []
    assert d["spouse_ids"] == []
    assert d["child_ids"] == []

  def test_to_dict_with_dates(self):
    p = Person(1, "Bob", birth_date="1990-01-15")
    d = p.to_dict()
    assert d["birth_date"] == "1990-01-15"
    assert d["death_date"] is None

  def test_from_dict(self):
    data = {
      "id": 1,
      "name": "Charlie",
      "birth_year": 1985,
      "death_year": None,
      "gender": "M",
      "birth_date": None,
      "death_date": None,
      "birth_city": "Berlin",
      "parent_ids": [2],
      "spouse_ids": [3],
      "child_ids": [4, 5],
    }
    p = Person.from_dict(data)
    assert p.id == 1
    assert p.name == "Charlie"
    assert p.birth_year == 1985
    assert p.gender == "M"
    assert p.birth_city == "Berlin"
    assert p.parent_ids == [2]
    assert p.spouse_ids == [3]
    assert p.child_ids == [4, 5]

  def test_roundtrip_dict(self):
    p = Person(1, "Dana", birth_year=1970, gender="F")
    p.parent_ids = [10]
    p.child_ids = [20, 21]
    restored = Person.from_dict(p.to_dict())
    assert restored.name == p.name
    assert restored.birth_year == p.birth_year
    assert restored.parent_ids == p.parent_ids
    assert restored.child_ids == p.child_ids

  def test_str_with_birth_year(self):
    p = Person(1, "Eve", birth_year=1990, gender="F")
    assert "Eve" in str(p)
    assert "1990" in str(p)
    assert "present" in str(p)
    assert "[F]" in str(p)

  def test_str_with_death_year(self):
    p = Person(1, "Fred", birth_year=1900, death_year=1980)
    s = str(p)
    assert "1900" in s
    assert "1980" in s

  def test_str_with_dates(self):
    p = Person(1, "Grace", birth_date="1990-05-20")
    s = str(p)
    assert "1990-05-20" in s
    assert "present" in s

  def test_str_with_death_date(self):
    p = Person(1, "Hank", birth_date="1900-01-01", death_date="1980-12-31")
    s = str(p)
    assert "1900-01-01" in s
    assert "1980-12-31" in s

  def test_str_with_city(self):
    p = Person(1, "Iris", birth_city="Rome")
    assert "from Rome" in str(p)

  def test_str_minimal(self):
    p = Person(1, "Jake")
    assert str(p) == "Jake"
