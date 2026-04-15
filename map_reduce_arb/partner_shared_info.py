"""
Deterministic "Partner Shared Information" text for credit summary reports.

Scope is resolved from optional metadata / client.partnerType, with safe fallbacks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

PartnerScope = Literal["group", "legal_entity", "business_relation"]


def _norm(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip().lower()


def _legal_entities(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = raw.get("data") or {}
    inner = data.get("data") or {}
    le = inner.get("legalEntities")
    return le if isinstance(le, list) else []


def _client(raw: Dict[str, Any]) -> Dict[str, Any]:
    c = raw.get("client")
    return c if isinstance(c, dict) else {}


def _metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    m = raw.get("metadata")
    return m if isinstance(m, dict) else {}


def resolve_partner_shared_scope(raw: Dict[str, Any]) -> PartnerScope:
    """Resolve which summary shape to render."""
    meta = _metadata(raw)
    for key in ("creditSummaryScope", "partnerSharedInformationScope", "summaryScope"):
        v = meta.get(key) if key in meta else raw.get(key)
        if v is None:
            continue
        n = _norm(v).replace("-", "_")
        if n in ("group",):
            return "group"
        if n in ("legal_entity", "legalentity"):
            return "legal_entity"
        if n in ("business_relation", "businessrelation", "br", "standalone_company", "standalone"):
            return "business_relation"

    pt = _norm(_client(raw).get("partnerType")).replace(" ", "_")
    if pt == "group":
        return "group"
    if pt in ("legal_entity", "legalentity"):
        return "legal_entity"
    if pt in ("business_relation", "businessrelationship", "br", "standalone_company"):
        return "business_relation"

    entities = _legal_entities(raw)
    if any(_norm(e.get("entityType")) == "group" for e in entities):
        return "group"
    le_only = [e for e in entities if _norm(e.get("entityType")) == "legalentity"]
    if len(le_only) == 1 and not any(_norm(e.get("entityType")) == "group" for e in entities):
        return "legal_entity"
    return "group"


def _vat(obj: Dict[str, Any]) -> Optional[str]:
    v = obj.get("vatNumber")
    if v is None or (isinstance(v, str) and not v.strip()):
        v = obj.get("VATNumber")
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _industry_code_desc(le: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    code = le.get("groupIndustryCode")
    desc = le.get("groupIndustryCodeDescription")
    c = str(code).strip() if code is not None else None
    d = str(desc).strip() if desc is not None else None
    if c == "":
        c = None
    if d == "":
        d = None
    return c, d


def _pd_crif(obj: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    risk = obj.get("risk") or {}
    pd = risk.get("probabilityOfDefaultGradeCode") if isinstance(risk, dict) else None
    crif_block = obj.get("crifData") or {}
    crif = crif_block.get("crifScoreValue") if isinstance(crif_block, dict) else None
    pds = str(pd).strip() if pd is not None else ""
    cs = str(crif).strip() if crif is not None else ""
    return (pds or None, cs or None)


def _pd_crif_with_br_fallback(le: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    pd, crif = _pd_crif(le)
    if pd is not None or crif is not None:
        return pd, crif
    for br in le.get("bankingRelations") or []:
        if not isinstance(br, dict):
            continue
        pd, crif = _pd_crif(br)
        if pd is not None or crif is not None:
            return pd, crif
    return None, None


def _br_display_name(br: Dict[str, Any]) -> str:
    n = br.get("organizationName") or br.get("name")
    if n is None:
        return ""
    return str(n).strip()


def _find_group_entity(entities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in entities:
        if _norm(e.get("entityType")) == "group":
            return e
    return None


def _find_legal_entity(entities: List[Dict[str, Any]], client: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cid = client.get("id")
    if cid is not None:
        for e in entities:
            if str(e.get("legalEntityIdGPID")) == str(cid) and _norm(e.get("entityType")) == "legalentity":
                return e
    for e in entities:
        if _norm(e.get("entityType")) == "legalentity":
            return e
    return None


def _find_business_relation(
    entities: List[Dict[str, Any]], client: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    br_key = client.get("bankingRelationshipNumber") or client.get("bankingRelationNumber")
    cid = client.get("id")

    if br_key is not None:
        for le in entities:
            for br in le.get("bankingRelations") or []:
                if not isinstance(br, dict):
                    continue
                if str(br.get("bankingRelationNumber")) == str(br_key):
                    return le, br

    for le in entities:
        if _norm(le.get("entityType")) in ("standalone_company", "legalentity"):
            if cid is not None and str(le.get("legalEntityIdGPID")) != str(cid):
                continue
            brs = [b for b in (le.get("bankingRelations") or []) if isinstance(b, dict)]
            if len(brs) == 1:
                return le, brs[0]
            if br_key is None and len(brs) == 1:
                return le, brs[0]

    for le in entities:
        for br in le.get("bankingRelations") or []:
            if not isinstance(br, dict):
                continue
            if cid is not None and str(br.get("bankingRelationNumber")) == str(cid):
                return le, br

    return None, None


def _append_pd_crif_lines(lines: List[str], pd: Optional[str], crif: Optional[str]) -> None:
    if pd:
        lines.append(f"- PD GRADE: {pd}")
    if crif:
        lines.append(f"- CRIF Score: {crif}")


def format_partner_shared_information(raw: Dict[str, Any]) -> str:
    """Build markdown for the Partner Shared Information section."""
    if not raw:
        return "No client payload available for Partner Shared Information."

    scope = resolve_partner_shared_scope(raw)
    entities = _legal_entities(raw)
    client = _client(raw)

    if scope == "group":
        return _format_group(entities)
    if scope == "legal_entity":
        return _format_legal_entity(entities, client)
    return _format_business_relation(entities, client)


def _format_group(entities: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    group = _find_group_entity(entities)
    if group:
        lines.append(f"- **Name:** {group.get('organizationName') or '—'}")
        lines.append(f"- **GPID:** {group.get('legalEntityIdGPID') or '—'}")
    else:
        lines.append("- **Group:** (no entity with entityType = Group in payload)")
    lines.append("")
    lines.append("### Legal entities")
    children = [e for e in entities if _norm(e.get("entityType")) == "legalentity"]
    if not children:
        lines.append("_No legal entities listed._")
        return "\n".join(lines)

    for i, le in enumerate(children, 1):
        lines.append(f"#### {i}. {le.get('organizationName') or '—'}")
        lines.append(f"- **GPID:** {le.get('legalEntityIdGPID') or '—'}")
        v = _vat(le)
        if v:
            lines.append(f"- **VAT:** {v}")
        gc, gd = _industry_code_desc(le)
        if gc:
            lines.append(f"- **groupIndustryCode:** {gc}")
        if gd:
            lines.append(f"- **groupIndustryCodeDescription:** {gd}")
        pd, crif = _pd_crif_with_br_fallback(le)
        _append_pd_crif_lines(lines, pd, crif)
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_legal_entity(entities: List[Dict[str, Any]], client: Dict[str, Any]) -> str:
    le = _find_legal_entity(entities, client)
    if le is None:
        return "_Could not resolve a Legal Entity (entityType = LegalEntity) for this request._"

    lines: List[str] = []
    lines.append(f"- **Name:** {le.get('organizationName') or '—'}")
    lines.append(f"- **GPID:** {le.get('legalEntityIdGPID') or '—'}")
    lines.append("")
    lines.append("### Business relations")
    brs = [b for b in (le.get("bankingRelations") or []) if isinstance(b, dict)]
    if not brs:
        lines.append("_No business relations listed._")
        return "\n".join(lines)

    for i, br in enumerate(brs, 1):
        name = _br_display_name(br) or "—"
        lines.append(f"#### {i}. {name}")
        lines.append(f"- **bankingRelationshipNumber:** {br.get('bankingRelationNumber') or '—'}")
        v = _vat(br)
        if not v:
            v = _vat(le)
        if v:
            lines.append(f"- **VAT:** {v}")
        gc, gd = _industry_code_desc(le)
        if gc:
            lines.append(f"- **groupIndustryCode:** {gc}")
        if gd:
            lines.append(f"- **groupIndustryCodeDescription:** {gd}")
        pd, crif = _pd_crif(br)
        _append_pd_crif_lines(lines, pd, crif)
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_business_relation(entities: List[Dict[str, Any]], client: Dict[str, Any]) -> str:
    le, br = _find_business_relation(entities, client)
    if br is None:
        return "_Could not resolve a Business Relation for this request._"

    lines: List[str] = []
    name = _br_display_name(br) or (le.get("organizationName") if le else None)
    lines.append(f"- **Name:** {name or '—'}")
    lines.append(f"- **bankingRelationshipNumber:** {br.get('bankingRelationNumber') or '—'}")
    v = _vat(br)
    if not v and le:
        v = _vat(le)
    if v:
        lines.append(f"- **VAT:** {v}")
    if le:
        gc, gd = _industry_code_desc(le)
        if gc:
            lines.append(f"- **groupIndustryCode:** {gc}")
        if gd:
            lines.append(f"- **groupIndustryCodeDescription:** {gd}")
    pd, crif = _pd_crif(br)
    _append_pd_crif_lines(lines, pd, crif)
    return "\n".join(lines).rstrip()
