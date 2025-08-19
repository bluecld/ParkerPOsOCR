#!/usr/bin/env python3
"""
Enhanced Part Number Validation System
Uses reference list from PartNumbers.xlsx to validate and correct OCR results
"""

import pandas as pd
import re
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
import logging

class PartNumberValidator:
    def __init__(self, excel_path="/volume1/Main/Main/ParkerPOsOCR/docs/PartNumbers.xlsx"):
        self.excel_path = excel_path
        self.part_numbers = set()
        self.part_to_full = {}  # Maps clean part number to full part+op
        self.load_part_numbers()
        
    def load_part_numbers(self):
        """Load part numbers from Excel file"""
        try:
            df = pd.read_excel(self.excel_path)
            logging.info(f"Loaded {len(df)} part numbers from {self.excel_path}")
            
            for _, row in df.iterrows():
                full_part = str(row['Part Number']).strip()
                if '*' in full_part:
                    clean_part = full_part.split('*')[0].upper().strip()
                else:
                    clean_part = full_part.upper().strip()
                
                self.part_numbers.add(clean_part)
                self.part_to_full[clean_part] = full_part
                
            logging.info(f"Processed {len(self.part_numbers)} unique part numbers")
            
        except Exception as e:
            logging.error(f"Error loading part numbers: {e}")
            
    def similarity_score(self, a, b):
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a.upper(), b.upper()).ratio()
        
    def fix_common_ocr_errors(self, text):
        """Fix common OCR character recognition errors"""
        # Common OCR mistakes
        fixes = {
            'Q': '9',  # Q often misread as 9
            'O': '0',  # O often misread as 0
            'I': '1',  # I often misread as 1
            'S': '5',  # S sometimes misread as 5
            'Z': '2',  # Z sometimes misread as 2
        }
        
        corrected_candidates = [text]
        
        # Generate candidates by fixing one character at a time
        for i, char in enumerate(text):
            if char in fixes:
                candidate = text[:i] + fixes[char] + text[i+1:]
                corrected_candidates.append(candidate)
                
        return corrected_candidates
        
    def validate_and_correct(self, ocr_text):
        """
        Validate OCR text against known part numbers and suggest corrections
        Returns: (is_valid, corrected_text, confidence, match_info)
        """
        if not ocr_text:
            return False, ocr_text, 0.0, "Empty input"
            
        # Clean the OCR text
        clean_ocr = ocr_text.strip().upper()
        if '*' in clean_ocr:
            clean_part = clean_ocr.split('*')[0]
            op_part = '*' + clean_ocr.split('*')[1] if '*' in clean_ocr else ''
        else:
            clean_part = clean_ocr
            op_part = ''
            
        # 1. Exact match check
        if clean_part in self.part_numbers:
            full_match = self.part_to_full.get(clean_part, clean_part + op_part)
            return True, full_match, 1.0, f"Exact match found: {clean_part}"
            
        # 2. Try OCR error corrections
        candidates = self.fix_common_ocr_errors(clean_part)
        for candidate in candidates:
            if candidate in self.part_numbers:
                full_match = self.part_to_full.get(candidate, candidate + op_part)
                confidence = self.similarity_score(clean_part, candidate)
                return True, full_match, confidence, f"OCR correction: {clean_part} → {candidate}"
                
        # 3. Fuzzy matching with high threshold
        close_matches = get_close_matches(clean_part, self.part_numbers, 
                                        n=5, cutoff=0.8)
        
        if close_matches:
            best_match = close_matches[0]
            confidence = self.similarity_score(clean_part, best_match)
            full_match = self.part_to_full.get(best_match, best_match + op_part)
            
            return True, full_match, confidence, f"Fuzzy match: {clean_part} → {best_match} (score: {confidence:.3f})"
            
        # 4. Pattern-based validation for new parts
        part_patterns = [
            r'^[A-Z]{2}\d{3,4}-\d+$',  # WA904-8, AB123-4
            r'^\d{6}-\d{1,3}$',        # 970000-101
            r'^[A-Z]+\d+-\d+$',        # KITF1116-1
            r'^\d{6}$',                # 151299
        ]
        
        for pattern in part_patterns:
            if re.match(pattern, clean_part):
                return False, clean_part + op_part, 0.7, f"Valid pattern but not in database: {clean_part}"
                
        return False, ocr_text, 0.0, f"No match found for: {clean_part}"
        
    def get_suggestions(self, ocr_text, max_suggestions=5):
        """Get multiple correction suggestions for manual review"""
        clean_part = ocr_text.strip().upper().split('*')[0]
        
        suggestions = []
        
        # OCR corrections
        candidates = self.fix_common_ocr_errors(clean_part)
        for candidate in candidates:
            if candidate in self.part_numbers:
                score = self.similarity_score(clean_part, candidate)
                suggestions.append((candidate, score, "OCR correction"))
                
        # Fuzzy matches
        close_matches = get_close_matches(clean_part, self.part_numbers, 
                                        n=max_suggestions, cutoff=0.6)
        for match in close_matches:
            score = self.similarity_score(clean_part, match)
            suggestions.append((match, score, "Fuzzy match"))
            
        # Sort by score and remove duplicates
        suggestions = list(set(suggestions))
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:max_suggestions]

def test_validator():
    """Test the validator with known cases"""
    validator = PartNumberValidator()
    
    test_cases = [
        "WAQ04-8*OP20",  # Should correct Q to 9
        "WA904-8*OP20",  # Should validate if exists
        "97O000-101*OP20",  # Should correct O to 0
        "151299*OP40",   # Should validate exact match
        "INVALID-PART",  # Should return no match
    ]
    
    print("Part Number Validation Test Results:")
    print("=" * 50)
    
    for test in test_cases:
        is_valid, corrected, confidence, info = validator.validate_and_correct(test)
        print(f"Input: {test}")
        print(f"Valid: {is_valid}, Corrected: {corrected}")
        print(f"Confidence: {confidence:.3f}, Info: {info}")
        
        if not is_valid or confidence < 0.9:
            suggestions = validator.get_suggestions(test)
            if suggestions:
                print(f"Suggestions: {[s[0] for s in suggestions[:3]]}")
        print("-" * 30)

if __name__ == "__main__":
    test_validator()
