from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class CollateralModel(BaseModel):
    collateralId: str
    collateralType: str
    # We always coerce output currency to CHF, so source currency can be nullable.
    currency: Optional[str] = None

    # Must be non-null per requirements; Pydantic will fail validation on `null`.
    lendingValueAmount: float
    nominalValueAmount: float

    lendingValueDate: datetime

    model_config = ConfigDict(extra="ignore")


class BankingRelationModel(BaseModel):
    bankingRelationNumber: str
    isMainBR: bool

    collaterals: list[CollateralModel] = []
    # businessModel contains nested objects/arrays; validate only as dicts.
    businessModel: list[dict[str, Any]] = []

    model_config = ConfigDict(extra="ignore")


class LegalEntityModel(BaseModel):
    legalEntityIdGPID: str
    bankingRelations: list[BankingRelationModel] = []

    model_config = ConfigDict(extra="ignore")


class DataInnerModel(BaseModel):
    legalEntities: list[LegalEntityModel] = []

    model_config = ConfigDict(extra="ignore")


class DataOuterModel(BaseModel):
    data: DataInnerModel
    preferenceData: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class RawPayloadModel(BaseModel):
    data: DataOuterModel

    model_config = ConfigDict(extra="ignore")

