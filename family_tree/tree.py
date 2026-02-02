"""
Business logic layer for the Family Tree application.

Contains the FamilyTree class with all CRUD operations.
No print statements - all methods return values or raise exceptions.
"""

import json
import os
from typing import Optional

from family_tree.models import Person, ValidationError

DATA_FILE = "family_tree_data.json"


class FamilyTree:
  """Manages a collection of Person objects and their relationships."""

  def __init__(self):
    self.people: dict[int, Person] = {}
    self.next_id = 1

  def add_person(
    self,
    name: str,
    birth_year: Optional[int] = None,
    death_year: Optional[int] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    death_date: Optional[str] = None,
    birth_city: Optional[str] = None
  ) -> Person:
    """Add a new person to the family tree. Returns the created Person."""
    person = Person(
      self.next_id, name, birth_year, death_year, gender,
      birth_date, death_date, birth_city
    )
    self.people[self.next_id] = person
    self.next_id += 1
    return person

  def get_person(self, id: int) -> Optional[Person]:
    """Retrieve a person by ID. Returns None if not found."""
    return self.people.get(id)

  def find_by_name(self, name: str) -> list[Person]:
    """Find all persons whose name contains the search string (case-insensitive)."""
    name_lower = name.lower()
    return [p for p in self.people.values() if name_lower in p.name.lower()]

  def _validate_not_self(self, id1: int, id2: int, relationship: str) -> None:
    """Validate that a person is not being related to themselves."""
    if id1 == id2:
      raise ValueError(f"Cannot create {relationship} relationship with self")

  def _validate_person_exists(self, person_id: int, role: str) -> Person:
    """Validate that a person exists and return them."""
    person = self.get_person(person_id)
    if not person:
      raise ValueError(f"{role} not found (ID: {person_id})")
    return person

  def add_parent_child(self, parent_id: int, child_id: int) -> tuple[Person, Person]:
    """Add a parent-child relationship. Returns (parent, child) tuple."""
    self._validate_not_self(parent_id, child_id, "parent-child")

    parent = self._validate_person_exists(parent_id, "Parent")
    child = self._validate_person_exists(child_id, "Child")

    if child_id not in parent.child_ids:
      parent.child_ids.append(child_id)
    if parent_id not in child.parent_ids:
      child.parent_ids.append(parent_id)

    return (parent, child)

  def add_spouse(self, person1_id: int, person2_id: int) -> tuple[Person, Person]:
    """Add a spouse relationship. Returns (person1, person2) tuple."""
    self._validate_not_self(person1_id, person2_id, "spouse")

    person1 = self._validate_person_exists(person1_id, "First person")
    person2 = self._validate_person_exists(person2_id, "Second person")

    if person2_id not in person1.spouse_ids:
      person1.spouse_ids.append(person2_id)
    if person1_id not in person2.spouse_ids:
      person2.spouse_ids.append(person1_id)

    return (person1, person2)

  def remove_person(self, person_id: int) -> Person:
    """Remove a person and all their relationships. Returns the removed Person."""
    person = self._validate_person_exists(person_id, "Person")

    for other in self.people.values():
      if person_id in other.parent_ids:
        other.parent_ids.remove(person_id)
      if person_id in other.child_ids:
        other.child_ids.remove(person_id)
      if person_id in other.spouse_ids:
        other.spouse_ids.remove(person_id)

    del self.people[person_id]
    return person

  def get_all_sorted(self) -> list[Person]:
    """Get all persons sorted alphabetically by name."""
    return sorted(self.people.values(), key=lambda p: p.name)

  def get_person_details(self, person_id: int) -> dict:
    """Get detailed information about a person including relationships."""
    person = self._validate_person_exists(person_id, "Person")

    parents = [self.get_person(pid) for pid in person.parent_ids]
    parents = [p for p in parents if p]

    spouses = [self.get_person(sid) for sid in person.spouse_ids]
    spouses = [s for s in spouses if s]

    children = [self.get_person(cid) for cid in person.child_ids]
    children = [c for c in children if c]

    siblings = self._get_siblings(person_id)

    return {
      "person": person,
      "parents": parents,
      "spouses": spouses,
      "children": children,
      "siblings": siblings
    }

  def _get_siblings(self, person_id: int) -> list[Person]:
    """Get all siblings of a person."""
    person = self.get_person(person_id)
    if not person or not person.parent_ids:
      return []

    siblings = set()
    for parent_id in person.parent_ids:
      parent = self.get_person(parent_id)
      if parent:
        for child_id in parent.child_ids:
          if child_id != person_id:
            siblings.add(child_id)

    return [self.get_person(sid) for sid in siblings if self.get_person(sid)]

  def get_tree_data(self, root_id: Optional[int] = None) -> list[dict]:
    """Get tree structure data for visualization."""
    if not self.people:
      return []

    if root_id:
      root = self.get_person(root_id)
      if not root:
        raise ValueError(f"Person not found (ID: {root_id})")
      return [self._build_tree_node(root, set())]
    else:
      roots = [p for p in self.people.values() if not p.parent_ids]
      if not roots:
        roots = [list(self.people.values())[0]]

      return [self._build_tree_node(root, set()) for root in roots]

  def _build_tree_node(self, person: Person, visited: set) -> dict:
    """Build a tree node with descendants."""
    if person.id in visited:
      return {"person": person, "spouses": [], "children": [], "truncated": True}

    visited.add(person.id)

    spouses = [self.get_person(sid) for sid in person.spouse_ids]
    spouses = [s for s in spouses if s]

    children_nodes = []
    for child_id in person.child_ids:
      child = self.get_person(child_id)
      if child:
        children_nodes.append(self._build_tree_node(child, visited))

    return {
      "person": person,
      "spouses": spouses,
      "children": children_nodes,
      "truncated": False
    }

  def save(self, filename: str = DATA_FILE) -> bool:
    """Save the family tree to a JSON file. Returns True on success."""
    data = {
      "next_id": self.next_id,
      "people": [p.to_dict() for p in self.people.values()]
    }
    with open(filename, "w") as f:
      json.dump(data, f, indent=2)
    return True

  def load(self, filename: str = DATA_FILE) -> bool:
    """Load the family tree from a JSON file. Returns True on success."""
    if not os.path.exists(filename):
      return False

    try:
      with open(filename, "r") as f:
        data = json.load(f)

      self.next_id = data.get("next_id", 1)
      self.people = {}
      for person_data in data.get("people", []):
        person = Person.from_dict(person_data)
        self.people[person.id] = person

      return True
    except (json.JSONDecodeError, KeyError) as e:
      raise ValueError(f"Error loading file: {e}")

  def update_person(
    self,
    person_id: int,
    name: Optional[str] = None,
    birth_year: Optional[int] = None,
    death_year: Optional[int] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    death_date: Optional[str] = None,
    birth_city: Optional[str] = None
  ) -> Person:
    """Update a person's details. Returns the updated Person."""
    from family_tree.models import (
      validate_name, validate_year, validate_death_year, validate_gender,
      validate_date, validate_death_date, validate_city
    )

    person = self._validate_person_exists(person_id, "Person")

    if name is not None:
      person.name = validate_name(name)
    if birth_year is not None:
      person.birth_year = validate_year(birth_year, "birth_year")
    if birth_date is not None:
      person.birth_date = validate_date(birth_date, "birth_date") if birth_date else None
    if death_year is not None:
      person.death_year = validate_death_year(death_year, person.birth_year)
    if death_date is not None:
      person.death_date = validate_death_date(death_date, person.birth_date, person.birth_year) if death_date else None
    if gender is not None:
      person.gender = validate_gender(gender) if gender else None
    if birth_city is not None:
      person.birth_city = validate_city(birth_city) if birth_city else None

    return person
