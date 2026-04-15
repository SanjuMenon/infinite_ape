from __future__ import annotations

from map_reduce_arb.partner_shared_info import (
    format_partner_shared_information,
    resolve_partner_shared_scope,
)


def test_resolve_scope_from_metadata() -> None:
    raw = {
        "metadata": {"creditSummaryScope": "legal_entity"},
        "client": {"partnerType": "GROUP"},
        "data": {"data": {"legalEntities": []}},
    }
    assert resolve_partner_shared_scope(raw) == "legal_entity"


def test_resolve_scope_from_partner_type() -> None:
    raw = {
        "client": {"partnerType": "BUSINESS_RELATION"},
        "data": {"data": {"legalEntities": []}},
    }
    assert resolve_partner_shared_scope(raw) == "business_relation"


def test_group_format_lists_group_and_empty_legal_entities() -> None:
    raw = {
        "client": {"partnerType": "GROUP"},
        "data": {
            "data": {
                "legalEntities": [
                    {
                        "entityType": "GROUP",
                        "legalEntityIdGPID": "G-1",
                        "organizationName": "HoldCo",
                    }
                ]
            }
        },
    }
    text = format_partner_shared_information(raw)
    assert "HoldCo" in text
    assert "G-1" in text
    assert "Legal entities" in text


def test_group_format_lists_legal_entity_children() -> None:
    raw = {
        "metadata": {"creditSummaryScope": "group"},
        "data": {
            "data": {
                "legalEntities": [
                    {
                        "entityType": "GROUP",
                        "legalEntityIdGPID": "G-1",
                        "organizationName": "Group Root",
                    },
                    {
                        "entityType": "LegalEntity",
                        "legalEntityIdGPID": "LE-99",
                        "organizationName": "Subsidiary",
                        "vatNumber": "CHE-1",
                        "groupIndustryCode": "123",
                        "groupIndustryCodeDescription": "Manufacturing",
                        "risk": {"probabilityOfDefaultGradeCode": "3"},
                        "crifData": {"crifScoreValue": "77"},
                    },
                ]
            }
        },
    }
    text = format_partner_shared_information(raw)
    assert "Group Root" in text
    assert "Subsidiary" in text
    assert "LE-99" in text
    assert "PD GRADE: 3" in text
    assert "CRIF Score: 77" in text
    assert "Manufacturing" in text


def test_legal_entity_format_lists_business_relations() -> None:
    raw = {
        "metadata": {"creditSummaryScope": "legal_entity"},
        "client": {"id": "LE-1"},
        "data": {
            "data": {
                "legalEntities": [
                    {
                        "entityType": "LegalEntity",
                        "legalEntityIdGPID": "LE-1",
                        "organizationName": "Acme AG",
                        "groupIndustryCode": "999",
                        "bankingRelations": [
                            {
                                "bankingRelationNumber": "BR-100",
                                "name": "Main BR",
                                "risk": {"probabilityOfDefaultGradeCode": "4"},
                                "crifData": {"crifScoreValue": "80"},
                            }
                        ],
                    }
                ]
            }
        },
    }
    text = format_partner_shared_information(raw)
    assert "Acme AG" in text
    assert "BR-100" in text
    assert "Main BR" in text
    assert "PD GRADE: 4" in text


def test_business_relation_format() -> None:
    raw = {
        "metadata": {"creditSummaryScope": "business_relation"},
        "client": {"bankingRelationshipNumber": "BR-200"},
        "data": {
            "data": {
                "legalEntities": [
                    {
                        "entityType": "Standalone_Company",
                        "legalEntityIdGPID": "LE-2",
                        "organizationName": "Standalone SA",
                        "groupIndustryCode": "111",
                        "bankingRelations": [
                            {
                                "bankingRelationNumber": "BR-200",
                                "name": "Treasury BR",
                                "vatNumber": "CHE-9",
                                "risk": {"probabilityOfDefaultGradeCode": "2"},
                                "crifData": {"crifScoreValue": "90"},
                            }
                        ],
                    }
                ]
            }
        },
    }
    text = format_partner_shared_information(raw)
    assert "BR-200" in text
    assert "Treasury BR" in text
    assert "PD GRADE: 2" in text
    assert "CRIF Score: 90" in text
