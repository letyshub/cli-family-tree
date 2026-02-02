"""
CLI layer for the Family Tree application using Rich library.

Contains all user interface components and the main menu loop.
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.text import Text
from rich import box

from family_tree.models import Person, ValidationError
from family_tree.tree import FamilyTree


class FamilyTreeCLI:
  """Rich-based CLI interface for the Family Tree application."""

  def __init__(self):
    self.console = Console()
    self.tree = FamilyTree()
    self._load_data()

  def _load_data(self) -> None:
    """Load existing data on startup."""
    try:
      if self.tree.load():
        count = len(self.tree.people)
        self.show_success(f"Loaded {count} family member(s)")
    except ValueError as e:
      self.show_error(str(e))

  def display_menu(self) -> None:
    """Display the categorized main menu."""
    self.console.print()

    menu_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
    menu_table.add_column("Category", style="bold blue")
    menu_table.add_column("Options")

    people_opts = "[cyan]1[/] Add  [cyan]2[/] Edit  [cyan]3[/] Remove"
    rel_opts = "[cyan]4[/] Parent-Child  [cyan]5[/] Spouse"
    view_opts = "[cyan]6[/] All  [cyan]7[/] Details  [cyan]8[/] Tree  [cyan]F[/] Find"
    data_opts = "[cyan]S[/] Save  [cyan]Q[/] Quit"

    menu_table.add_row("[bold blue]People[/]", people_opts)
    menu_table.add_row("[bold blue]Relationships[/]", rel_opts)
    menu_table.add_row("[bold blue]View[/]", view_opts)
    menu_table.add_row("[bold blue]Data[/]", data_opts)

    header = Panel(
      "[bold white]Family Tree Manager[/]",
      box=box.DOUBLE,
      style="blue"
    )
    self.console.print(header)
    self.console.print(menu_table)

  def display_table(self, people: list[Person]) -> None:
    """Display a list of people in a Rich table."""
    if not people:
      self.console.print("[dim]No family members yet.[/]")
      return

    table = Table(title="Family Members", box=box.ROUNDED)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Born", style="dim")
    table.add_column("Died", style="dim")
    table.add_column("Birthplace", style="dim")
    table.add_column("Gender", style="dim")

    for person in people:
      born = ""
      if person.birth_date:
        born = person.birth_date.isoformat()
      elif person.birth_year:
        born = str(person.birth_year)

      died = ""
      if person.death_date:
        died = person.death_date.isoformat()
      elif person.death_year:
        died = str(person.death_year)

      birthplace = person.birth_city or "-"
      gender = person.gender or "-"
      table.add_row(str(person.id), person.name, born, died, birthplace, gender)

    self.console.print(table)

  def display_details(self, person_id: int) -> None:
    """Display detailed information about a person."""
    try:
      details = self.tree.get_person_details(person_id)
      person = details["person"]

      title = person.name
      if person.gender:
        title += f" [{person.gender}]"

      content = Text()

      content.append("Personal Info:\n", style="bold")
      if person.birth_date:
        content.append(f"  Born: {person.birth_date.isoformat()}\n")
      elif person.birth_year:
        content.append(f"  Born: {person.birth_year}\n")

      if person.death_date:
        content.append(f"  Died: {person.death_date.isoformat()}\n")
      elif person.death_year:
        content.append(f"  Died: {person.death_year}\n")

      if person.birth_city:
        content.append(f"  Birthplace: {person.birth_city}\n")

      content.append("\n")

      if details["parents"]:
        content.append("Parents:\n", style="bold")
        for p in details["parents"]:
          content.append(f"  {p}\n")

      if details["spouses"]:
        content.append("Spouse(s):\n", style="bold")
        for s in details["spouses"]:
          content.append(f"  {s}\n")

      if details["children"]:
        content.append("Children:\n", style="bold")
        for c in details["children"]:
          content.append(f"  {c}\n")

      if details["siblings"]:
        content.append("Siblings:\n", style="bold")
        for s in details["siblings"]:
          content.append(f"  {s}\n")

      if not any([details["parents"], details["spouses"], details["children"], details["siblings"]]):
        content.append("[dim]No relationships recorded.[/]")

      panel = Panel(content, title=title, box=box.ROUNDED, border_style="blue")
      self.console.print(panel)

    except ValueError as e:
      self.show_error(str(e))

  def display_tree(self, root_id: Optional[int] = None) -> None:
    """Display the family tree using Rich Tree component."""
    try:
      tree_data = self.tree.get_tree_data(root_id)

      if not tree_data:
        self.console.print("[dim]No family members yet.[/]")
        return

      rich_tree = Tree("[bold blue]Family Tree[/]")

      for root_node in tree_data:
        self._add_tree_branch(rich_tree, root_node)

      self.console.print(rich_tree)

    except ValueError as e:
      self.show_error(str(e))

  def _add_tree_branch(self, parent: Tree, node: dict) -> None:
    """Recursively add branches to the Rich tree."""
    person = node["person"]
    spouses = node["spouses"]

    label = str(person)
    if spouses:
      spouse_names = ", ".join(s.name for s in spouses)
      label += f" [dim]{spouse_names}[/]"

    if node.get("truncated"):
      label += " [yellow](cycle)[/]"

    branch = parent.add(label)

    for child_node in node["children"]:
      self._add_tree_branch(branch, child_node)

  def search_person(self, prompt_text: str = "Search by name") -> Optional[Person]:
    """Search for a person by partial name and let user select."""
    query = Prompt.ask(f"[cyan]{prompt_text}[/]")
    if not query:
      return None

    matches = self.tree.find_by_name(query)

    if not matches:
      self.show_error("No matches found", ["Try a different search term", "Use 'View All' to see everyone"])
      return None

    if len(matches) == 1:
      self.console.print(f"[green]Found:[/] {matches[0]}")
      return matches[0]

    table = Table(title=f"Found {len(matches)} matches", box=box.ROUNDED)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="white")
    table.add_column("Years", style="dim")
    table.add_column("ID", style="dim")

    for i, person in enumerate(matches, 1):
      years = ""
      if person.birth_year:
        death = str(person.death_year) if person.death_year else "present"
        years = f"{person.birth_year}-{death}"
      table.add_row(str(i), person.name, years, str(person.id))

    self.console.print(table)

    try:
      choice = IntPrompt.ask("Select #", default=0)
      if 1 <= choice <= len(matches):
        return matches[choice - 1]
      elif choice == 0:
        return None
      else:
        self.show_error("Invalid selection")
        return None
    except Exception:
      return None

  def show_success(self, message: str) -> None:
    """Display a success message."""
    self.console.print(f"[green]{message}[/]")

  def show_error(self, message: str, suggestions: Optional[list[str]] = None) -> None:
    """Display an error message with optional suggestions."""
    self.console.print(f"[red]{message}[/]")
    if suggestions:
      for suggestion in suggestions:
        self.console.print(f"  [dim]{suggestion}[/]")

  def confirm_action(self, message: str) -> bool:
    """Ask for user confirmation."""
    return Confirm.ask(f"[yellow]{message}[/]")

  def run(self) -> None:
    """Main application loop."""
    self.console.clear()

    while True:
      self.display_menu()

      choice = Prompt.ask("[bold]Enter choice[/]").strip().upper()

      if choice == "1":
        self._handle_add_person()
      elif choice == "2":
        self._handle_edit_person()
      elif choice == "3":
        self._handle_remove_person()
      elif choice == "4":
        self._handle_add_parent_child()
      elif choice == "5":
        self._handle_add_spouse()
      elif choice == "6":
        self._handle_view_all()
      elif choice == "7":
        self._handle_view_details()
      elif choice == "8":
        self._handle_view_tree()
      elif choice == "F":
        self._handle_find()
      elif choice == "S":
        self._handle_save()
      elif choice == "Q":
        self._handle_quit()
        break
      else:
        self.show_error("Invalid choice", ["Enter a number 1-8, F, S, or Q"])

  def _handle_add_person(self) -> None:
    """Handle adding a new person."""
    self.console.print("\n[bold blue]Add New Person[/]")

    try:
      name = Prompt.ask("Name")
      if not name:
        self.show_error("Name is required")
        return

      self.console.print("[dim]For dates: use YYYY-MM-DD format or just year[/]")

      birth_date_str = Prompt.ask("Birth date (YYYY-MM-DD, optional)", default="")
      birth_date = birth_date_str if birth_date_str else None
      birth_year = None
      if birth_date_str and len(birth_date_str) == 4 and birth_date_str.isdigit():
        birth_year = int(birth_date_str)
        birth_date = None

      death_date_str = Prompt.ask("Death date (YYYY-MM-DD, optional)", default="")
      death_date = death_date_str if death_date_str else None
      death_year = None
      if death_date_str and len(death_date_str) == 4 and death_date_str.isdigit():
        death_year = int(death_date_str)
        death_date = None

      birth_city = Prompt.ask("Birth city (optional)", default="")
      birth_city = birth_city if birth_city else None

      gender = Prompt.ask("Gender (M/F/Other, optional)", default="")
      gender = gender if gender else None

      person = self.tree.add_person(
        name, birth_year, death_year, gender,
        birth_date, death_date, birth_city
      )
      self.show_success(f"Added: {person} (ID: {person.id})")

    except ValidationError as e:
      self.show_error(e.message)
    except ValueError as e:
      self.show_error(str(e))

  def _handle_edit_person(self) -> None:
    """Handle editing a person."""
    self.console.print("\n[bold blue]Edit Person[/]")

    person = self.search_person("Search for person to edit")
    if not person:
      return

    self.console.print(f"[dim]Editing: {person}[/]")
    self.console.print("[dim]Press Enter to keep current value, use YYYY-MM-DD for dates[/]")

    try:
      new_name = Prompt.ask(f"Name [{person.name}]", default="")

      current_birth = person.birth_date.isoformat() if person.birth_date else (person.birth_year or '-')
      new_birth = Prompt.ask(f"Birth date [{current_birth}]", default="")

      current_death = person.death_date.isoformat() if person.death_date else (person.death_year or '-')
      new_death = Prompt.ask(f"Death date [{current_death}]", default="")

      new_city = Prompt.ask(f"Birth city [{person.birth_city or '-'}]", default="")
      new_gender = Prompt.ask(f"Gender [{person.gender or '-'}]", default="")

      name = new_name if new_name else None

      birth_year = None
      birth_date = None
      if new_birth:
        if len(new_birth) == 4 and new_birth.isdigit():
          birth_year = int(new_birth)
        else:
          birth_date = new_birth

      death_year = None
      death_date = None
      if new_death:
        if len(new_death) == 4 and new_death.isdigit():
          death_year = int(new_death)
        else:
          death_date = new_death

      birth_city = new_city if new_city else None
      gender = new_gender if new_gender else None

      if any([name, birth_year, birth_date, death_year, death_date, birth_city, gender]):
        updated = self.tree.update_person(
          person.id,
          name=name,
          birth_year=birth_year,
          death_year=death_year,
          gender=gender,
          birth_date=birth_date,
          death_date=death_date,
          birth_city=birth_city
        )
        self.show_success(f"Updated: {updated}")
      else:
        self.console.print("[dim]No changes made[/]")

    except ValidationError as e:
      self.show_error(e.message)
    except ValueError as e:
      self.show_error(str(e))

  def _handle_remove_person(self) -> None:
    """Handle removing a person."""
    self.console.print("\n[bold blue]Remove Person[/]")

    person = self.search_person("Search for person to remove")
    if not person:
      return

    if self.confirm_action(f"Remove {person.name}? This cannot be undone."):
      try:
        removed = self.tree.remove_person(person.id)
        self.show_success(f"Removed: {removed.name}")
      except ValueError as e:
        self.show_error(str(e))

  def _handle_add_parent_child(self) -> None:
    """Handle adding a parent-child relationship."""
    self.console.print("\n[bold blue]Add Parent-Child Relationship[/]")

    parent = self.search_person("Search for parent")
    if not parent:
      return

    child = self.search_person("Search for child")
    if not child:
      return

    try:
      p, c = self.tree.add_parent_child(parent.id, child.id)
      self.show_success(f"{p.name} is now parent of {c.name}")
    except ValueError as e:
      self.show_error(str(e))

  def _handle_add_spouse(self) -> None:
    """Handle adding a spouse relationship."""
    self.console.print("\n[bold blue]Add Spouse Relationship[/]")

    person1 = self.search_person("Search for first person")
    if not person1:
      return

    person2 = self.search_person("Search for second person")
    if not person2:
      return

    try:
      p1, p2 = self.tree.add_spouse(person1.id, person2.id)
      self.show_success(f"{p1.name} {p2.name}")
    except ValueError as e:
      self.show_error(str(e))

  def _handle_view_all(self) -> None:
    """Handle viewing all family members."""
    self.console.print()
    people = self.tree.get_all_sorted()
    self.display_table(people)

  def _handle_view_details(self) -> None:
    """Handle viewing person details."""
    self.console.print("\n[bold blue]View Person Details[/]")

    person = self.search_person()
    if person:
      self.display_details(person.id)

  def _handle_view_tree(self) -> None:
    """Handle viewing the family tree."""
    self.console.print("\n[bold blue]Family Tree View[/]")

    use_root = Confirm.ask("Start from specific person?", default=False)
    root_id = None

    if use_root:
      person = self.search_person("Search for root person")
      if person:
        root_id = person.id

    self.display_tree(root_id)

  def _handle_find(self) -> None:
    """Handle finding/searching for people."""
    self.console.print("\n[bold blue]Find Person[/]")

    person = self.search_person()
    if person:
      self.display_details(person.id)

  def _handle_save(self) -> None:
    """Handle saving data."""
    try:
      self.tree.save()
      self.show_success("Data saved successfully")
    except Exception as e:
      self.show_error(f"Failed to save: {e}")

  def _handle_quit(self) -> None:
    """Handle quitting the application."""
    if self.confirm_action("Save before quitting?"):
      self._handle_save()
    self.console.print("[bold]Goodbye![/]")
