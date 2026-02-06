# Family Tree CLI

A command-line application to manage and visualize family trees with relationships.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![No Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen.svg)
![Tests](https://github.com/letyshub/cli-family-tree/actions/workflows/test.yml/badge.svg)

## Overview

Family Tree CLI is a lightweight, zero-dependency Python application that lets you create, manage, and visualize your family tree directly from the terminal. Track family members across generations, define relationships, and display hierarchical family structures with ease.

## Features

- **Person Management** - Add, edit, and remove family members with details (name, birth/death year, gender)
- **Relationship Tracking** - Define parent-child and spouse relationships
- **Tree Visualization** - Display family trees as hierarchical ASCII art
- **Search** - Find family members by name
- **Persistent Storage** - Automatic JSON-based data persistence
- **Zero Dependencies** - Built with Python standard library only

## Demo

```
==================================================
  FAMILY TREE MANAGER
==================================================

Commands:
  1. Add person
  2. Add parent-child relationship
  3. Add spouse relationship
  4. View all members
  5. View person details
  6. Display family tree
  7. Search by name
  8. Edit person
  9. Remove person
  10. Save
  0. Save & Exit
```

### Tree Visualization

```
==================================================
FAMILY TREE
==================================================
├── John Smith (1950-present) [M] ⚭ Mary Johnson
  ├── Michael Smith (1975-present) [M] ⚭ Sarah Davis
    ├── Emma Smith (2005-present) [F]
    ├── James Smith (2008-present) [M]
  ├── Jennifer Smith (1978-present) [F]
==================================================
```

### Person Details

```
==================================================
DETAILS: Michael Smith (1975-present) [M]
==================================================
Parents:
  • John Smith (1950-present) [M]
  • Mary Johnson (1952-present) [F]
Spouse(s):
  ⚭ Sarah Davis (1977-present) [F]
Children:
  • Emma Smith (2005-present) [F]
  • James Smith (2008-present) [M]
Siblings:
  • Jennifer Smith (1978-present) [F]
==================================================
```

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/cli-family-tree.git
    cd cli-family-tree
    ```

2. **Run the application**
    ```bash
    python family_tree.py
    ```

That's it! No dependencies to install.

## Requirements

- Python 3.9 or higher

## Usage

### Adding Family Members

```
Enter choice: 1

--- Add New Person ---
Name: John Smith
Birth year (or Enter to skip): 1950
Death year (or Enter to skip):
Gender (M/F/Other, or Enter to skip): M
✓ Added: John Smith (1950-present) [M] (ID: 1)
```

### Creating Relationships

```
Enter choice: 2

--- Add Parent-Child Relationship ---
Parent ID: 1
Child ID: 2
✓ Added relationship: John Smith is parent of Michael Smith
```

### Searching

```
Enter choice: 7
Search name: smith

Found 4 match(es):
  [1] John Smith (1950-present) [M]
  [2] Michael Smith (1975-present) [M]
  [3] Emma Smith (2005-present) [F]
  [4] James Smith (2008-present) [M]
```

## Data Storage

Family data is automatically saved to `family_tree_data.json` in the application directory. The file is human-readable and can be manually edited if needed.

```json
{
    "next_id": 3,
    "people": [
        {
            "id": 1,
            "name": "John Smith",
            "birth_year": 1950,
            "death_year": null,
            "gender": "M",
            "parent_ids": [],
            "spouse_ids": [2],
            "child_ids": [3]
        }
    ]
}
```

## Project Structure

```
cli-family-tree/
├── family_tree.py          # Main application
├── family_tree_data.json   # Data storage (auto-generated)
└── README.md
```

## Architecture

The application uses an object-oriented design with two main classes:

- **`Person`** - Represents a family member with attributes and relationship references
- **`FamilyTree`** - Manages the collection of people and their relationships

All relationships are bidirectional and automatically maintained for data consistency.

## Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Export to GEDCOM format
- [ ] Import from GEDCOM
- [ ] Generate family tree diagrams (PNG/SVG)
- [ ] Add more relationship types (adoptive, step-parents)
- [ ] Web interface

---

Made with Python
