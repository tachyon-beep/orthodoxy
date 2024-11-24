"""Module for handling JSON archive loading and validation.

This module provides functionality for loading and validating card archives,
implementing proper error handling and type safety.
"""

import json
from typing import Dict, Optional


class ArchiveLoader:
    """Handles loading and validation of JSON card archives.
    
    This class encapsulates the logic for loading JSON archives and
    performing initial validation checks.
    """

    @staticmethod
    def load_archive(archive_path: str) -> Dict:
        """Load and validate the JSON archive with type checking.
        
        Args:
            archive_path: Path to the JSON archive file
            
        Returns:
            Dict: The validated JSON data
            
        Raises:
            FileNotFoundError: If archive file doesn't exist
            ValueError: If archive format is invalid
        """
        try:
            with open(archive_path, 'r') as archive_file:
                data = json.load(archive_file)
                
            if not isinstance(data, dict):
                raise ValueError("Archive must be a JSON object")
                
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"Archive file not found: {archive_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in archive: {str(e)}")

    @staticmethod
    def validate_archive_structure(archive_data: Dict) -> Optional[str]:
        """Validate the basic structure of the loaded archive.
        
        Args:
            archive_data: The loaded archive data
            
        Returns:
            Optional[str]: Error message if validation fails, None if successful
        """
        if "data" not in archive_data:
            return "Archive missing 'data' section"
        return None
