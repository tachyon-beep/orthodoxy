# Magic: The Gathering Data Structure Documentation

This document serves as a comprehensive guide to understanding the Magic: The Gathering (MTG) JSON data format, how to work with it programmatically, and how to leverage its rich features. It includes detailed breakdowns of each section, examples, and best practices.

---

## **1. Overview of the Data Structure**

The dataset is designed to represent MTG card sets and their associated data. It includes:
- Metadata about the dataset itself.
- Card set information (e.g., name, size, block).
- Detailed card data (e.g., names, rules text, translations, legalities).

---

## **2. Meta Information**

The `meta` object provides metadata about the dataset.

| Field         | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `date`        | String | The release or creation date of the dataset.     |
| `version`     | String | The version of the dataset, typically timestamped.|

**Example:**
```json
"meta": {
    "date": "2024-11-23",
    "version": "5.2.2+20241123"
}
```

---

## **3. Data Section**

The `data` object contains the main card data, grouped by **set codes**. Each set contains:

| Field            | Type          | Description                                      |
|-------------------|---------------|--------------------------------------------------|
| `baseSetSize`     | Integer       | The number of main cards in the set.            |
| `block`           | String        | The name of the block or thematic grouping.     |
| `cards`           | Array         | The list of all cards in the set.               |

**Example:**
```json
"data": {
    "BIG": {
        "baseSetSize": 0,
        "block": "Outlaws of Thunder Junction",
        "cards": [...]
    }
}
```

---

## **4. Cards Array**

The `cards` array contains objects representing individual cards in the set. Each card has a rich set of fields.

### **Core Fields**

| Field               | Type            | Description                                                    |
|---------------------|-----------------|----------------------------------------------------------------|
| `name`              | String          | The card’s name.                                               |
| `type`              | String          | The card’s type (e.g., Artifact, Creature).                   |
| `manaCost`          | String          | The mana cost to cast the card.                                |
| `manaValue`         | Float           | The numeric converted mana cost (CMC) of the card.             |
| `text`              | String          | The rules text of the card.                                    |
| `power`             | String (opt.)   | The card's power (if applicable, for creatures).               |
| `toughness`         | String (opt.)   | The card's toughness (if applicable, for creatures).           |
| `rarity`            | String          | The card’s rarity (e.g., common, mythic).                      |
| `legalities`        | Object          | Formats where the card is legal (e.g., Standard, Commander).   |

**Example:**
```json
{
    "name": "Collector's Cage",
    "manaCost": "{1}{W}",
    "manaValue": 2.0,
    "type": "Artifact",
    "text": "Hideaway 5...",
    "rarity": "mythic",
    "legalities": {
        "standard": "Legal",
        "commander": "Legal",
        ...
    }
}
```

---

### **Translations (`foreignData`)**

The `foreignData` array provides translations of the card into different languages. Each translation includes:

| Field         | Type   | Description                                     |
|---------------|--------|-------------------------------------------------|
| `language`    | String | The language of the translation (e.g., German). |
| `name`        | String | The translated name of the card.                |
| `text`        | String | The translated text of the card.                |

**Example:**
```json
"foreignData": [
    {
        "language": "German",
        "name": "Käfig des Sammlers",
        "text": "Refugium 5..."
    },
    {
        "language": "Spanish",
        "name": "Jaula de coleccionista",
        "text": "Esconder 5..."
    }
]
```

---

### **Rulings System**

The `rulings` array contains official clarifications and rule interpretations for each card. Each ruling is structured as follows:

| Field         | Type   | Description                                           |
|---------------|--------|-------------------------------------------------------|
| `date`        | String | The date the ruling was issued (YYYY-MM-DD format).   |
| `text`        | String | The actual ruling text explaining the card interaction.|

**Example:**
```json
"rulings": [
    {
        "date": "2024-04-12",
        "text": "If Rest in Peace is destroyed by a spell, Rest in Peace will be exiled and then the spell will be put into its owner's graveyard."
    },
    {
        "date": "2024-04-12",
        "text": "While Rest in Peace is on the battlefield, abilities that trigger whenever a creature dies won't trigger because cards and tokens are never put into a player's graveyard."
    }
]
```

#### **Working with Rulings**

**1. Retrieving Card Rulings**
```python
def get_card_rulings(cards, card_name):
    card = next((card for card in cards if card["name"] == card_name), None)
    if card and "rulings" in card:
        return card["rulings"]
    return []

# Example usage:
rulings = get_card_rulings(cards, "Rest in Peace")
for ruling in rulings:
    print(f"[{ruling['date']}] {ruling['text']}")
```

**2. Finding Recent Rulings**
```python
from datetime import datetime

def get_recent_rulings(cards, since_date):
    date_obj = datetime.strptime(since_date, "%Y-%m-%d")
    recent_rulings = []
    
    for card in cards:
        if "rulings" in card:
            for ruling in card["rulings"]:
                ruling_date = datetime.strptime(ruling["date"], "%Y-%m-%d")
                if ruling_date >= date_obj:
                    recent_rulings.append({
                        "card": card["name"],
                        "ruling": ruling
                    })
    
    return recent_rulings
```

**3. Keyword-Based Ruling Search**
```python
def search_rulings_by_keyword(cards, keyword):
    matching_rulings = []
    
    for card in cards:
        if "rulings" in card:
            for ruling in card["rulings"]:
                if keyword.lower() in ruling["text"].lower():
                    matching_rulings.append({
                        "card": card["name"],
                        "ruling": ruling
                    })
    
    return matching_rulings
```

#### **Common Use Cases for Rulings**

1. **Rule Clarification Tools**
   - Search for rulings by keyword or card name.
   - Generate detailed ruling lists for specific cards or mechanics.

2. **Tournament Support**
   - Provide quick lookups for official rulings.
   - Validate ruling applicability by date.

3. **Educational Resources**
   - Teach players about complex card interactions.
   - Use rulings for quizzes or training modules.

#### **Best Practices for Working with Rulings**

1. **Date Handling**:
   - Parse ruling dates using proper date objects to enable sorting or filtering.
   - Ensure date formats (YYYY-MM-DD) are consistent.

2. **Text Processing**:
   - Normalize text for case-insensitive keyword searches.
   - Handle special characters and game-specific symbols (e.g., `{T}`, `{W}`).

