#!/usr/bin/env python3

"""
Enhanced Q Clause Processing with FileMaker Integration
Classifies Q clauses and prepares them for FileMaker workflow integration
"""

import re
import json

def get_q_clause_classification():
    """
    Define Q clause business rules and classification
    """
    return {
        # Auto-accept - Standard clauses that don't affect timesheet pricing
        "auto_accept": {
            "Q1": {
                "description": "QUALITY SYSTEMS REQUIREMENTS",
                "timesheet_impact": False,
                "action": "ACCEPT",
                "notes": "Standard quality compliance - no special handling"
            },
            "Q5": {
                "description": "CERTIFICATION OF CONFORMANCE AND RECORD RETENTION",
                "timesheet_impact": False, 
                "action": "ACCEPT",
                "notes": "Standard COC - include in normal process"
            },
            "Q26": {
                "description": "PACKING FOR SHIPMENT",
                "timesheet_impact": False,
                "action": "ACCEPT", 
                "notes": "Standard packing - no additional cost"
            }
        },
        
        # Review required - May affect timesheet/pricing
        "review_required": {
            "Q2": {
                "description": "SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY",
                "timesheet_impact": True,
                "action": "REVIEW",
                "notes": "Customer access required - coordinate scheduling",
                "alert_level": "MEDIUM"
            },
            "Q9": {
                "description": "CORRECTIVE ACTION", 
                "timesheet_impact": True,
                "action": "REVIEW",
                "notes": "CA documentation required - add time for reporting",
                "alert_level": "MEDIUM"
            },
            "Q11": {
                "description": "SPECIAL PROCESS SOURCES REQUIRED",
                "timesheet_impact": True,
                "action": "REVIEW",
                "notes": "Verify certifications - may require source approval",
                "alert_level": "HIGH"
            },
            "Q13": {
                "description": "REPORT OF DISCREPANCY # Quality Notification (QN)",
                "timesheet_impact": True,
                "action": "REVIEW", 
                "notes": "QN reporting required - add admin time",
                "alert_level": "HIGH"
            },
            "Q14": {
                "description": "FOREIGN OBJECT DAMAGE (FOD)",
                "timesheet_impact": True,
                "action": "REVIEW",
                "notes": "FOD prevention measures - additional handling time",
                "alert_level": "MEDIUM"
            }
        },
        
        # Object to - Typically reject or negotiate
        "object_to": {
            "Q15": {
                "description": "ANTI-TERRORIST POLICY",
                "timesheet_impact": False,
                "action": "OBJECT",
                "notes": "Standard objection - conflicts with commercial practices",
                "alert_level": "HIGH"
            },
            "Q32": {
                "description": "FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]",
                "timesheet_impact": False,
                "action": "OBJECT", 
                "notes": "Flowdown too broad - negotiate specific requirements",
                "alert_level": "HIGH"
            },
            "Q33": {
                "description": "FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS",
                "timesheet_impact": False,
                "action": "OBJECT",
                "notes": "FAR inappropriate for commercial work - standard objection",
                "alert_level": "CRITICAL"
            }
        }
    }

def classify_and_process_q_clauses(quality_clauses_dict):
    """
    Process extracted Q clauses and classify them for business handling
    """
    if not quality_clauses_dict:
        return {
            "total_clauses": 0,
            "accept_clauses": [],
            "review_clauses": [], 
            "object_clauses": [],
            "unknown_clauses": [],
            "timesheet_impact": "NONE",
            "action_required": False,
            "summary": "No Q clauses found",
            "filemaker_fields": {}
        }
    
    classification = get_q_clause_classification()
    
    result = {
        "total_clauses": len(quality_clauses_dict),
        "accept_clauses": [],
        "review_clauses": [],
        "object_clauses": [], 
        "unknown_clauses": [],
        "timesheet_impact": "NONE",
        "action_required": False,
        "summary": "",
        "filemaker_fields": {}
    }
    
    # Classify each Q clause
    for q_number, description in quality_clauses_dict.items():
        clause_data = {"number": q_number, "description": description}
        
        # Find in classification
        found = False
        for category, clauses in classification.items():
            if q_number in clauses:
                clause_info = clauses[q_number]
                clause_data.update(clause_info)
                
                if category == "auto_accept":
                    result["accept_clauses"].append(clause_data)
                elif category == "review_required":
                    result["review_clauses"].append(clause_data)
                    if clause_info.get("timesheet_impact"):
                        result["timesheet_impact"] = "MEDIUM" if result["timesheet_impact"] == "NONE" else "HIGH"
                elif category == "object_to":
                    result["object_clauses"].append(clause_data)
                    result["action_required"] = True
                
                found = True
                break
        
        if not found:
            result["unknown_clauses"].append(clause_data)
            result["action_required"] = True
            result["timesheet_impact"] = "HIGH"
    
    # Determine overall timesheet impact
    if result["review_clauses"] or result["unknown_clauses"]:
        if any(c.get("alert_level") == "HIGH" for c in result["review_clauses"]):
            result["timesheet_impact"] = "HIGH"
        elif any(c.get("alert_level") == "MEDIUM" for c in result["review_clauses"]):
            if result["timesheet_impact"] == "NONE":
                result["timesheet_impact"] = "MEDIUM"
    
    # Generate summary
    summary_parts = []
    if result["accept_clauses"]:
        summary_parts.append(f"{len(result['accept_clauses'])} auto-accept")
    if result["review_clauses"]:
        summary_parts.append(f"{len(result['review_clauses'])} need review")
    if result["object_clauses"]:
        summary_parts.append(f"{len(result['object_clauses'])} to object")
    if result["unknown_clauses"]:
        summary_parts.append(f"{len(result['unknown_clauses'])} unknown")
    
    result["summary"] = "; ".join(summary_parts) if summary_parts else "No clauses"
    
    # Prepare FileMaker fields (Option 2: Detailed Tracking)
    result["filemaker_fields"] = {
        "Q_Clauses_Accept": ", ".join([c["number"] for c in result["accept_clauses"]]),
        "Q_Clauses_Review": ", ".join([c["number"] for c in result["review_clauses"]]), 
        "Q_Clauses_Object": ", ".join([c["number"] for c in result["object_clauses"]]),
        "Q_Clauses_Status": "PENDING_REVIEW" if result["action_required"] else "ACCEPTED",
        "Q_Timesheet_Impact": result["timesheet_impact"],
        "Q_Action_Required": result["action_required"]
    }
    
    return result

def extract_quality_clauses_enhanced(text):
    """
    Enhanced Q clause extraction with classification
    """
    quality_clauses = {}
    
    # Define known quality clauses and their complete descriptions
    known_clauses = {
        'Q1': 'QUALITY SYSTEMS REQUIREMENTS',
        'Q2': 'SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY',
        'Q5': 'CERTIFICATION OF CONFORMANCE AND RECORD RETENTION',
        'Q9': 'CORRECTIVE ACTION',
        'Q11': 'SPECIAL PROCESS SOURCES REQUIRED',
        'Q13': 'REPORT OF DISCREPANCY # Quality Notification (QN)',
        'Q14': 'FOREIGN OBJECT DAMAGE (FOD)',
        'Q15': 'ANTI-TERRORIST POLICY',
        'Q26': 'PACKING FOR SHIPMENT',
        'Q32': 'FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]',
        'Q33': 'FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS'
    }
    
    # Extract Q numbers that actually appear in the text
    q_numbers_found = re.findall(r'(Q\d+)', text.upper())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_q_numbers = []
    for q in q_numbers_found:
        if q not in seen:
            seen.add(q)
            unique_q_numbers.append(q)
    
    # Map found Q numbers to their descriptions
    for q_number in unique_q_numbers:
        if q_number in known_clauses:
            quality_clauses[q_number] = known_clauses[q_number]
        else:
            # For unknown Q numbers, try to extract description from context
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if q_number in line.upper():
                    # Try to get description from same line or following lines
                    description_parts = []
                    remaining = line.split(q_number, 1)
                    if len(remaining) > 1:
                        desc = remaining[1].strip()
                        if desc:
                            description_parts.append(desc)
                    
                    # Look at next couple lines for continuation
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not re.match(r'^Q\d+', next_line.upper()) and len(next_line) < 60:
                            description_parts.append(next_line)
                        else:
                            break
                    
                    if description_parts:
                        quality_clauses[q_number] = ' '.join(description_parts).strip()
                    break
    
    # Classify and process the Q clauses
    processed_result = classify_and_process_q_clauses(quality_clauses)
    
    return quality_clauses, processed_result

# Test the enhanced function
if __name__ == "__main__":
    # Test with sample Q clauses from PO 4551241534
    test_q_clauses = {
        'Q11': 'SPECIAL PROCESS SOURCES REQUIRED',
        'Q1': 'QUALITY SYSTEMS REQUIREMENTS', 
        'Q2': 'SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY',
        'Q5': 'CERTIFICATION OF CONFORMANCE AND RECORD RETENTION',
        'Q9': 'CORRECTIVE ACTION',
        'Q13': 'REPORT OF DISCREPANCY # Quality Notification (QN)',
        'Q14': 'FOREIGN OBJECT DAMAGE (FOD)',
        'Q15': 'ANTI-TERRORIST POLICY',
        'Q26': 'PACKING FOR SHIPMENT',
        'Q32': 'FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]',
        'Q33': 'FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS'
    }
    
    print("🧪 Testing Enhanced Q Clause Processing")
    print("=" * 60)
    
    result = classify_and_process_q_clauses(test_q_clauses)
    
    print(f"📊 Analysis Results:")
    print(f"  Total Clauses: {result['total_clauses']}")
    print(f"  Summary: {result['summary']}")
    print(f"  Timesheet Impact: {result['timesheet_impact']}")
    print(f"  Action Required: {result['action_required']}")
    
    print(f"\n🟢 Auto-Accept ({len(result['accept_clauses'])}):")
    for clause in result["accept_clauses"]:
        print(f"  {clause['number']}: {clause['notes']}")
    
    print(f"\n🟡 Review Required ({len(result['review_clauses'])}):")
    for clause in result["review_clauses"]:
        print(f"  {clause['number']}: {clause['notes']} [{clause.get('alert_level', 'MEDIUM')}]")
    
    print(f"\n🔴 Object To ({len(result['object_clauses'])}):")
    for clause in result["object_clauses"]:
        print(f"  {clause['number']}: {clause['notes']} [{clause.get('alert_level', 'HIGH')}]")
    
    print(f"\n🎯 FileMaker Fields:")
    for field, value in result["filemaker_fields"].items():
        print(f"  {field}: '{value}'")
