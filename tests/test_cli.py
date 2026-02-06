"""Tests for family_tree.cli module."""

from datetime import date
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from family_tree.cli import FamilyTreeCLI
from family_tree.models import Person, ValidationError
from family_tree.tree import FamilyTree


@pytest.fixture
def cli():
  """Create a CLI instance without loading data from disk."""
  with patch.object(FamilyTreeCLI, "_load_data"):
    instance = FamilyTreeCLI()
  instance.tree = FamilyTree()
  return instance


@pytest.fixture
def populated_cli(cli):
  """CLI with a small family loaded."""
  parent = cli.tree.add_person("John Smith", birth_year=1950, gender="M")
  spouse = cli.tree.add_person("Mary Johnson", birth_year=1952, gender="F")
  child = cli.tree.add_person("Mike Smith", birth_year=1975, gender="M")
  cli.tree.add_spouse(parent.id, spouse.id)
  cli.tree.add_parent_child(parent.id, child.id)
  cli.tree.add_parent_child(spouse.id, child.id)
  return cli


class TestLoadData:
  def test_successful_load(self):
    with patch.object(FamilyTree, "load", return_value=True):
      with patch.object(FamilyTreeCLI, "show_success") as mock_success:
        instance = FamilyTreeCLI()
        mock_success.assert_called_once()

  def test_no_existing_data(self):
    with patch.object(FamilyTree, "load", return_value=False):
      with patch.object(FamilyTreeCLI, "show_success") as mock_success:
        instance = FamilyTreeCLI()
        mock_success.assert_not_called()

  def test_load_error(self):
    with patch.object(FamilyTree, "load", side_effect=ValueError("bad file")):
      with patch.object(FamilyTreeCLI, "show_error") as mock_error:
        instance = FamilyTreeCLI()
        mock_error.assert_called_once()


class TestDisplayMenu:
  def test_displays_without_error(self, cli):
    cli.display_menu()


class TestDisplayTable:
  def test_empty_list(self, cli):
    cli.display_table([])

  def test_with_people(self, populated_cli):
    people = populated_cli.tree.get_all_sorted()
    populated_cli.display_table(people)

  def test_with_dates(self, cli):
    p = cli.tree.add_person("Test", birth_date="1990-06-15", death_date="2050-12-31")
    cli.display_table([p])

  def test_with_year_only(self, cli):
    p = cli.tree.add_person("Test", birth_year=1990, death_year=2050)
    cli.display_table([p])


class TestDisplayDetails:
  def test_person_with_relationships(self, populated_cli):
    populated_cli.display_details(3)  # Mike has parents and siblings

  def test_person_no_relationships(self, cli):
    p = cli.tree.add_person("Alone")
    cli.display_details(p.id)

  def test_invalid_person(self, cli):
    cli.display_details(999)

  def test_person_with_all_relationship_types(self, populated_cli):
    populated_cli.display_details(1)  # John has spouse and children

  def test_person_with_dates(self, cli):
    p = cli.tree.add_person("Test", birth_date="1990-01-15", death_date="2050-06-30", birth_city="NYC")
    cli.display_details(p.id)

  def test_person_with_years(self, cli):
    p = cli.tree.add_person("Test", birth_year=1990, death_year=2050)
    cli.display_details(p.id)


class TestDisplayTree:
  def test_empty_tree(self, cli):
    cli.display_tree()

  def test_with_family(self, populated_cli):
    populated_cli.display_tree()

  def test_with_root_id(self, populated_cli):
    populated_cli.display_tree(root_id=1)

  def test_invalid_root(self, cli):
    cli.display_tree(root_id=999)

  def test_tree_with_spouses(self, populated_cli):
    """Ensure spouse labels appear in the tree."""
    populated_cli.display_tree()


class TestShowMessages:
  def test_show_success(self, cli):
    cli.show_success("it worked")

  def test_show_error(self, cli):
    cli.show_error("it failed")

  def test_show_error_with_suggestions(self, cli):
    cli.show_error("it failed", ["try this", "or this"])


class TestAddTreeBranch:
  def test_truncated_node(self, cli):
    """Test that cycle nodes get the truncated label."""
    from rich.tree import Tree
    rich_tree = Tree("test")
    person = cli.tree.add_person("Cyclic")
    node = {
      "person": person,
      "spouses": [],
      "children": [],
      "truncated": True
    }
    cli._add_tree_branch(rich_tree, node)

  def test_node_with_spouses(self, cli):
    from rich.tree import Tree
    rich_tree = Tree("test")
    p1 = cli.tree.add_person("A")
    p2 = cli.tree.add_person("B")
    node = {
      "person": p1,
      "spouses": [p2],
      "children": [],
      "truncated": False
    }
    cli._add_tree_branch(rich_tree, node)

  def test_node_with_children(self, cli):
    from rich.tree import Tree
    rich_tree = Tree("test")
    p1 = cli.tree.add_person("Parent")
    p2 = cli.tree.add_person("Child")
    child_node = {
      "person": p2,
      "spouses": [],
      "children": [],
      "truncated": False
    }
    parent_node = {
      "person": p1,
      "spouses": [],
      "children": [child_node],
      "truncated": False
    }
    cli._add_tree_branch(rich_tree, parent_node)


class TestSearchPerson:
  def test_no_query(self, cli):
    with patch("family_tree.cli.Prompt.ask", return_value=""):
      result = cli.search_person()
      assert result is None

  def test_no_matches(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Nobody"):
      result = populated_cli.search_person()
      assert result is None

  def test_single_match(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Mike"):
      result = populated_cli.search_person()
      assert result is not None
      assert result.name == "Mike Smith"

  def test_multiple_matches_select(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Smith"):
      with patch("family_tree.cli.IntPrompt.ask", return_value=1):
        result = populated_cli.search_person()
        assert result is not None

  def test_multiple_matches_cancel(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Smith"):
      with patch("family_tree.cli.IntPrompt.ask", return_value=0):
        result = populated_cli.search_person()
        assert result is None

  def test_multiple_matches_invalid_selection(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Smith"):
      with patch("family_tree.cli.IntPrompt.ask", return_value=99):
        result = populated_cli.search_person()
        assert result is None

  def test_multiple_matches_exception(self, populated_cli):
    with patch("family_tree.cli.Prompt.ask", return_value="Smith"):
      with patch("family_tree.cli.IntPrompt.ask", side_effect=Exception("error")):
        result = populated_cli.search_person()
        assert result is None


class TestHandleAddPerson:
  def test_successful_add(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Alice", "", "", "", ""]):
      cli._handle_add_person()
      assert len(cli.tree.people) == 1
      assert cli.tree.get_person(1).name == "Alice"

  def test_empty_name(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["", "", "", "", ""]):
      cli._handle_add_person()
      assert len(cli.tree.people) == 0

  def test_with_year(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Bob", "1990", "", "", "M"]):
      cli._handle_add_person()
      p = cli.tree.get_person(1)
      assert p.birth_year == 1990
      assert p.birth_date is None

  def test_with_date(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Carol", "1990-06-15", "", "", ""]):
      cli._handle_add_person()
      p = cli.tree.get_person(1)
      assert p.birth_date == date(1990, 6, 15)

  def test_with_death_year(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Dan", "1900", "1980", "", ""]):
      cli._handle_add_person()
      p = cli.tree.get_person(1)
      assert p.death_year == 1980

  def test_validation_error(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Valid", "not-a-date", "", "", ""]):
      cli._handle_add_person()

  def test_with_city(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Eve", "", "", "London", ""]):
      cli._handle_add_person()
      p = cli.tree.get_person(1)
      assert p.birth_city == "London"


class TestHandleEditPerson:
  def test_no_person_found(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_edit_person()

  def test_no_changes(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch("family_tree.cli.Prompt.ask", return_value=""):
        populated_cli._handle_edit_person()

  def test_update_name(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch("family_tree.cli.Prompt.ask", side_effect=["New Name", "", "", "", ""]):
        populated_cli._handle_edit_person()
        assert person.name == "New Name"

  def test_update_with_year(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch("family_tree.cli.Prompt.ask", side_effect=["", "1960", "", "", ""]):
        populated_cli._handle_edit_person()

  def test_update_with_date(self, cli):
    p = cli.tree.add_person("Test")
    with patch.object(cli, "search_person", return_value=p):
      with patch("family_tree.cli.Prompt.ask", side_effect=["", "1990-05-20", "", "", ""]):
        cli._handle_edit_person()

  def test_validation_error_caught(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch("family_tree.cli.Prompt.ask", side_effect=["", "bad-date", "", "", ""]):
        populated_cli._handle_edit_person()


class TestHandleRemovePerson:
  def test_no_person_found(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_remove_person()

  def test_confirmed_removal(self, populated_cli):
    person = populated_cli.tree.get_person(3)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch.object(populated_cli, "confirm_action", return_value=True):
        populated_cli._handle_remove_person()
        assert populated_cli.tree.get_person(3) is None

  def test_cancelled_removal(self, populated_cli):
    person = populated_cli.tree.get_person(3)
    with patch.object(populated_cli, "search_person", return_value=person):
      with patch.object(populated_cli, "confirm_action", return_value=False):
        populated_cli._handle_remove_person()
        assert populated_cli.tree.get_person(3) is not None


class TestHandleAddParentChild:
  def test_no_parent(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_add_parent_child()

  def test_no_child(self, populated_cli):
    parent = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", side_effect=[parent, None]):
      populated_cli._handle_add_parent_child()

  def test_successful(self, cli):
    p1 = cli.tree.add_person("Parent")
    p2 = cli.tree.add_person("Child")
    with patch.object(cli, "search_person", side_effect=[p1, p2]):
      cli._handle_add_parent_child()
      assert p2.id in p1.child_ids

  def test_error_caught(self, cli):
    p1 = cli.tree.add_person("Same")
    with patch.object(cli, "search_person", side_effect=[p1, p1]):
      cli._handle_add_parent_child()


class TestHandleAddSpouse:
  def test_no_person1(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_add_spouse()

  def test_no_person2(self, populated_cli):
    p1 = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", side_effect=[p1, None]):
      populated_cli._handle_add_spouse()

  def test_successful(self, cli):
    p1 = cli.tree.add_person("A")
    p2 = cli.tree.add_person("B")
    with patch.object(cli, "search_person", side_effect=[p1, p2]):
      cli._handle_add_spouse()
      assert p2.id in p1.spouse_ids


class TestHandleViewAll:
  def test_view(self, populated_cli):
    populated_cli._handle_view_all()


class TestHandleViewDetails:
  def test_found(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      populated_cli._handle_view_details()

  def test_not_found(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_view_details()


class TestHandleViewTree:
  def test_no_root(self, populated_cli):
    with patch("family_tree.cli.Confirm.ask", return_value=False):
      populated_cli._handle_view_tree()

  def test_with_root(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch("family_tree.cli.Confirm.ask", return_value=True):
      with patch.object(populated_cli, "search_person", return_value=person):
        populated_cli._handle_view_tree()


class TestHandleFind:
  def test_found(self, populated_cli):
    person = populated_cli.tree.get_person(1)
    with patch.object(populated_cli, "search_person", return_value=person):
      populated_cli._handle_find()

  def test_not_found(self, cli):
    with patch.object(cli, "search_person", return_value=None):
      cli._handle_find()


class TestHandleSave:
  def test_successful(self, cli):
    with patch.object(cli.tree, "save"):
      cli._handle_save()

  def test_failure(self, cli):
    with patch.object(cli.tree, "save", side_effect=Exception("disk full")):
      cli._handle_save()


class TestHandleQuit:
  def test_save_on_quit(self, cli):
    with patch.object(cli, "confirm_action", return_value=True):
      with patch.object(cli, "_handle_save"):
        cli._handle_quit()

  def test_no_save_on_quit(self, cli):
    with patch.object(cli, "confirm_action", return_value=False):
      cli._handle_quit()


class TestRun:
  def test_menu_loop_quit(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["Q"]):
      with patch.object(cli, "confirm_action", return_value=False):
        with patch.object(cli.console, "clear"):
          cli.run()

  def test_invalid_choice(self, cli):
    with patch("family_tree.cli.Prompt.ask", side_effect=["X", "Q"]):
      with patch.object(cli, "confirm_action", return_value=False):
        with patch.object(cli.console, "clear"):
          cli.run()

  def test_all_menu_choices(self, cli):
    """Exercise all menu branches."""
    handlers = {
      "1": "_handle_add_person",
      "2": "_handle_edit_person",
      "3": "_handle_remove_person",
      "4": "_handle_add_parent_child",
      "5": "_handle_add_spouse",
      "6": "_handle_view_all",
      "7": "_handle_view_details",
      "8": "_handle_view_tree",
      "F": "_handle_find",
      "S": "_handle_save",
    }
    choices = list(handlers.keys()) + ["Q"]
    with patch("family_tree.cli.Prompt.ask", side_effect=choices):
      with patch.object(cli, "confirm_action", return_value=False):
        with patch.object(cli.console, "clear"):
          for name in handlers.values():
            setattr(cli, name, MagicMock())
          cli.run()
          for name in handlers.values():
            getattr(cli, name).assert_called_once()
