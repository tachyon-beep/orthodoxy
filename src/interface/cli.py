"""Command line interface for Magic: The Gathering card filtering operations.

This module provides the command-line interface for filtering and processing Magic: The
Gathering card data. It handles argument parsing, service initialization, and high-level
error handling for the card filtering application.

Features:
- Card filtering with custom criteria
- Deck list card extraction
- Schema-based filtering
- Multi-language support
- Configuration file handling
- Error logging and reporting

Commands:
    filter: Filter cards based on various criteria
        Arguments:
            input_file: Path to the source JSON file containing card data
            output_file: Path where filtered card data will be written
            --schema: Optional path to a JSON schema file for attribute filtering
            --dump-schema: Optional path to output the default schema
            --filters: JSON string of filter criteria
            --additional-languages: List of languages to include besides English
            --config: Path to YAML or JSON configuration file

    extract-deck: Extract card data for a deck list
        Arguments:
            archive: Path to the JSON archive containing all card data
            decklist: Path to the deck list file
            output: Path where extracted card data will be written
            --schema: Optional path to a JSON schema file for attribute filtering
            --debug: Show detailed debug output during extraction

Example usage:
    Filter white cards:
    $ python -m orthodoxy filter input.json output.json --filters '{"colors": {"contains": "W"}}'

    Include German translations:
    $ python -m orthodoxy filter input.json output.json --additional-languages German

    Extract deck cards:
    $ python -m orthodoxy extract-deck cards.json deck.txt deck_cards.json
"""

import json
import sys
import argparse
from typing import Optional, Dict, Any
from ..utils.container import Container
from ..services.analysis import CardFilterService


def setup_filter_parser(subparsers):
    """Set up the parser for the filter command."""
    parser = subparsers.add_parser(
        'filter',
        help="Filter cards from a JSON file based on various criteria",
        description="""
Filter Magic: The Gathering cards from a JSON file based on various criteria.

This command allows you to filter cards using multiple criteria such as colors, types,
mana cost, and more. You can specify filters using a JSON string, use a schema file
to control which attributes are included in the output, and include translations in
additional languages.

Output Format:
  The command outputs a JSON file containing the filtered card data. Each card is
  represented as a JSON object with attributes like name, mana_cost, type_line, etc.
  Use the --schema option to control which attributes are included in the output.

Examples:
  # Filter white cards and save to filtered.json
  python -m orthodoxy filter cards.json filtered.json --filters '{"colors": {"contains": "W"}}'

  # Filter legendary creatures and include German translations
  python -m orthodoxy filter cards.json legends.json \\
    --filters '{"type_line": {"contains": "Legendary Creature"}}' \\
    --additional-languages German

  # Use a custom schema to control which card attributes appear in the output JSON
  python -m orthodoxy filter cards.json output.json --schema custom_schema.json

  # Export the default schema to see available card attributes
  python -m orthodoxy filter cards.json output.json --dump-schema schema.json
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input JSON file containing the card data to filter."
    )
    parser.add_argument(
        "output_file",
        type=str,
        help="Path where the filtered card data will be written as a JSON file."
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="""Path to a JSON schema file that defines which card attributes to include in the output JSON.
Use this to customize which fields (like name, mana_cost, type_line) appear in the output."""
    )
    parser.add_argument(
        "--dump-schema",
        type=str,
        help="Path where the default schema will be written as JSON for reference or customization."
    )
    parser.add_argument(
        "--filters",
        type=str,
        help="""JSON string containing filter criteria. Format: {"field": {"operator": "value"}}.
Available operators: equals, contains, greater_than, less_than, regex.
Example: '{"colors": {"contains": "W"}, "cmc": {"less_than": 4}}'"""
    )
    parser.add_argument(
        "--additional-languages",
        type=str,
        nargs="+",
        help="""Additional languages to include in the output JSON besides English.
Example: --additional-languages German Spanish Japanese"""
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a YAML or JSON configuration file with additional settings."
    )
    return parser


def setup_extract_deck_parser(subparsers):
    """Set up the parser for the extract-deck command."""
    parser = subparsers.add_parser(
        'extract-deck',
        help="Extract card data for a deck list",
        description="""
Extract card data for a deck list from a JSON archive.

This command processes a deck list file and extracts detailed card information for each
card in the list from a provided JSON archive. The deck list should contain one card
per line with optional quantity prefixes.

Output Format:
  The command outputs a JSON file containing the full card data for each card in your
  deck list. Each card is represented as a JSON object with attributes like name,
  mana_cost, type_line, etc. Use the --schema option to control which attributes are
  included in the output.

Deck List Format:
  4 Lightning Bolt
  2x Mountain
  Mox Ruby
  3 Birds of Paradise

The command will:
1. Read the deck list file
2. Look up each card in the JSON archive
3. Extract the relevant card data
4. Save the results as a JSON file
5. Display statistics about the extraction process

Examples:
  # Extract card data for a standard deck list
  python -m orthodoxy extract-deck cards.json deck.txt output.json

  # Use a custom schema to control which card attributes appear in the output JSON
  python -m orthodoxy extract-deck cards.json deck.txt output.json --schema custom_schema.json

  # Show detailed debug output during extraction
  python -m orthodoxy extract-deck cards.json deck.txt output.json --debug
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "archive",
        type=str,
        help="Path to the JSON archive file containing the complete card database."
    )
    parser.add_argument(
        "decklist",
        type=str,
        help="""Path to the deck list file. Each line should contain a card name,
optionally prefixed with a quantity (e.g., "4 Lightning Bolt" or "2x Mountain")."""
    )
    parser.add_argument(
        "output",
        type=str,
        help="Path where the extracted card data will be written as a JSON file."
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="""Path to a JSON schema file that defines which card attributes to include in the output JSON.
Use this to customize which fields (like name, mana_cost, type_line) appear in the output."""
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed debug output during extraction."
    )
    return parser


def handle_filter_command(args: argparse.Namespace, container: Container) -> None:
    """Handle the filter command."""
    card_filter_service = CardFilterService(container)

    schema = None
    if args.schema:
        with open(args.schema, 'r', encoding='utf-8') as schema_file:
            schema = json.load(schema_file)

    filters = None
    if args.filters:
        filters = card_filter_service.parser.parse_filter_string(args.filters)

    card_filter_service.process_cards(
        args.input_file,
        args.output_file,
        schema=schema,
        dump_schema=args.dump_schema,
        filters=filters,
        additional_languages=args.additional_languages,
    )


def handle_extract_deck_command(args: argparse.Namespace, container: Container) -> None:
    """Handle the extract-deck command."""
    try:
        deck_extractor = container.deck_extractor_service()
        logger = container.logging_service()

        schema = None
        if args.schema:
            try:
                with open(args.schema, 'r', encoding='utf-8') as schema_file:
                    schema = json.load(schema_file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error loading schema file: {str(e)}")
                print(f"Error: Failed to load schema file - {str(e)}")
                sys.exit(1)

        try:
            stats = deck_extractor.extract_deck_cards(
                archive_path=args.archive,
                decklist_path=args.decklist,
                output_path=args.output,
                schema=schema,
                debug=args.debug
            )

            # Print statistics
            print("\nDeck Extraction Statistics:")
            print(f"Total unique cards: {stats.total_cards}")
            print(f"Cards found: {stats.cards_found}")
            print(f"Cards missing: {stats.cards_missing}")
            print(f"Success rate: {stats.success_rate:.1f}%")

        except FileNotFoundError as e:
            logger.error(str(e))
            print(f"Error: {str(e)}")
            sys.exit(1)
        except (ValueError, IOError) as e:
            logger.error(str(e))
            print(f"Error: {str(e)}")
            sys.exit(1)

    except Exception as e:
        logger = container.logging_service()
        logger.error("Unexpected error: " + str(e))
        print(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for the card filter application."""
    container = Container()
    container.init_resources()
    
    parser = argparse.ArgumentParser(
        description="""Process Magic: The Gathering card data.

This tool provides two main commands that both output card data in JSON format:

  filter        - Filter cards from a JSON file based on various criteria.
                 Outputs matching cards as a JSON file.

  extract-deck  - Extract card data for a deck list from a card database.
                 Outputs the deck's cards as a JSON file.

Both commands support using a schema file (--schema) to control which card
attributes appear in the output JSON.

Use -h or --help with any command to see detailed usage information.
Example: python -m orthodoxy filter --help""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(
        dest='command',
        metavar='{filter, extract-deck}',
        help='Available commands',
        description='Choose a command to execute:'
    )

    # Set up command parsers
    setup_filter_parser(subparsers)
    setup_extract_deck_parser(subparsers)

    args = parser.parse_args()

    try:
        if args.command == 'filter':
            handle_filter_command(args, container)
        elif args.command == 'extract-deck':
            handle_extract_deck_command(args, container)
        else:
            parser.print_help()
            exit(1)

    except Exception as e:
        container.logging_service().error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
