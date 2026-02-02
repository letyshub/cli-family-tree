"""
Family Tree Package

A Rich-based console application for managing family trees.
"""

from family_tree.models import Person, ValidationError
from family_tree.tree import FamilyTree
from family_tree.cli import FamilyTreeCLI

__all__ = ["Person", "FamilyTree", "FamilyTreeCLI", "ValidationError"]
