"""Tests for family_tree.tree module."""

import json
import os
import tempfile

import pytest

from family_tree.models import ValidationError
from family_tree.tree import FamilyTree


@pytest.fixture
def tree():
  return FamilyTree()


@pytest.fixture
def family(tree):
  """A small family: parent, spouse, two children."""
  parent = tree.add_person("John", birth_year=1950, gender="M")
  spouse = tree.add_person("Mary", birth_year=1952, gender="F")
  child1 = tree.add_person("Mike", birth_year=1975, gender="M")
  child2 = tree.add_person("Jane", birth_year=1978, gender="F")
  tree.add_spouse(parent.id, spouse.id)
  tree.add_parent_child(parent.id, child1.id)
  tree.add_parent_child(parent.id, child2.id)
  tree.add_parent_child(spouse.id, child1.id)
  tree.add_parent_child(spouse.id, child2.id)
  return {"parent": parent, "spouse": spouse, "child1": child1, "child2": child2}


class TestAddPerson:
  def test_basic(self, tree):
    p = tree.add_person("Alice")
    assert p.id == 1
    assert p.name == "Alice"
    assert tree.get_person(1) is p

  def test_increments_id(self, tree):
    p1 = tree.add_person("A")
    p2 = tree.add_person("B")
    assert p1.id == 1
    assert p2.id == 2
    assert tree.next_id == 3

  def test_with_all_fields(self, tree):
    p = tree.add_person(
      "Bob", birth_year=1990, death_year=2050,
      gender="M", birth_date="1990-03-15", birth_city="NYC"
    )
    assert p.birth_year == 1990
    assert p.gender == "M"
    assert p.birth_city == "NYC"

  def test_invalid_name_raises(self, tree):
    with pytest.raises(ValidationError):
      tree.add_person("")


class TestGetPerson:
  def test_found(self, tree):
    p = tree.add_person("Test")
    assert tree.get_person(p.id) is p

  def test_not_found(self, tree):
    assert tree.get_person(999) is None


class TestFindByName:
  def test_exact_match(self, tree):
    tree.add_person("Alice Smith")
    results = tree.find_by_name("Alice Smith")
    assert len(results) == 1

  def test_partial_match(self, tree):
    tree.add_person("Alice Smith")
    tree.add_person("Bob Smith")
    results = tree.find_by_name("Smith")
    assert len(results) == 2

  def test_case_insensitive(self, tree):
    tree.add_person("Alice")
    results = tree.find_by_name("alice")
    assert len(results) == 1

  def test_no_match(self, tree):
    tree.add_person("Alice")
    results = tree.find_by_name("Bob")
    assert len(results) == 0


class TestAddParentChild:
  def test_basic(self, tree):
    parent = tree.add_person("Parent")
    child = tree.add_person("Child")
    p, c = tree.add_parent_child(parent.id, child.id)
    assert child.id in p.child_ids
    assert parent.id in c.parent_ids

  def test_self_relationship_raises(self, tree):
    p = tree.add_person("Self")
    with pytest.raises(ValueError, match="self"):
      tree.add_parent_child(p.id, p.id)

  def test_nonexistent_parent_raises(self, tree):
    child = tree.add_person("Child")
    with pytest.raises(ValueError, match="Parent not found"):
      tree.add_parent_child(999, child.id)

  def test_nonexistent_child_raises(self, tree):
    parent = tree.add_person("Parent")
    with pytest.raises(ValueError, match="Child not found"):
      tree.add_parent_child(parent.id, 999)

  def test_idempotent(self, tree):
    parent = tree.add_person("Parent")
    child = tree.add_person("Child")
    tree.add_parent_child(parent.id, child.id)
    tree.add_parent_child(parent.id, child.id)
    assert parent.child_ids.count(child.id) == 1
    assert child.parent_ids.count(parent.id) == 1


class TestAddSpouse:
  def test_basic(self, tree):
    p1 = tree.add_person("Person1")
    p2 = tree.add_person("Person2")
    r1, r2 = tree.add_spouse(p1.id, p2.id)
    assert p2.id in r1.spouse_ids
    assert p1.id in r2.spouse_ids

  def test_self_relationship_raises(self, tree):
    p = tree.add_person("Self")
    with pytest.raises(ValueError, match="self"):
      tree.add_spouse(p.id, p.id)

  def test_nonexistent_raises(self, tree):
    p = tree.add_person("Exists")
    with pytest.raises(ValueError):
      tree.add_spouse(p.id, 999)

  def test_idempotent(self, tree):
    p1 = tree.add_person("A")
    p2 = tree.add_person("B")
    tree.add_spouse(p1.id, p2.id)
    tree.add_spouse(p1.id, p2.id)
    assert p1.spouse_ids.count(p2.id) == 1


class TestRemovePerson:
  def test_basic(self, tree):
    p = tree.add_person("ToRemove")
    removed = tree.remove_person(p.id)
    assert removed.name == "ToRemove"
    assert tree.get_person(p.id) is None

  def test_cleans_relationships(self, tree, family):
    child1 = family["child1"]
    parent = family["parent"]
    tree.remove_person(child1.id)
    assert child1.id not in parent.child_ids

  def test_nonexistent_raises(self, tree):
    with pytest.raises(ValueError, match="not found"):
      tree.remove_person(999)


class TestGetAllSorted:
  def test_sorted_alphabetically(self, tree):
    tree.add_person("Charlie")
    tree.add_person("Alice")
    tree.add_person("Bob")
    result = tree.get_all_sorted()
    names = [p.name for p in result]
    assert names == ["Alice", "Bob", "Charlie"]

  def test_empty_tree(self, tree):
    assert tree.get_all_sorted() == []


class TestGetPersonDetails:
  def test_returns_all_relationships(self, tree, family):
    details = tree.get_person_details(family["child1"].id)
    assert details["person"].name == "Mike"
    parent_names = [p.name for p in details["parents"]]
    assert "John" in parent_names
    assert "Mary" in parent_names
    sibling_names = [s.name for s in details["siblings"]]
    assert "Jane" in sibling_names

  def test_nonexistent_raises(self, tree):
    with pytest.raises(ValueError, match="not found"):
      tree.get_person_details(999)

  def test_no_relationships(self, tree):
    p = tree.add_person("Alone")
    details = tree.get_person_details(p.id)
    assert details["parents"] == []
    assert details["spouses"] == []
    assert details["children"] == []
    assert details["siblings"] == []


class TestGetSiblings:
  def test_siblings_found(self, tree, family):
    siblings = tree._get_siblings(family["child1"].id)
    assert len(siblings) == 1
    assert siblings[0].name == "Jane"

  def test_no_parents_no_siblings(self, tree):
    p = tree.add_person("Orphan")
    assert tree._get_siblings(p.id) == []

  def test_nonexistent_person(self, tree):
    assert tree._get_siblings(999) == []


class TestGetTreeData:
  def test_empty_tree(self, tree):
    assert tree.get_tree_data() == []

  def test_with_family(self, tree, family):
    data = tree.get_tree_data()
    assert len(data) >= 1
    root = data[0]
    assert root["person"].name == "John"
    assert not root["truncated"]

  def test_with_root_id(self, tree, family):
    data = tree.get_tree_data(root_id=family["child1"].id)
    assert len(data) == 1
    assert data[0]["person"].name == "Mike"

  def test_invalid_root_raises(self, tree, family):
    with pytest.raises(ValueError, match="not found"):
      tree.get_tree_data(root_id=999)

  def test_no_roots_uses_first(self, tree):
    """When all people have parents, use the first person as root."""
    p1 = tree.add_person("A")
    p2 = tree.add_person("B")
    tree.add_parent_child(p2.id, p1.id)
    p2.parent_ids.append(999)  # Fake parent to make p2 non-root too
    data = tree.get_tree_data()
    assert len(data) >= 1

  def test_cycle_detection(self, tree):
    """Cycles are handled with truncated flag."""
    p1 = tree.add_person("A")
    p2 = tree.add_person("B")
    tree.add_parent_child(p1.id, p2.id)
    p1.parent_ids.append(p2.id)
    p2.child_ids.append(p1.id)
    data = tree.get_tree_data(root_id=p1.id)
    assert data[0]["truncated"] is False


class TestSaveLoad:
  def test_save_and_load(self, tree):
    tree.add_person("Alice", birth_year=1990, gender="F")
    tree.add_person("Bob", birth_year=1985, gender="M")
    tree.add_spouse(1, 2)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
      tmpfile = f.name

    try:
      tree.save(tmpfile)
      new_tree = FamilyTree()
      result = new_tree.load(tmpfile)
      assert result is True
      assert len(new_tree.people) == 2
      assert new_tree.get_person(1).name == "Alice"
      assert 2 in new_tree.get_person(1).spouse_ids
    finally:
      os.unlink(tmpfile)

  def test_load_nonexistent_file(self, tree):
    assert tree.load("nonexistent_file.json") is False

  def test_load_invalid_json(self, tree):
    with tempfile.NamedTemporaryFile(
      mode="w", suffix=".json", delete=False
    ) as f:
      f.write("not json")
      tmpfile = f.name

    try:
      with pytest.raises(ValueError, match="Error loading"):
        tree.load(tmpfile)
    finally:
      os.unlink(tmpfile)

  def test_save_returns_true(self, tree):
    tree.add_person("Test")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
      tmpfile = f.name
    try:
      assert tree.save(tmpfile) is True
    finally:
      os.unlink(tmpfile)


class TestUpdatePerson:
  def test_update_name(self, tree):
    p = tree.add_person("Old Name")
    updated = tree.update_person(p.id, name="New Name")
    assert updated.name == "New Name"

  def test_update_multiple_fields(self, tree):
    p = tree.add_person("Test", birth_year=1990)
    updated = tree.update_person(
      p.id, name="Updated", gender="F", birth_city="Paris"
    )
    assert updated.name == "Updated"
    assert updated.gender == "F"
    assert updated.birth_city == "Paris"

  def test_update_nonexistent_raises(self, tree):
    with pytest.raises(ValueError, match="not found"):
      tree.update_person(999, name="Nope")

  def test_update_birth_year(self, tree):
    p = tree.add_person("Test")
    tree.update_person(p.id, birth_year=1985)
    assert p.birth_year == 1985

  def test_update_birth_date(self, tree):
    p = tree.add_person("Test")
    tree.update_person(p.id, birth_date="1985-06-15")
    from datetime import date
    assert p.birth_date == date(1985, 6, 15)

  def test_update_death_year(self, tree):
    p = tree.add_person("Test", birth_year=1900)
    tree.update_person(p.id, death_year=1980)
    assert p.death_year == 1980

  def test_update_death_date(self, tree):
    p = tree.add_person("Test", birth_date="1900-01-01")
    tree.update_person(p.id, death_date="1980-12-31")
    from datetime import date
    assert p.death_date == date(1980, 12, 31)

  def test_clear_gender(self, tree):
    p = tree.add_person("Test", gender="M")
    tree.update_person(p.id, gender="")
    assert p.gender is None

  def test_clear_birth_city(self, tree):
    p = tree.add_person("Test", birth_city="NYC")
    tree.update_person(p.id, birth_city="")
    assert p.birth_city is None

  def test_clear_birth_date(self, tree):
    p = tree.add_person("Test", birth_date="1990-01-01")
    tree.update_person(p.id, birth_date="")
    assert p.birth_date is None

  def test_clear_death_date(self, tree):
    p = tree.add_person("Test", birth_date="1900-01-01", death_date="1980-01-01")
    tree.update_person(p.id, death_date="")
    assert p.death_date is None
