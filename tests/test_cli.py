"""Tests for CLI functionality."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from src.interface.cli import main, handle_filter_command, handle_extract_deck_command
from src.utils.container import Container
from src.services.analysis import CardFilterService
from src.core.errors import InvalidFilterError
from src.utils.models import DeckListStats


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary files for testing."""
    files = {
        "input": tmp_path / "input.json",
        "output": tmp_path / "output.json",
        "schema": tmp_path / "schema.json",
        "dump_schema": tmp_path / "dump_schema.json"
    }
    
    # Create input file with test data
    files["input"].write_text('{"meta": {}, "data": {}}')
    
    # Create schema file with test data
    files["schema"].write_text('["name", "type"]')
    return {k: str(v) for k, v in files.items()}


@pytest.fixture
def mock_container():
    """Create a mock container."""
    container = Mock(spec=Container)
    config = Mock()
    container.config.return_value = config
    # Add init_resources method to the mock
    container.init_resources = Mock()
    # Add logging service
    container.logging_service.return_value = Mock()
    return container


@pytest.fixture
def mock_service():
    """Create a mock service with required methods."""
    service = Mock(spec=CardFilterService)
    # Create a mock parser with parse_filter_string method
    parser = Mock()
    parser.parse_filter_string = Mock()
    # Attach the parser to the service
    service.parser = parser
    return service


def test_basic_filter(temp_files, mock_container, mock_service, monkeypatch):
    """Test basic CLI execution."""
    test_args = [
        "prog",
        "filter",
        temp_files["input"],
        temp_files["output"]
    ]
    monkeypatch.setattr("sys.argv", test_args)
    
    with patch("src.interface.cli.CardFilterService", return_value=mock_service), \
         patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_not_called()
    
    mock_service.process_cards.assert_called_once()


def test_with_schema(temp_files, mock_container, mock_service, monkeypatch):
    """Test CLI execution with schema argument."""
    test_args = [
        "prog",
        "filter",
        temp_files["input"],
        temp_files["output"],
        "--schema",
        temp_files["schema"]
    ]
    monkeypatch.setattr("sys.argv", test_args)
    
    with patch("src.interface.cli.CardFilterService", return_value=mock_service), \
         patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_not_called()
    
    mock_service.process_cards.assert_called_once()


def test_with_filters(temp_files, mock_container, mock_service, monkeypatch):
    """Test CLI execution with filters argument."""
    test_filter = '{"colors": {"contains": "W"}}'
    test_args = [
        "prog",
        "filter",
        temp_files["input"],
        temp_files["output"],
        "--filters",
        test_filter
    ]
    monkeypatch.setattr("sys.argv", test_args)
    
    # Mock filter parsing
    parsed_filter = {"colors": {"contains": "W"}}
    mock_service.parser.parse_filter_string.return_value = parsed_filter
    
    with patch("src.interface.cli.CardFilterService", return_value=mock_service), \
         patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_not_called()
    
    mock_service.parser.parse_filter_string.assert_called_once_with(test_filter)
    mock_service.process_cards.assert_called_once()


def test_with_languages(temp_files, mock_container, mock_service, monkeypatch):
    """Test CLI execution with languages argument."""
    test_args = [
        "prog",
        "filter",
        temp_files["input"],
        temp_files["output"],
        "--additional-languages",
        "German", "French"
    ]
    monkeypatch.setattr("sys.argv", test_args)
    
    with patch("src.interface.cli.CardFilterService", return_value=mock_service), \
         patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_not_called()
    
    # Verify languages were passed correctly
    process_calls = mock_service.process_cards.call_args_list
    assert len(process_calls) == 1
    _, kwargs = process_calls[0]
    assert kwargs.get("additional_languages") == ["German", "French"]


def test_invalid_filter_string(temp_files, mock_container, mock_service, monkeypatch):
    """Test handling of invalid filter string."""
    test_args = [
        "prog",
        "filter",
        temp_files["input"],
        temp_files["output"],
        "--filters",
        "invalid json"
    ]
    monkeypatch.setattr("sys.argv", test_args)
    
    # Mock filter parsing to raise an exception
    mock_service.parser.parse_filter_string.side_effect = json.JSONDecodeError("Test error", "invalid json", 0)
    
    with patch("src.interface.cli.CardFilterService", return_value=mock_service):
        with pytest.raises(SystemExit):
            main()
    
    mock_service.parser.parse_filter_string.assert_called_once()


def test_extract_deck_basic(temp_files, mock_container, mock_service, monkeypatch):
    """Test basic deck extraction."""
    # Create deck list file
    deck_file = Path(temp_files["input"]).parent / "deck.txt"
    deck_file.write_text("1 Test Card")

    # Note: CLI command format is "extract-deck <decklist> <archive> <output>"
    test_args = [
        "prog",
        "extract-deck",
        temp_files["input"],  # archive file
        str(deck_file),       # deck list file
        temp_files["output"]  # output file
    ]
    monkeypatch.setattr("sys.argv", test_args)

    # Mock the deck extractor service
    mock_deck_extractor = Mock()
    mock_deck_extractor.extract_deck_cards.return_value = DeckListStats(
        total_cards=1,
        cards_found=1,
        cards_missing=0
    )

    # Patch container to return our mock deck extractor
    mock_container.deck_extractor_service.return_value = mock_deck_extractor

    with patch("src.interface.cli.CardFilterService", return_value=mock_service), \
         patch("src.interface.cli.Container", return_value=mock_container), \
         patch("sys.exit") as mock_exit:
        main()
        mock_exit.assert_not_called()

    # Verify the deck extractor was called with correct arguments
    mock_deck_extractor.extract_deck_cards.assert_called_once_with(
        archive_path=temp_files["input"],
        decklist_path=str(deck_file),
        output_path=temp_files["output"],
        schema=None,
        debug=False  # Added debug parameter with default value
    )
