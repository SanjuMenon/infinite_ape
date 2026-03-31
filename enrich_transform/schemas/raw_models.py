from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AddressModel(BaseModel):
    street: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    houseNumber: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class RealEstateModel(BaseModel):
    realEstateId: str
    realEstateType: Optional[str] = None
    marketValue: Optional[float] = None
    marketValueDate: Optional[datetime] = None
    selfUtilizationPercentage: Optional[float] = None
    indexedValue: Optional[float] = None
    indexedValueDate: Optional[datetime] = None
    constructionDate: Optional[datetime] = None
    condominiumFlag: Optional[bool] = None
    landLease: Optional[bool] = None
    endOfLandLeaseDate: Optional[datetime] = None
    rentAssignmentFlag: Optional[bool] = None
    rentalIncome: Optional[float] = None
    mortgageDeedRank: Optional[float] = None
    address: Optional[AddressModel] = None

    model_config = ConfigDict(extra="ignore")


class MortgageDeedModel(BaseModel):
    mortgageDeedType: Optional[str] = None
    mortgageDeedSecuringType: Optional[str] = None
    mortgageDeedRegistrationDate: Optional[datetime] = None
    realestates: list[RealEstateModel] = []

    model_config = ConfigDict(extra="ignore")


class CollateralModel(BaseModel):
    collateralId: str
    collateralType: str
    # We always coerce output currency to CHF, so source currency can be nullable.
    currency: Optional[str] = None

    # Must be non-null per requirements; Pydantic will fail validation on `null`.
    lendingValueAmount: float
    nominalValueAmount: float

    lendingValueDate: datetime
    mortgageDeed: Optional[MortgageDeedModel] = None

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

