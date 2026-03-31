from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class _ReportBaseModel(BaseModel):
    """Base model for report schemas: allow population by field name and alias."""

    model_config = ConfigDict(populate_by_name=True)


class SummarySubSection(_ReportBaseModel):
    identifier: str
    heading: str
    content_format: str = Field(alias="content-format")
    content: str


class SummarySection(_ReportBaseModel):
    identifier: str
    heading: str
    sub_heading: Optional[str] = Field(default=None, alias="sub-heading")
    content: str
    content_format: str = Field(alias="content-format")
    summary_sub_sections: List[SummarySubSection] = Field(default_factory=list, alias="summary-sub-sections")


class OverallEvaluationReport(_ReportBaseModel):
    content: str
    content_format: str = Field(alias="content-format")


class SummaryMetaData(_ReportBaseModel):
    overall_evaluation_report: OverallEvaluationReport = Field(alias="overall-evaluation-report")
    debug_log: str = Field(alias="debug-log")


class CreditSummaryGenAIResponse(_ReportBaseModel):
    schema_: str = Field(alias="$schema")
    id_: str = Field(alias="$id")
    request_id: str = Field(alias="requestId")
    language: str
    generated_by: str = Field(alias="generatedBy")
    generated_at: str = Field(alias="generatedAt")
    summary_sections: List[SummarySection] = Field(alias="summary-sections")
    summary_meta_data: SummaryMetaData = Field(alias="summary-meta-data")
