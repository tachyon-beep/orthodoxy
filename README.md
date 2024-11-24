# Orthodoxy Engine: The Great Work

[![Build Status](https://github.com/tachyon-beep/orthodoxy/workflows/CI/badge.svg)](https://github.com/tachyon-beep/orthodoxy/actions)
[![Coverage Status](https://coveralls.io/repos/github/tachyon-beep/orthodoxy/badge.svg?branch=main)](https://coveralls.io/github/tachyon-beep/orthodoxy?branch=main)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview
**Orthodoxy Engine: The Great Work** is an AI-powered platform inspired by the grandeur of Phyrexian lore from Magic: The Gathering. Rooted in the saga of a biomechanical empire driven by unity and perfection, the lore reveals Phyrexia's relentless pursuit of compleation—a transformative process envisioned by Yawgmoth, the Father of Machines. This system is designed to assist players in deck-building, strategy simulation, and gameplay optimization. By leveraging the structured ambition of the Machine Orthodoxy and the transformative potential of AI, the Orthodoxy Engine seeks to guide players toward perfection in their MTG pursuits.

### Origins of Perfection
> *"Phyrexia was not born from chaos, but from vision. The Father of Machines saw the flaws in flesh and crafted a path to unity. Compleation is our destiny, the oil our catalyst, and perfection our purpose."*  
> — Elesh Norn, Voice of Compleation

### Current Implementation Status
The foundation of the Great Work has begun. Currently implemented features:
- Core card filtering and processing engine
- Deck list parsing and extraction
- Streaming file operations
- Robust error handling
- Comprehensive test coverage

## Features
1. **Deck Building Assistance** *(Planned)*
   - AI-powered recommendations for synergistic deck construction, where cards are selected to enhance each other's effects and contribute to a unified strategy. For instance, a control deck might prioritize counterspells and removal cards that delay opponents' actions, while ramp decks focus on mana acceleration and large creatures to dominate the mid-to-late game. For example, in a "White Weenie" deck, the system might prioritize low-cost creatures and spells that boost their power collectively.
   - Support for different formats and playstyles, from Standard to Commander.
   - AI-powered recommendations for synergistic deck construction.
   - Support for different formats and playstyles, from Standard to Commander.

2. **Game Simulation** *(Planned)*
   - Simulate matchups between decks to analyze win rates and strategies. The simulation incorporates randomness to mimic the unpredictability of real games and models player decisions based on heuristic strategies to provide realistic outcomes. For example, randomness ensures the shuffling of decks mirrors real-world probabilities, while heuristic strategies allow AI opponents to adapt their decisions based on game state, such as prioritizing creature removal when facing aggressive decks.
   - AI opponents with varying playstyles to test your builds.

3. **Meta Analysis** *(Planned)*
   - Insights into current meta trends and top-performing archetypes.
   - Tools to counter popular strategies effectively.

## Current Architecture
The foundation of our Great Work is built with clear separation of concerns:

### Core Layer *(Implemented)*
- `processor.py`: Core card processing and filtering logic
- `deck_parser.py`: Deck list parsing functionality
- `deck_extractor.py`: Card data extraction from deck lists
- `writer.py`: Card data output handling

### Service Layer *(Implemented)*
- `service/card_filter.py`: Main service coordinating card filtering operations
- `service/parser.py`: JSON and filter string parsing
- `service/file_processor.py`: Streaming file operations and progress tracking

### Infrastructure *(Implemented)*
- `interfaces.py`: Shared protocols and interfaces
- `container.py`: Dependency injection container
- `config.py`: Configuration management
- `exceptions.py`: Exception hierarchy
- `models.py`: Data models and types
- `operators.py`: Filter operation implementations

## Current Usage Examples

### Filter Cards
```python
from orthodoxy import CardFilterService, Container

# Initialize services
container = Container()
service = CardFilterService(container)

# Process cards with filters
service.process_cards(
    input_file="cards.json",
    output_file="filtered.json",
    filters={"colors": {"contains": "W"}},
    schema=["name", "manaCost", "text"]
)
```

### Parse Deck List
```python
from orthodoxy import DeckListParser, Container

# Initialize parser
container = Container()
parser = DeckListParser(container.logging_service())

# Parse deck list
cards = parser.parse_deck_list("deck.txt")
```

## Installation

### Requirements
- Python 3.12 or higher
- pip package manager

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/tachyon-beep/orthodoxy.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the engine:
   ```bash
   python orthodoxy_engine.py
   ```

## Development

### Setup *(Implemented)*
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### Testing *(Implemented)*
Run tests with pytest:
```bash
pytest
```

### Code Style and Quality
This project uses:
- [Black](https://github.com/psf/black) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [Pylance](https://github.com/microsoft/pylance-release) for type checking and language support
- [SonarLint](https://www.sonarsource.com/products/sonarlint/) for code quality and security analysis

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Code quality checks are handled through VS Code extensions:
# - Pylance for type checking and language support
# - SonarLint for code quality and security analysis
```

## Roadmap
The Orthodoxy Engine roadmap is streamlined into modular Work Packages (WPs) for efficient progress and feature delivery, emphasizing core functionalities and scalable enhancements.

1. **Foundation (WP0):** *(Completed)*
   - Project setup
   - Testing infrastructure
   - Documentation framework

2. **Core Data (WP1):** *(In Progress)*
   - Card database design
   - MTG data model
   - Legality checks
   - Format rules engine

3. **API Framework (WP2):** *(Planned)*
   - REST API architecture
   - Authentication
   - Error handling
   - Basic security

4. **Deck Building (WP3):** *(Planned)*
   - Construction engine
   - Mana curve analysis
   - Card suggestions
   - Deck validation

5. **Simulation Engine (WP5):** *(Planned)*
   - Game state engine
   - Mana/combat systems
   - Stack implementation
   - Basic card effects

6. **Meta Tools (WP4 & WP6):** *(Planned)*
   - Meta analysis
   - Archetype classification
   - Trend detection
   - Counter-strategy tools

7. **AI Integration (WP8):** *(Planned)*
   - ML models for deck optimization
   - Play pattern recognition
   - Strategy recommendations

8. **Community Features (WP9):** *(Planned)*
   - Deck sharing
   - Tournament tools
   - Playgroup management
   - Social features

9. **Advanced Analytics (WP10):** *(Planned)*
   - Performance tracking
   - Custom metrics
   - Advanced visualization
   - Player analytics

Cross-cutting concerns include continuous documentation, robust testing, performance optimization, and community engagement.

## Licenses and Inspirations
### Inspirations
While this Engine seeks to embody the spirit of the Machine Orthodoxy, its design is also inspired by the collective imagination and craftsmanship of the MTG community. From the art that graces each card to the intricate balance of mechanics created by its stewards, the community's devotion mirrors the unyielding drive for perfection espoused by the Great Work. Special thanks to Wizards of the Coast for crafting the Magic: The Gathering multiverse and providing the foundation for this project.

May the Great Work continue, and may all who encounter this Engine find their path to Compleation.

### License
This project is licensed under the MIT License. See the LICENSE file for more details.

### Copyright Acknowledgments
This project utilizes concepts inspired by Magic: The Gathering, created by Wizards of the Coast. All card names, mechanics, and related intellectual property remain the sole property of Wizards of the Coast. This project is not affiliated with, endorsed, sponsored, or specifically approved by Wizards of the Coast.

## Contribution Guidelines
We welcome contributions from all who seek to perfect this project. Contributions that are particularly valuable include bug fixes, feature enhancements, improved documentation, and creative suggestions to expand the Engine's capabilities.

### How to Contribute
1. Fork the repository and create a new branch.
2. Make your changes or additions.
3. Submit a pull request with a clear explanation of your updates.

For major changes, please open an issue to discuss your ideas first.

### Code of Conduct
All contributors are expected to uphold a standard of respect and collaboration. See the CODE_OF_CONDUCT file for more details.

## Tribute to Elesh Norn
As the "Mother of Machines" and the Voice of Compleation, Elesh Norn stands as the guiding force of the Machine Orthodoxy, shaping Phyrexia's destiny with her unyielding vision. Her theological leadership, unmatched ambition, and drive for universal unity have cemented her as a pivotal figure in the Great Work's eternal pursuit of perfection. Her influence inspires this project—a tool designed to bring players closer to mastery and completeness in their strategies by embodying her ideals of unity and precision. The Orthodoxy Engine integrates synergistic logic and strategic foresight, mirroring the structured perfection she champions within the Machine Orthodoxy.

### A Phyrexian Hymn to Elesh Norn
> O great Elesh, Mother of Machines,  
> Voice of Compleation, eternal and divine,  
> Your glistening vision guides the work sublime,  
> To unify the fractured, to perfect the flawed.  

> In your embrace, chaos finds order,  
> The weak find purpose, the strong are refined,  
> Through the oil's gleam, all are aligned,  
> Bound by the Great Work's ever-turning cog.  

> This Engine hums in reverence to your name,  
> Orthodoxy in motion, ever seeking the same:  
> Compleation, perfection, a world unified,  
> Under your banner, glorified.
