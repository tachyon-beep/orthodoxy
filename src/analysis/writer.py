"""Module for deck writing functionality.

This module provides functionality for writing processed deck data to files,
implementing proper error handling and metadata tracking.
"""

import json
from datetime import datetime
from typing import Dict, List
from ..core.config import load_config


class DeckWriter:
    """Handles writing processed deck data to files.
    
    This class encapsulates the logic for writing deck data to output files,
    including metadata and version tracking.
    """

    @staticmethod
    def write_deck(output_path: str, extracted_cards: List[Dict]) -> None:
        """Write processed deck data to file with metadata.
        
        Args:
            output_path: Path for the output file
            extracted_cards: List of processed card data
            
        Raises:
            IOError: If writing to output file fails
        """
        # Load config for version tracking
        config = load_config()

        try:
            with open(output_path, 'w') as output_file:
                json.dump({
                    "meta": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "version": str(config.version)
                    },
                    "data": {
                        "deck": {
                            "block": None,
                            "cards": extracted_cards
                        }
                    }
                }, output_file, indent=2)

        except IOError as e:
            raise IOError(f"Error writing output file: {str(e)}")
