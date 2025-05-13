"""
Sanskrit Phonetic Engine for the Vishnu Sahasranama Nirukti Project

This module implements a specialized phonetic engine for Sanskrit text normalization and matching,
using a character-by-character approach with Sanskrit-specific linguistic rules.
"""

import re
from fuzzywuzzy import fuzz, process

class SanskritPhoneticEngine:
    def __init__(self):
        # Character equivalence map for Sanskrit
        self.char_map = {
            # Long vowels
            'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṝ': 'ṛ', 'ḹ': 'ḷ',
            # Nasals and visarga
            'ṃ': 'm', 'ṁ': 'm', 'ḥ': 'h',
            # Retroflex consonants
            'ṭ': 't', 'ḍ': 'd', 'ṇ': 'n',
            # Palatal and retroflex sibilants
            'ś': 's', 'ṣ': 's',
            # Other special characters
            'ṅ': 'n', 'ñ': 'n'
        }
        
        # Common Sanskrit compound syllables with standardized forms
        self.compound_patterns = [
            ('sh', 's'),  # sh → s (śiva → siva)
            ('ch', 'c'),  # ch → c (cakra → cakra)
            ('esh', 'es'),  # Only apply this after sh → s conversion
            ('aa', 'a'),  # aa → a (shaanti → santi)
            ('ee', 'i'),  # ee → i (veena → vina)
            ('oo', 'u'),  # oo → u (pooja → puja)
            ('ksh', 'ks'),  # ksh → ks (lakshmi → laksmi)
            ('dh', 'd'),  # dh → d (madhava → madava)
        ]
        
        # Doubled consonants to be simplified
        self.doubled_consonants = [
            'tt', 'kk', 'ss', 'dd', 'nn', 'mm',
            'll', 'pp', 'jj'
        ]

    def normalize_text(self, text):
        """
        Normalize Sanskrit text by removing diacritics for comparison purposes
        Maintains original text alongside normalized version
        """
        if not text:
            return {"original": "", "normalized": ""}
            
        normalized = text.lower().strip()
        
        # Step 1: Replace all diacritics with plain Roman letters
        for sanskrit, latin in self.char_map.items():
            normalized = normalized.replace(sanskrit, latin)
        
        # Step 2: Apply compound patterns in specific order
        # Handle 'sh' → 's' first as it's critical
        normalized = normalized.replace('sh', 's')
        
        # Then apply other patterns
        for pattern, replacement in self.compound_patterns:
            if pattern != 'sh':  # Skip 'sh' as we've already handled it
                normalized = normalized.replace(pattern, replacement)
        
        # Step 3: Handle doubled consonants
        for double in self.doubled_consonants:
            normalized = normalized.replace(double, double[0])
        
        return {
            'original': text,
            'normalized': normalized
        }

    def find_matches(self, query, dictionary, threshold=70):
        """
        Find matching names in a dictionary using phonetic similarity.
        
        This enhanced version handles partial names better.
        """
        normalized_query = self.normalize_text(query)['normalized']
        results = {}
        
        # Check for exact matches first
        for name, data in dictionary.items():
            normalized_name = self.normalize_text(name)['normalized']
            
            # If normalized form matches exactly
            if normalized_name == normalized_query:
                results[name] = {
                    'data': data,
                    'score': 100,
                    'match_type': 'exact'
                }
                return results  # Return exact match immediately
        
        # No exact match, check for partial matches (prefix matching)
        partial_matches = {}
        for name in dictionary.keys():
            normalized_name = self.normalize_text(name)['normalized']
            
            # Check if query is a prefix of the name (partial match)
            if normalized_name.startswith(normalized_query) and len(normalized_query) >= 3:
                match_percentage = (len(normalized_query) / len(normalized_name)) * 100
                # Higher score for closer length matches
                partial_matches[name] = {
                    'data': dictionary[name],
                    'score': min(95, match_percentage + 70),  # Cap at 95, but ensure good partial matches score well
                    'match_type': 'partial'
                }
        
        # If we have good partial matches, return them
        if partial_matches:
            # Sort by score
            sorted_matches = sorted(partial_matches.items(), key=lambda x: x[1]['score'], reverse=True)
            # Take top matches (max 3)
            top_matches = dict(sorted_matches[:3])
            return top_matches
            
        # Try fuzzy matching
        for name in dictionary.keys():
            normalized_name = self.normalize_text(name)['normalized']
            
            # Use fuzzywuzzy to calculate similarity
            ratio = fuzz.ratio(normalized_query, normalized_name)
            if ratio >= threshold:
                results[name] = {
                    'data': dictionary[name],
                    'score': ratio,
                    'match_type': 'fuzzy'
                }
        
        # If still no matches, try substring matching
        if not results:
            for name in dictionary.keys():
                normalized_name = self.normalize_text(name)['normalized']
                if normalized_query in normalized_name and len(normalized_query) >= 2:
                    # Score based on what percentage of the name matches
                    match_percentage = (len(normalized_query) / len(normalized_name)) * 100
                    results[name] = {
                        'data': dictionary[name],
                        'score': min(80, match_percentage + 50),  # Cap at 80
                        'match_type': 'substring'
                    }
        
        # Return top matches by score
        sorted_matches = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
        return dict(sorted_matches[:3])
    
    def extract_sanskrit_terms(self, text):
        """
        Extract potential Sanskrit terms with diacritics from text
        """
        # Look for words that contain Sanskrit-specific diacritic characters
        diacritic_pattern = r'\b\w*[āīūṛṝḷḹṃṁḥṅñṭḍṇśṣ]\w*\b'
        return re.findall(diacritic_pattern, text)
    
    def guess_sanskrit_name(self, query, dictionary):
        """
        Make an educated guess for which Sanskrit name the user is looking for,
        even with highly variant spellings.
        """
        # Try direct normalization first
        direct_matches = self.find_matches(query, dictionary, threshold=75)
        if direct_matches:
            return direct_matches
        
        # If no direct match, try analyzing and transforming the query
        # Common transliteration variations to try
        variations = [
            # Try with added 'h' after certain consonants
            query.replace('s', 'sh'),
            query.replace('k', 'kh') if 'k' in query else query,
            query.replace('g', 'gh') if 'g' in query else query,
            query.replace('c', 'ch') if 'c' in query else query,
            query.replace('j', 'jh') if 'j' in query else query,
            query.replace('t', 'th') if 't' in query else query,
            query.replace('d', 'dh') if 'd' in query else query,
            query.replace('p', 'ph') if 'p' in query else query,
            query.replace('b', 'bh') if 'b' in query else query,
            
            # Try with vowel variations
            query.replace('a', 'ā') if 'a' in query else query,
            query.replace('i', 'ī') if 'i' in query else query,
            query.replace('u', 'ū') if 'u' in query else query,
        ]
        
        # Try each variation
        for variant in variations:
            if variant != query:  # Skip if it's the same as original query
                matches = self.find_matches(variant, dictionary, threshold=70)
                if matches:
                    return matches
        
        # Lower the threshold for a last attempt
        return self.find_matches(query, dictionary, threshold=60)