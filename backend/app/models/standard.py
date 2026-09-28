"""
Canonical Pydantic v2 schemas for Manak-SpecEngine.
Defines IndianStandard, QCOOrder, and ProcurementSpec models.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import re

StandardStatus = Literal["ACTIVE", "WITHDRAWN", "SUPERSEDED"]
MandatoryScheme = Literal["Scheme-I", "Scheme-II (CRS)", "Hallmarking"]


class IndianStandard(BaseModel):
    """
    Represents an Indian Standard published by the Bureau of Indian Standards (BIS).
    """
    is_number: str = Field(
        ...,
        description="Standard identifier, e.g., 'IS 2062' or 'IS 1786:2008'",
        examples=["IS 2062", "IS 1786", "IS 456"]
    )
    title: str = Field(
        ...,
        description="Official publication title of the Indian Standard",
        min_length=3
    )
    year: Optional[int] = Field(
        default=None,
        description="Latest publication or revision year"
    )
    amendments: List[int] = Field(
        default_factory=list,
        description="List of published amendment numbers"
    )
    status: StandardStatus = Field(
        default="ACTIVE",
        description="Current regulatory and technical status: ACTIVE, WITHDRAWN, or SUPERSEDED"
    )
    scope: str = Field(
        ...,
        description="Technical scope, applicability, and abstract of the standard",
        min_length=10
    )
    committee: str = Field(
        ...,
        description="Sectional Committee responsible, e.g., 'CED 54', 'MTD 4'"
    )
    normative_references: List[str] = Field(
        default_factory=list,
        description="List of standards referenced in Clause 2"
    )
    test_standards: List[str] = Field(
        default_factory=list,
        description="List of testing and sampling method standards"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Domain keywords, material grades, and colloquial search terms"
    )
    historical_revisions: List[str] = Field(
        default_factory=list,
        description="Prior historical editions and revisions"
    )
    department: Optional[str] = Field(
        default=None,
        description="Division/Department, e.g. Civil, Mechanical, Electrotechnical"
    )

    @field_validator("is_number")
    @classmethod
    def validate_is_number(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", " ", v.strip())
        if not cleaned:
            raise ValueError("is_number cannot be empty")
        if not re.match(r"^(?:IS|IS/ISO|IS/IEC)\b", cleaned, re.I):
            cleaned = f"IS {cleaned}"
        return cleaned

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1900 or v > 2050):
            raise ValueError(f"Year {v} is outside acceptable range (1900-2050)")
        return v

    @field_validator("normative_references", "test_standards")
    @classmethod
    def clean_standard_lists(cls, v: List[str]) -> List[str]:
        cleaned = []
        for item in v:
            item_str = re.sub(r"\s+", " ", str(item).strip())
            if item_str and item_str not in cleaned:
                cleaned.append(item_str)
        return cleaned


class QCOOrder(BaseModel):
    """
    Represents a statutory Quality Control Order (QCO) issued under Section 16 of the BIS Act, 2016.
    """
    order_name: str = Field(
        ...,
        description="Official title of the statutory order",
        min_length=5
    )
    ministry: str = Field(
        ...,
        description="Line Ministry issuing the order (e.g. Ministry of Steel, MeitY, DPIIT)"
    )
    gazette_no: str = Field(
        ...,
        description="Official Gazette notification number, e.g. 'S.O. 2240(E)'"
    )
    effective_date: str = Field(
        ...,
        description="Enforcement date in YYYY-MM-DD or Gazette date string"
    )
    mandatory_scheme: str = Field(
        ...,
        description="Conformity assessment scheme: 'Scheme-I', 'Scheme-II (CRS)', 'Hallmarking', etc."
    )
    applicable_standards: List[str] = Field(
        ...,
        description="Indian Standards governed by this mandatory QCO",
        min_length=1
    )
    penal_clause: Optional[str] = Field(
        default="Mandatory conformity to Indian Standard with BIS Standard Mark under Section 16 of the BIS Act, 2016.",
        description="Statutory penalties and compliance requirements"
    )
    scope_summary: Optional[str] = Field(
        default=None,
        description="Product categories covered by the order"
    )

    @field_validator("mandatory_scheme")
    @classmethod
    def validate_scheme(cls, v: str) -> str:
        v_clean = v.strip()
        if "Scheme-II" in v_clean or "CRS" in v_clean:
            return "Scheme-II (CRS)"
        elif "Scheme-I" in v_clean or "ISI" in v_clean:
            return "Scheme-I"
        elif "Hallmark" in v_clean:
            return "Hallmarking"
        elif "Scheme-X" in v_clean:
            return "Scheme-X"
        return v_clean

    @field_validator("applicable_standards")
    @classmethod
    def validate_applicable_standards(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("applicable_standards must contain at least one standard")
        return [re.sub(r"\s+", " ", str(s).strip()) for s in v if str(s).strip()]


class ProcurementSpec(BaseModel):
    """
    Represents user or tender specification input text for compliance auditing or recommendations.
    """
    raw_text: str = Field(
        ...,
        description="Raw procurement specification text",
        min_length=3
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code of input text (e.g. 'en', 'hi', 'mr', 'ta')"
    )
    extracted_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Technical parameters extracted from specification (e.g. yield strength, diameter)"
    )

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("raw_text cannot be blank")
        return cleaned
