#!/usr/bin/env python3
"""
Family Tree Manager - Entry Point

A Rich-based console application for managing family trees.
"""

from family_tree import FamilyTreeCLI


def main():
  cli = FamilyTreeCLI()
  cli.run()


if __name__ == "__main__":
  main()
