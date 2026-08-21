import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def calculate_health_score(records: List[Dict[str, Any]], schema: Dict[str, str]) -> Tuple[float, str, Dict[str, Any]]:
    """
    Computes a health score (0-100) based on record counts and field fill rates.
    Required fields are weighted heavily (1.0), optional fields are weighted lighter (0.25).
    Returns (health_score, status, detailed_report).
    """
    if not records:
        return 0.0, "FAILED", {
            "error": "No records extracted",
            "total_records": 0,
            "field_stats": {field: 0.0 for field in schema.keys()}
        }

    total = len(records)
    field_counts = {field: 0 for field in schema.keys()}

    for rec in records:
        for field in schema.keys():
            val = rec.get(field)
            if val is not None and str(val).strip() != "":
                field_counts[field] += 1

    fill_rates = {field: field_counts[field] / total for field in schema.keys()}

    # Separate weights
    required_fields = [f for f, req in schema.items() if req == "required"]
    optional_fields = [f for f, req in schema.items() if req == "optional"]

    # If schema is empty, default to 100%
    if not required_fields and not optional_fields:
        return 100.0, "HEALTHY", {"total_records": total, "field_stats": {}}

    weighted_score_sum = 0.0
    total_weight = 0.0

    for f in required_fields:
        weighted_score_sum += fill_rates[f] * 1.0
        total_weight += 1.0

    for f in optional_fields:
        weighted_score_sum += fill_rates[f] * 0.25
        total_weight += 0.25

    health_score = (weighted_score_sum / total_weight) * 100.0
    
    # Calculate state
    # If any required field is completely missing (0% fill rate), mark as FAILED or DEGRADED
    completely_missing_required = [f for f in required_fields if fill_rates[f] == 0.0]
    
    if len(completely_missing_required) == len(required_fields) or health_score < 30.0:
        status = "FAILED"
    elif completely_missing_required or health_score < 90.0:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    details = {
        "total_records": total,
        "fill_rates": fill_rates,
        "completely_missing_required": completely_missing_required,
        "status": status
    }

    return round(health_score, 1), status, details

def diff_selector_mappings(old_mapping: Dict[str, str], new_mapping: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Diffs old selector configurations with new ones, classifying changes into:
    - ADDED: Selectors present in new mapping but not in old mapping
    - REMOVED: Selectors present in old mapping but not in new mapping
    - CHANGED: Selectors present in both but with different selector values
    """
    changes = {
        "ADDED": [],
        "REMOVED": [],
        "CHANGED": []
    }

    for key, val in new_mapping.items():
        if key not in old_mapping:
            changes["ADDED"].append(f"{key} (using '{val}')")
        elif old_mapping[key] != val:
            changes["CHANGED"].append(f"{key}: '{old_mapping[key]}' → '{val}'")

    for key, val in old_mapping.items():
        if key not in new_mapping:
            changes["REMOVED"].append(f"{key} (was '{val}')")

    return changes
