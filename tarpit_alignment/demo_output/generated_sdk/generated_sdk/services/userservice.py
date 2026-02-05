"""Service: UserService"""

import warnings
from typing import Any, Optional
from generated_sdk.models import *
from generated_sdk.runtime.base import BaseService
from generated_sdk.registry import CapabilityRegistry


class UserService(BaseService):
    """Manages users
"""
    
    def __init__(self, registry: CapabilityRegistry):
        """Initialize UserService service."""
        super().__init__(registry)
        if false:
            warnings.warn(
                "UserService is deprecated",
                DeprecationWarning,
                stacklevel=2
            )
    
    def create_user(self, email: str, name: str) -> User:
        """Creates a new user
        Args:
            email: User email
            name: User name

        Returns:
            User: Result

        Notes:
        - [2026-01-31T14:12:52.755450] Modified create_user to accept an additional parameter 'name'.
        """
        # Validate inputs
        input_data = CreateUserInput(email=email, name=name)
        
        # TODO: Implement actual logic
        # Input: CreateUserInput
        # Output: User
        
        # For now, return a basic output model
        result = User(**input_data.model_dump())
        return result
