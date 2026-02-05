"""Pydantic models for SDK inputs and outputs."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class CreateUserInput(BaseModel):
    """CreateUserInput model."""
    
    email: str = Field(default=None, description='User email')
    name: str = Field(default=None, description='User name')


class User(BaseModel):
    """User model."""
    
    user: User = Field(default=None, description='Created user')


class CreateInvoiceInput(BaseModel):
    """CreateInvoiceInput model."""
    
    user_id: str = Field(default=None, description='User ID')
    amount: float = Field(default=None, description='Invoice amount')


class Invoice(BaseModel):
    """Invoice model."""
    
    invoice: Invoice = Field(default=None, description='Created invoice')

