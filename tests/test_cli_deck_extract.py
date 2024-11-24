"""Tests for the deck extraction CLI functionality."""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from src.interface.cli import main, handle_extract_deck_command
from src.utils.models import DeckListStats


@pytest.fixture
def mock_container():
    """Provides a mock container with required services."""
    container = Mock()
    container.logging_service.return_value = Mock()
    container.deck_extractor_service.return_value = Mock()
    return container


@pytest.fixture
def sample_files(tmp_path):
    """Creates sample files needed for testing."""
    # Create archive file
    archive_data = {
        "data": {
            "BLB": {
                "cards": [
                    {
                        "name": "Test Card",
                        "setCode": "BLB",
                        "number": "1"
                    }
                ]
            },
            "FDN": {
                "cards": [
                    {
                        "name": "Test Card",
                        "setCode": "FDN",
                        "number": "2"
                    }
                ]
            }
        }
    }
    archive_file = tmp_path / "cards.json"
    archive_file.write_text(json.dumps(archive_data))
    
    # Create deck list file
    decklist = "4 Test Card (BLB) 1"
    decklist_file = tmp_path / "deck.txt"
    decklist_file.write_text(decklist)
    
    # Create schema file
    schema = ["name", "setCode"]
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema))
    
    return {
        "archive": archive_file,
        "decklist": decklist_file,
        "schema": schema_file,
        "output": tmp_path / "output.json"
    }


def test_extract_deck_command(mock_container, sample_files):
    """Test the extract-deck command with basic arguments."""
    args = Mock(
        command="extract-deck",
        archive=str(sample_files["archive"]),
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=None,
        debug=False
    )
    
    # Set up mock statistics
    mock_stats = DeckListStats(
        cards_found=1,
        cards_missing=0,
        total_cards=1
    )
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute command
    handle_extract_deck_command(args, mock_container)
    
    # Verify service was called correctly
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once_with(
        archive_path=str(sample_files["archive"]),
        decklist_path=str(sample_files["decklist"]),
        output_path=str(sample_files["output"]),
        schema=None,
        debug=False
    )


def test_extract_deck_command_with_debug(mock_container, sample_files):
    """Test the extract-deck command with debug flag enabled."""
    args = Mock(
        command="extract-deck",
        archive=str(sample_files["archive"]),
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=None,
        debug=True
    )
    
    # Set up mock statistics
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute command
    handle_extract_deck_command(args, mock_container)
    
    # Verify service was called with debug flag
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once_with(
        archive_path=str(sample_files["archive"]),
        decklist_path=str(sample_files["decklist"]),
        output_path=str(sample_files["output"]),
        schema=None,
        debug=True
    )


def test_extract_deck_command_with_schema(mock_container, sample_files):
    """Test the extract-deck command with a schema file."""
    args = Mock(
        command="extract-deck",
        archive=str(sample_files["archive"]),
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=str(sample_files["schema"]),
        debug=False
    )
    
    # Set up mock statistics
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute command
    handle_extract_deck_command(args, mock_container)
    
    # Verify service was called with schema
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once()
    call_args = mock_container.deck_extractor_service.return_value.extract_deck_cards.call_args[1]
    assert "schema" in call_args
    assert call_args["schema"] == ["name", "setCode"]
    assert call_args["debug"] == False


@patch("sys.argv")
def test_main_extract_deck(mock_argv, mock_container, sample_files):
    """Test the main function with extract-deck command."""
    # Set up command line arguments
    mock_argv.__getitem__.side_effect = lambda i: [
        "orthodoxy",
        "extract-deck",
        str(sample_files["archive"]),
        str(sample_files["decklist"]),
        str(sample_files["output"])
    ][i]
    
    # Set up mock statistics
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute main with mocked container
    with patch("src.interface.cli.Container", return_value=mock_container):
        main()
    
    # Verify service was called with debug=False by default
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once()
    assert mock_container.deck_extractor_service.return_value.extract_deck_cards.call_args[1]["debug"] == False


@patch("sys.argv")
def test_main_extract_deck_with_debug(mock_argv, mock_container, sample_files):
    """Test the main function with extract-deck command and debug flag."""
    # Set up command line arguments
    mock_argv.__getitem__.side_effect = lambda i: [
        "orthodoxy",
        "extract-deck",
        str(sample_files["archive"]),
        str(sample_files["decklist"]),
        str(sample_files["output"]),
        "--debug"
    ][i]
    
    # Set up mock statistics
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute main with mocked container
    with patch("src.interface.cli.Container", return_value=mock_container):
        main()
    
    # Verify service was called with debug=True
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once()
    assert mock_container.deck_extractor_service.return_value.extract_deck_cards.call_args[1]["debug"] == True


@patch("sys.argv")
@patch("builtins.open", new_callable=mock_open, read_data='["name", "type"]')
def test_main_extract_deck_with_actual_files(mock_open, mock_argv, mock_container):
    """Test the extract-deck command using actual project files."""
    # Set up command line arguments to match the actual command:
    # python -m src.interface.cli extract-deck data/standard.json data/deck.txt data/output.json --schema docs/schemas/core.json
    mock_argv.__getitem__.side_effect = lambda i: [
        "orthodoxy",
        "extract-deck",
        "data/standard.json",
        "data/deck.txt",
        "data/output.json",
        "--schema",
        "docs/schemas/core.json"
    ][i]
    
    # Set up mock statistics
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute main with mocked container
    with patch("src.interface.cli.Container", return_value=mock_container):
        main()
    
    # Verify service was called with correct paths and schema
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once()
    call_args = mock_container.deck_extractor_service.return_value.extract_deck_cards.call_args[1]
    
    assert call_args["archive_path"] == "data/standard.json"
    assert call_args["decklist_path"] == "data/deck.txt"
    assert call_args["output_path"] == "data/output.json"
    assert call_args["schema"] == ["name", "type"]  # Schema should be loaded from core.json
    assert call_args["debug"] == False


@patch("sys.argv")
def test_extract_deck_existing_output_file(mock_argv, mock_container, sample_files):
    """Test the extract-deck command when the output file already exists."""
    # Create an existing output file with some content
    existing_content = {"existing": "data"}
    output_file = sample_files["output"]
    output_file.write_text(json.dumps(existing_content))
    
    # Verify the file exists and has content
    assert output_file.exists()
    assert json.loads(output_file.read_text()) == existing_content
    
    # Set up command line arguments
    mock_argv.__getitem__.side_effect = lambda i: [
        "orthodoxy",
        "extract-deck",
        str(sample_files["archive"]),
        str(sample_files["decklist"]),
        str(output_file)
    ][i]
    
    # Set up mock statistics and new content
    mock_stats = DeckListStats(cards_found=1, cards_missing=0, total_cards=1)
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute main with mocked container
    with patch("src.interface.cli.Container", return_value=mock_container):
        # Command should execute without raising any errors
        main()
    
    # Verify service was called
    mock_container.deck_extractor_service.return_value.extract_deck_cards.assert_called_once()
    
    # Verify the output file still exists
    assert output_file.exists()
    
    # Note: The actual content would be different from the existing_content
    # as the file is opened in write mode which overwrites the existing content
    assert mock_container.deck_extractor_service.return_value.extract_deck_cards.call_args[1]["output_path"] == str(output_file)


def test_extract_deck_missing_archive(mock_container, sample_files):
    """Test handling of missing archive file."""
    args = Mock(
        command="extract-deck",
        archive="nonexistent.json",
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=None,
        debug=False
    )
    
    # Set up mock to raise error
    mock_container.deck_extractor_service.return_value.extract_deck_cards.side_effect = \
        FileNotFoundError("Archive file not found")
    
    # Execute command and verify error handling
    with pytest.raises(SystemExit):
        handle_extract_deck_command(args, mock_container)
    
    # Verify error was logged
    mock_container.logging_service.return_value.error.assert_called_once()


def test_extract_deck_invalid_schema(mock_container, sample_files):
    """Test handling of invalid schema file."""
    # Create invalid schema file
    invalid_schema = sample_files["schema"].parent / "invalid_schema.json"
    invalid_schema.write_text("invalid json")
    
    args = Mock(
        command="extract-deck",
        archive=str(sample_files["archive"]),
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=str(invalid_schema),
        debug=False
    )
    
    # Execute command and verify error handling
    with pytest.raises(SystemExit):
        handle_extract_deck_command(args, mock_container)
    
    # Verify error was logged
    mock_container.logging_service.return_value.error.assert_called_once()


@patch("builtins.print")
def test_extract_deck_statistics_output(mock_print, mock_container, sample_files):
    """Test that statistics are properly displayed."""
    args = Mock(
        command="extract-deck",
        archive=str(sample_files["archive"]),
        decklist=str(sample_files["decklist"]),
        output=str(sample_files["output"]),
        schema=None,
        debug=False
    )
    
    # Set up mock statistics
    mock_stats = DeckListStats(
        cards_found=3,
        cards_missing=1,
        total_cards=4
    )
    mock_container.deck_extractor_service.return_value.extract_deck_cards.return_value = mock_stats
    
    # Execute command
    handle_extract_deck_command(args, mock_container)
    
    # Verify statistics were printed
    mock_print.assert_any_call("\nDeck Extraction Statistics:")
    mock_print.assert_any_call("Total unique cards: 4")
    mock_print.assert_any_call("Cards found: 3")
    mock_print.assert_any_call("Cards missing: 1")
    mock_print.assert_any_call("Success rate: 75.0%")
