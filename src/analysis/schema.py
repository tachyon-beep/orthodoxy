"""Module for schema validation functionality.

This module provides functionality for validating card data against schemas,
implementing proper type checking and error handling.
"""

import json
from typing import Dict, List, Optional, Union


class SchemaValidator:
    """Handles schema validation for card data.
    
    This class encapsulates the logic for validating card data against
    schemas, with support for both file-based and dict-based schemas.
    """

    @staticmethod
    def get_required_fields(schema: Union[str, Dict, None]) -> Optional[List[str]]:
        """Get required fields from schema with validation.
        
        Args:
            schema: Schema as path string or parsed dict
            
        Returns:
            Optional[List[str]]: Validated required fields
            
        Example:
            ```python
            # Load schema from file
            fields = SchemaValidator.get_required_fields("schema.json")
            if fields:
                print(f"Required fields: {', '.join(fields)}")
            ```
        """
        if schema is None:
            return None
            
        # If schema is a string (path), load it
        schema_dict: Dict
        if isinstance(schema, str):
            with open(schema, 'r') as f:
                schema_dict = json.load(f)
        else:
            schema_dict = schema
                
        # Extract required fields with validation
        try:
            properties = schema_dict.get("properties", {})
            if not properties:
                return None
                
            data = properties.get("data", {})
            if not data:
                return None
                
            pattern_props = data.get("patternProperties", {})
            if not pattern_props:
                return None
                
            wildcard = pattern_props.get(".*", {})
            if not wildcard:
                return None
                
            card_props = wildcard.get("properties", {})
            if not card_props:
                return None
                
            cards = card_props.get("cards", {})
            if not cards:
                return None
                
            items = cards.get("items", {})
            if not items:
                return None
                
            return items.get("required", [])
        except (KeyError, AttributeError):
            return None
