#!/usr/bin/env python3
"""
Family Tree MVP Console Application
A simple application to manage and visualize your family tree.
"""

import json
import os
from datetime import datetime
from typing import Optional

DATA_FILE = "family_tree_data.json"


class Person:
    def __init__(self, id: int, name: str, birth_year: Optional[int] = None,
                 death_year: Optional[int] = None, gender: Optional[str] = None):
        self.id = id
        self.name = name
        self.birth_year = birth_year
        self.death_year = death_year
        self.gender = gender
        self.parent_ids: list[int] = []
        self.spouse_ids: list[int] = []
        self.child_ids: list[int] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "gender": self.gender,
            "parent_ids": self.parent_ids,
            "spouse_ids": self.spouse_ids,
            "child_ids": self.child_ids
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        person = cls(
            id=data["id"],
            name=data["name"],
            birth_year=data.get("birth_year"),
            death_year=data.get("death_year"),
            gender=data.get("gender")
        )
        person.parent_ids = data.get("parent_ids", [])
        person.spouse_ids = data.get("spouse_ids", [])
        person.child_ids = data.get("child_ids", [])
        return person

    def __str__(self) -> str:
        years = ""
        if self.birth_year:
            death = self.death_year if self.death_year else "present"
            years = f" ({self.birth_year}-{death})"
        gender_str = f" [{self.gender}]" if self.gender else ""
        return f"{self.name}{years}{gender_str}"


class FamilyTree:
    def __init__(self):
        self.people: dict[int, Person] = {}
        self.next_id = 1

    def add_person(self, name: str, birth_year: Optional[int] = None,
                   death_year: Optional[int] = None, gender: Optional[str] = None) -> Person:
        person = Person(self.next_id, name, birth_year, death_year, gender)
        self.people[self.next_id] = person
        self.next_id += 1
        print(f"✓ Added: {person} (ID: {person.id})")
        return person

    def get_person(self, id: int) -> Optional[Person]:
        return self.people.get(id)

    def find_by_name(self, name: str) -> list[Person]:
        name_lower = name.lower()
        return [p for p in self.people.values() if name_lower in p.name.lower()]

    def add_parent_child(self, parent_id: int, child_id: int) -> bool:
        parent = self.get_person(parent_id)
        child = self.get_person(child_id)
        
        if not parent or not child:
            print("✗ Error: Parent or child not found.")
            return False
        
        if child_id not in parent.child_ids:
            parent.child_ids.append(child_id)
        if parent_id not in child.parent_ids:
            child.parent_ids.append(parent_id)
        
        print(f"✓ Added relationship: {parent.name} is parent of {child.name}")
        return True

    def add_spouse(self, person1_id: int, person2_id: int) -> bool:
        person1 = self.get_person(person1_id)
        person2 = self.get_person(person2_id)
        
        if not person1 or not person2:
            print("✗ Error: One or both persons not found.")
            return False
        
        if person2_id not in person1.spouse_ids:
            person1.spouse_ids.append(person2_id)
        if person1_id not in person2.spouse_ids:
            person2.spouse_ids.append(person1_id)
        
        print(f"✓ Added spouse relationship: {person1.name} ⚭ {person2.name}")
        return True

    def remove_person(self, person_id: int) -> bool:
        person = self.get_person(person_id)
        if not person:
            print("✗ Error: Person not found.")
            return False
        
        # Remove from all relationships
        for other in self.people.values():
            if person_id in other.parent_ids:
                other.parent_ids.remove(person_id)
            if person_id in other.child_ids:
                other.child_ids.remove(person_id)
            if person_id in other.spouse_ids:
                other.spouse_ids.remove(person_id)
        
        del self.people[person_id]
        print(f"✓ Removed: {person.name}")
        return True

    def list_all(self) -> None:
        if not self.people:
            print("No family members yet.")
            return
        
        print("\n" + "=" * 50)
        print("ALL FAMILY MEMBERS")
        print("=" * 50)
        for person in sorted(self.people.values(), key=lambda p: p.name):
            print(f"  [{person.id}] {person}")
        print("=" * 50)

    def show_person_details(self, person_id: int) -> None:
        person = self.get_person(person_id)
        if not person:
            print("✗ Person not found.")
            return
        
        print("\n" + "=" * 50)
        print(f"DETAILS: {person}")
        print("=" * 50)
        
        # Parents
        if person.parent_ids:
            print("Parents:")
            for pid in person.parent_ids:
                parent = self.get_person(pid)
                if parent:
                    print(f"  • {parent}")
        
        # Spouses
        if person.spouse_ids:
            print("Spouse(s):")
            for sid in person.spouse_ids:
                spouse = self.get_person(sid)
                if spouse:
                    print(f"  ⚭ {spouse}")
        
        # Children
        if person.child_ids:
            print("Children:")
            for cid in person.child_ids:
                child = self.get_person(cid)
                if child:
                    print(f"  • {child}")
        
        # Siblings
        siblings = self._get_siblings(person_id)
        if siblings:
            print("Siblings:")
            for sibling in siblings:
                print(f"  • {sibling}")
        
        print("=" * 50)

    def _get_siblings(self, person_id: int) -> list[Person]:
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

    def display_tree(self, root_id: Optional[int] = None) -> None:
        if not self.people:
            print("No family members yet.")
            return
        
        print("\n" + "=" * 50)
        print("FAMILY TREE")
        print("=" * 50)
        
        if root_id:
            root = self.get_person(root_id)
            if root:
                self._print_descendants(root, 0, set())
            else:
                print("✗ Person not found.")
        else:
            # Find roots (people with no parents)
            roots = [p for p in self.people.values() if not p.parent_ids]
            if not roots:
                # If everyone has parents, just pick the first person
                roots = [list(self.people.values())[0]]
            
            for root in roots:
                self._print_descendants(root, 0, set())
                print()
        
        print("=" * 50)

    def _print_descendants(self, person: Person, level: int, visited: set) -> None:
        if person.id in visited:
            return
        visited.add(person.id)
        
        indent = "  " * level
        spouse_str = ""
        if person.spouse_ids:
            spouses = [self.get_person(sid) for sid in person.spouse_ids]
            spouse_names = [s.name for s in spouses if s]
            if spouse_names:
                spouse_str = f" ⚭ {', '.join(spouse_names)}"
        
        print(f"{indent}├── {person}{spouse_str}")
        
        for child_id in person.child_ids:
            child = self.get_person(child_id)
            if child:
                self._print_descendants(child, level + 1, visited)

    def save(self, filename: str = DATA_FILE) -> None:
        data = {
            "next_id": self.next_id,
            "people": [p.to_dict() for p in self.people.values()]
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved to {filename}")

    def load(self, filename: str = DATA_FILE) -> bool:
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
            
            print(f"✓ Loaded {len(self.people)} family members from {filename}")
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error loading file: {e}")
            return False


def get_int_input(prompt: str, allow_empty: bool = False) -> Optional[int]:
    while True:
        value = input(prompt).strip()
        if not value and allow_empty:
            return None
        try:
            return int(value)
        except ValueError:
            if allow_empty:
                return None
            print("Please enter a valid number.")


def main():
    tree = FamilyTree()
    tree.load()
    
    print("\n" + "=" * 50)
    print("  FAMILY TREE MANAGER")
    print("=" * 50)
    
    while True:
        print("\nCommands:")
        print("  1. Add person")
        print("  2. Add parent-child relationship")
        print("  3. Add spouse relationship")
        print("  4. View all members")
        print("  5. View person details")
        print("  6. Display family tree")
        print("  7. Search by name")
        print("  8. Edit person")
        print("  9. Remove person")
        print("  10. Save")
        print("  0. Save & Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            print("\n--- Add New Person ---")
            name = input("Name: ").strip()
            if not name:
                print("✗ Name is required.")
                continue
            birth = get_int_input("Birth year (or Enter to skip): ", allow_empty=True)
            death = get_int_input("Death year (or Enter to skip): ", allow_empty=True)
            gender = input("Gender (M/F/Other, or Enter to skip): ").strip() or None
            tree.add_person(name, birth, death, gender)
        
        elif choice == "2":
            print("\n--- Add Parent-Child Relationship ---")
            tree.list_all()
            parent_id = get_int_input("Parent ID: ")
            child_id = get_int_input("Child ID: ")
            if parent_id and child_id:
                tree.add_parent_child(parent_id, child_id)
        
        elif choice == "3":
            print("\n--- Add Spouse Relationship ---")
            tree.list_all()
            id1 = get_int_input("First person ID: ")
            id2 = get_int_input("Second person ID: ")
            if id1 and id2:
                tree.add_spouse(id1, id2)
        
        elif choice == "4":
            tree.list_all()
        
        elif choice == "5":
            tree.list_all()
            person_id = get_int_input("Enter person ID: ")
            if person_id:
                tree.show_person_details(person_id)
        
        elif choice == "6":
            tree.list_all()
            root_id = get_int_input("Enter root person ID (or Enter for all): ", allow_empty=True)
            tree.display_tree(root_id)
        
        elif choice == "7":
            name = input("Search name: ").strip()
            results = tree.find_by_name(name)
            if results:
                print(f"\nFound {len(results)} match(es):")
                for p in results:
                    print(f"  [{p.id}] {p}")
            else:
                print("No matches found.")
        
        elif choice == "8":
            print("\n--- Edit Person ---")
            tree.list_all()
            person_id = get_int_input("Enter person ID to edit: ")
            person = tree.get_person(person_id) if person_id else None
            if person:
                print(f"Editing: {person}")
                print("(Press Enter to keep current value)")
                
                new_name = input(f"Name [{person.name}]: ").strip()
                if new_name:
                    person.name = new_name
                
                new_birth = input(f"Birth year [{person.birth_year}]: ").strip()
                if new_birth:
                    try:
                        person.birth_year = int(new_birth)
                    except ValueError:
                        pass
                
                new_death = input(f"Death year [{person.death_year}]: ").strip()
                if new_death:
                    try:
                        person.death_year = int(new_death)
                    except ValueError:
                        pass
                
                new_gender = input(f"Gender [{person.gender}]: ").strip()
                if new_gender:
                    person.gender = new_gender
                
                print(f"✓ Updated: {person}")
            else:
                print("✗ Person not found.")
        
        elif choice == "9":
            print("\n--- Remove Person ---")
            tree.list_all()
            person_id = get_int_input("Enter person ID to remove: ")
            if person_id:
                confirm = input("Are you sure? (y/n): ").strip().lower()
                if confirm == "y":
                    tree.remove_person(person_id)
        
        elif choice == "10":
            tree.save()
        
        elif choice == "0":
            tree.save()
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
