#!/usr/bin/env python3

"""
Q Clause Analysis and Classification System
Analyzes extracted Quality Clauses and categorizes them for business processing
"""

import sys
import json
import os

# Add the scripts directory to the path
sys.path.append('/volume1/Main/Main/ParkerPOsOCR/docker_system/scripts')

def classify_q_clauses():
    """
    Classify Q clauses into business categories for processing decisions
    """
    
    # Q Clause Classification based on business impact
    q_clause_classification = {
        # ALWAYS COMPLY - Standard clauses we automatically accept
        "always_comply": {
            "Q1": {
                "description": "QUALITY SYSTEMS REQUIREMENTS",
                "action": "ACCEPT",
                "timesheet_note": "Standard quality compliance",
                "auto_process": True
            },
            "Q5": {
                "description": "CERTIFICATION OF CONFORMANCE AND RECORD RETENTION", 
                "action": "ACCEPT",
                "timesheet_note": "Standard COC requirements",
                "auto_process": True
            },
            "Q26": {
                "description": "PACKING FOR SHIPMENT",
                "action": "ACCEPT", 
                "timesheet_note": "Standard packing requirements",
                "auto_process": True
            }
        },
        
        # SPECIAL ATTENTION - Require review but generally acceptable
        "special_attention": {
            "Q2": {
                "description": "SURVEILLANCE BY MEGGITT AND RIGHT OF ENTRY",
                "action": "REVIEW_REQUIRED",
                "timesheet_note": "Customer surveillance - coordinate access",
                "auto_process": False,
                "alert_level": "MEDIUM"
            },
            "Q9": {
                "description": "CORRECTIVE ACTION",
                "action": "REVIEW_REQUIRED", 
                "timesheet_note": "CA process - document corrective actions",
                "auto_process": False,
                "alert_level": "MEDIUM"
            },
            "Q11": {
                "description": "SPECIAL PROCESS SOURCES REQUIRED",
                "action": "REVIEW_REQUIRED",
                "timesheet_note": "Verify special process certifications",
                "auto_process": False,
                "alert_level": "HIGH"
            },
            "Q13": {
                "description": "REPORT OF DISCREPANCY # Quality Notification (QN)",
                "action": "REVIEW_REQUIRED",
                "timesheet_note": "QN reporting required for discrepancies", 
                "auto_process": False,
                "alert_level": "HIGH"
            },
            "Q14": {
                "description": "FOREIGN OBJECT DAMAGE (FOD)",
                "action": "REVIEW_REQUIRED",
                "timesheet_note": "FOD prevention measures required",
                "auto_process": False, 
                "alert_level": "MEDIUM"
            }
        },
        
        # OBJECT TO - Clauses that require pushback or special negotiation
        "object_to": {
            "Q15": {
                "description": "ANTI-TERRORIST POLICY", 
                "action": "OBJECT",
                "timesheet_note": "Review anti-terrorism requirements - may object",
                "auto_process": False,
                "alert_level": "HIGH",
                "reason": "May conflict with standard business practices"
            },
            "Q32": {
                "description": "FLOWDOWN OF REQUIREMENTS [QUALITY AND ENVIRONMENTAL]",
                "action": "OBJECT",
                "timesheet_note": "Review flowdown requirements - potential objection",
                "auto_process": False,
                "alert_level": "HIGH", 
                "reason": "Flowdown clauses can be overly broad"
            },
            "Q33": {
                "description": "FAR and DOD FAR SUPPLEMENTAL FLOWDOWN PROVISIONS",
                "action": "OBJECT",
                "timesheet_note": "FAR flowdown - likely objection",
                "auto_process": False,
                "alert_level": "CRITICAL",
                "reason": "FAR clauses often inappropriate for commercial work"
            }
        }
    }
    
    return q_clause_classification

def analyze_po_q_clauses(po_json_file):
    """
    Analyze Q clauses from a processed PO and provide recommendations
    """
    
    if not os.path.exists(po_json_file):
        print(f"❌ PO file not found: {po_json_file}")
        return None
    
    # Load PO data
    with open(po_json_file, 'r') as f:
        po_data = json.load(f)
    
    po_number = po_data.get('purchase_order_number', 'Unknown')
    quality_clauses = po_data.get('quality_clauses', {})
    
    if not quality_clauses:
        print(f"ℹ️  PO {po_number}: No Q clauses found")
        return {
            "po_number": po_number,
            "total_clauses": 0,
            "analysis": {},
            "recommendations": []
        }
    
    print(f"\n📋 Analyzing PO {po_number} - Q Clauses")
    print("=" * 60)
    
    classification = classify_q_clauses()
    analysis_result = {
        "po_number": po_number,
        "total_clauses": len(quality_clauses),
        "always_comply": [],
        "special_attention": [],
        "object_to": [],
        "unknown": [],
        "recommendations": [],
        "timesheet_impact": "NONE"
    }
    
    # Classify each Q clause found in the PO
    for q_number, description in quality_clauses.items():
        clause_info = {
            "q_number": q_number,
            "description": description,
            "found_in_classification": False
        }
        
        # Check each category
        for category_name, category_clauses in classification.items():
            if q_number in category_clauses:
                clause_details = category_clauses[q_number]
                clause_info.update(clause_details)
                clause_info["found_in_classification"] = True
                analysis_result[category_name].append(clause_info)
                
                print(f"✅ {q_number}: {clause_details['action']} - {description[:50]}...")
                break
        
        if not clause_info["found_in_classification"]:
            analysis_result["unknown"].append(clause_info)
            print(f"❓ {q_number}: UNKNOWN - {description[:50]}...")
    
    # Generate recommendations
    recommendations = []
    
    if analysis_result["always_comply"]:
        recommendations.append(f"✅ {len(analysis_result['always_comply'])} standard clauses - auto-accept")
        analysis_result["timesheet_impact"] = "LOW"
    
    if analysis_result["special_attention"]:
        high_priority = [c for c in analysis_result["special_attention"] if c.get("alert_level") == "HIGH"]
        recommendations.append(f"⚠️  {len(analysis_result['special_attention'])} clauses need review ({len(high_priority)} high priority)")
        if analysis_result["timesheet_impact"] == "NONE":
            analysis_result["timesheet_impact"] = "MEDIUM"
    
    if analysis_result["object_to"]:
        critical = [c for c in analysis_result["object_to"] if c.get("alert_level") == "CRITICAL"]
        recommendations.append(f"❌ {len(analysis_result['object_to'])} clauses to object ({len(critical)} critical)")
        analysis_result["timesheet_impact"] = "HIGH"
    
    if analysis_result["unknown"]:
        recommendations.append(f"❓ {len(analysis_result['unknown'])} unknown clauses - need classification")
        analysis_result["timesheet_impact"] = "HIGH"
    
    analysis_result["recommendations"] = recommendations
    
    print(f"\n📊 Summary for PO {po_number}:")
    for rec in recommendations:
        print(f"  {rec}")
    print(f"  🕐 Timesheet Impact: {analysis_result['timesheet_impact']}")
    
    return analysis_result

def generate_filemaker_suggestions():
    """
    Generate suggestions for FileMaker field implementation
    """
    
    suggestions = {
        "option_1_simple": {
            "name": "Simple Text Field Approach",
            "fields": [
                {
                    "field_name": "Q_Clauses_Summary", 
                    "type": "Text",
                    "description": "Comma-separated list of Q clause numbers (e.g., 'Q1, Q5, Q11')"
                },
                {
                    "field_name": "Q_Clauses_Alert_Level",
                    "type": "Value List", 
                    "values": ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Highest alert level from any Q clause"
                }
            ],
            "pros": ["Simple to implement", "Minimal database changes"],
            "cons": ["Limited detail", "Hard to report on specific clauses"]
        },
        
        "option_2_detailed": {
            "name": "Detailed Tracking Approach", 
            "fields": [
                {
                    "field_name": "Q_Clauses_Accept",
                    "type": "Text", 
                    "description": "Auto-accepted clauses (e.g., 'Q1, Q5, Q26')"
                },
                {
                    "field_name": "Q_Clauses_Review",
                    "type": "Text",
                    "description": "Clauses requiring review (e.g., 'Q2, Q11')" 
                },
                {
                    "field_name": "Q_Clauses_Object", 
                    "type": "Text",
                    "description": "Clauses to object to (e.g., 'Q15, Q33')"
                },
                {
                    "field_name": "Q_Clauses_Status",
                    "type": "Value List",
                    "values": ["PENDING_REVIEW", "ACCEPTED", "OBJECTION_FILED", "NEGOTIATED"],
                    "description": "Overall status of Q clause handling"
                }
            ],
            "pros": ["Detailed tracking", "Clear action items", "Good for reporting"],
            "cons": ["More fields to manage", "Requires process changes"]
        },
        
        "option_3_workflow": {
            "name": "Workflow Integration Approach",
            "fields": [
                {
                    "field_name": "Q_Clauses_Raw",
                    "type": "Text",
                    "description": "JSON string of all extracted Q clauses with details"
                },
                {
                    "field_name": "Q_Timesheet_Impact", 
                    "type": "Value List",
                    "values": ["NONE", "LOW", "MEDIUM", "HIGH"],
                    "description": "Impact on timesheet/pricing"
                },
                {
                    "field_name": "Q_Action_Required",
                    "type": "Checkbox",
                    "description": "Flags POs that need Q clause review"
                },
                {
                    "field_name": "Q_Notes",
                    "type": "Text", 
                    "description": "Notes about Q clause handling decisions"
                }
            ],
            "pros": ["Integrates with timesheet process", "Preserves all data", "Flexible"],
            "cons": ["Requires workflow changes", "More complex to implement"]
        }
    }
    
    return suggestions

def main():
    """
    Main analysis function
    """
    
    print("🔍 Q CLAUSE ANALYSIS AND FILEMAKER INTEGRATION PLANNING")
    print("=" * 70)
    
    # Analyze existing POs
    po_files = [
        "/volume1/Main/Main/ParkerPOsOCR/POs/4551241534/4551241534_info.json",
        "/volume1/Main/Main/ParkerPOsOCR/POs/4551242061/4551242061_info.json"
    ]
    
    for po_file in po_files:
        if os.path.exists(po_file):
            analyze_po_q_clauses(po_file)
    
    # Generate FileMaker suggestions
    print("\n\n🎯 FILEMAKER IMPLEMENTATION OPTIONS")
    print("=" * 70)
    
    suggestions = generate_filemaker_suggestions()
    
    for option_key, option in suggestions.items():
        print(f"\n📋 {option['name']}")
        print("-" * 50)
        
        print("Fields:")
        for field in option['fields']:
            print(f"  • {field['field_name']} ({field['type']})")
            print(f"    {field['description']}")
            if 'values' in field:
                print(f"    Values: {', '.join(field['values'])}")
        
        print("\nPros:")
        for pro in option['pros']:
            print(f"  ✅ {pro}")
            
        print("Cons:")
        for con in option['cons']:
            print(f"  ⚠️  {con}")
    
    print("\n\n💡 RECOMMENDATIONS")
    print("=" * 40)
    print("1. Start with Option 2 (Detailed Tracking) for better visibility")
    print("2. Add Q clause classification to extraction pipeline") 
    print("3. Create alerts/notifications for high-priority clauses")
    print("4. Consider timesheet integration for pricing impact")

if __name__ == "__main__":
    main()
