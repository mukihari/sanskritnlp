"""
Sanskrit NLP System for the Vishnu Sahasranama Nirukti Project

This module provides a comprehensive NLP system for handling Sanskrit text,
particularly for the Vishnu Sahasranama, integrating the phonetic engine
with additional linguistic features.
"""

import re
from sanskrit import SanskritPhoneticEngine

class SanskritNLP:
    def __init__(self, dictionary=None):
        # Initialize the phonetic engine
        self.phonetic_engine = SanskritPhoneticEngine()
        
        # If dictionary is not provided, try to import it
        if dictionary is None:
            try:
                from dictionary_108 import vishnu_ashtottaram
                self.dictionary = vishnu_ashtottaram
            except ImportError:
                print("Warning: dictionary_108 module not found.")
                self.dictionary = {}
        else:
            self.dictionary = dictionary
        
        # Store conversation context
        self.context = {
            "last_name": None,
            "last_intent": None,
            "name_in_query": None,
            "last_response": None,
            "partial_query": None
        }
        
        # Define intent keywords and patterns
        self.intent_keywords = {
            "meaning": ["mean", "meaning", "definition", "artha", "significance", 
                       "refer to", "translation", "what does"],
            
            "etymology": ["etymology", "derive", "derivation", "root", "dhatu", 
                         "prakṛyā", "prakrya", "prakrīyā", "origin", "source", 
                         "come from", "formation", "word history", "linguistic origin"],
            
            "analysis": ["analyze", "analyse", "examination", "breakdown", 
                        "details", "information about"],
            
            "pranam": ["pranam", "caturthī", "caturthi", "mantra", "worship", 
                      "namah", "namaḥ", "salutation", "prayer"],
            
            "position": ["position", "number", "where", "located", "place", 
                        "sequence", "location", "rank", "appear", "find", 
                        "placement", "order", "spot", "occurrence"],
            
            "vigrahavākya": ["vigrahavākya", "vigraha", "vigraha vakya", 
                           "explanation", "detailed meaning", "sentence form", 
                           "compound", "breakdown", "grammatical analysis", 
                           "word components", "split compound", "compound splitting"],
        }
        
        # Intent patterns for regex matching
        self.intent_patterns = {
            "meaning": [
                r"(?:give me|tell me|show|explain|what(?: is| does)?|provide)?\s*(?:the)?\s*meaning(?: of)?\s*(.+)",
                r"what does (.+?) mean",
                r"define (.+)",
                r"translation of (.+)",
                r"artha(?: of)? (.+)",
                r"(.+) artha"
            ],

            "etymology": [
                r"(?:what is|explain|give me|show|tell me)?\s*(?:the)?\s*(etymology|origin|derivation|root|dhatu|prakriya|prakṛyā)(?: of)?\s*(.+)",
                r"how is (.+?) derived",
                r"where does (.+?) come from",
                r"how did (.+?) get its name",
                r"what is the root of (.+)"
            ],

            "vigrahavākya": [
                r"(?:what is|explain|give me|show|tell me)?\s*(?:the)?\s*(vigrahav[āa]kya|vigraha vakya|vigraha|compound breakdown|grammatical breakdown|compound analysis|word breakdown|splitting)(?: of)?\s*(.+)",
                r"how is (.+?) broken down",
                r"what is the vigraha of (.+)",
                r"compound splitting of (.+)"
            ],

            "pranam": [
                r"(?:what is|give me|show|tell me|how to)?\s*(?:the)?\s*(pranam|caturth[īi]|mantra|salutation|prayer|offering|worship)(?: for| of)?\s*(.+)",
                r"how to worship (.+)",
                r"how to offer pranam to (.+)",
                r"salutation to (.+)",
                r"mantra for (.+)",
                r"prayer for (.+)",
                r"(.+) caturth[īi]"
            ],

            "analysis": [
                r"(?:analyze|analyse|explain|describe|give me|tell me|what do you know about|details of|everything about|who is|what is)\s*(.+)",
                r"analysis of (.+)",
                r"explanation of (.+)",
                r"info(?:rmation)? about (.+)"
            ],

            "position": [
                r"(?:what is|tell me|give me|show|which|where)?\s*(?:the)?\s*(position|place|rank|location|number|sequence)(?: of)?\s*(.+)",
                r"where is (.+?) (located|mentioned|found)",
                r"what number is (.+)",
                r"which position is (.+)",
                r"sequence number of (.+)",
                r"(.+) comes at what number",
                r"(.+) is at what position",
                r"at what place is (.+)"
            ]
        }

        
        # Classification for query types
        self.query_classes = {
            'meaning': [r'what\s+(does|is)\s+the\s+meaning', r'what\s+(does|is)\s+.+\s+mean'],
            'etymology': [r'etymology', r'derive', r'root', r'origin', r'prakṛyā', r'prakrya'],
            'listing': [r'list', r'show', r'display', r'names', r'all', r'every'],
            'comparison': [r'compare', r'difference', r'different', r'similar', r'similarity'],
            'pranam': [r'pranam', r'caturthī', r'caturthi', r'mantra', r'worship', r'namah'],
            'search': [r'find', r'search', r'related', r'names\s+.*about', r'names\s+.*related']
        }
        
        # Define ontological categories
        self.ontological_categories = {
            'creation': ['sṛṣṭi', 'creation', 'create', 'creator', 'generating'],
            'preservation': ['sthiti', 'maintain', 'preserve', 'sustain', 'sustainer'],
            'destruction': ['laya', 'destroy', 'end', 'dissolve', 'destruction'],
            'time': ['kāla', 'time', 'eternal', 'timeless', 'temporal'],
            'consciousness': ['cit', 'consciousness', 'awareness', 'knowledge', 'knowing'],
            'existence': ['sat', 'existence', 'being', 'reality', 'existent'],
            'bliss': ['ānanda', 'bliss', 'joy', 'happiness', 'delight'],
            'supreme': ['para', 'supreme', 'highest', 'transcendent', 'ultimate']
        }
        
        # Grammatical categories
        self.grammatical_categories = {
            'caturthī': ['pranam', 'mantra', 'prayer', 'salutation', 'worship'],
            'vibhakti': ['case', 'declension'],
            'vacana': ['number', 'singular', 'dual', 'plural'],
            'dhātu': ['root', 'verb root', 'dhatu'],
            'pratyaya': ['suffix', 'affix', 'ending'],
            'upasarga': ['prefix', 'preposition'],
            'samāsa': ['compound', 'samasa'],
            'sandhi': ['junction', 'joining']
        }

    def process_query(self, query):
        """
        Main function to process a user query with comprehensive query detection.
        """
        # Reset name_in_query for the new query
        self.context["name_in_query"] = None
        
        # Convert query to lowercase for easier matching
        query_lower = query.lower().strip()
        
        # Check if this is a concept search query
        concept_patterns = [
            r"names? related to (\w+)",
            r"names? about (\w+)",
            r"show me (\w+) names?",
            r"give me (\w+) names?",
            r"(\w+) names?$",
            r"names? with (\w+)",
            r"(\w+) related names?",
            r"names? for (\w+)",
            r"find names? about (\w+)",
            r"search for (\w+) names?",
            r"list (\w+) names?",
            r"what names? (are|is) related to (\w+)"
        ]
        
        for pattern in concept_patterns:
            match = re.search(pattern, query_lower)
            if match:
                # If there's a second group (for the last pattern), use that, otherwise use the first
                concept = match.group(2) if "what names" in pattern else match.group(1)
                return self.process_concept_query(query)
        
        # Try multiple position patterns to catch various ways users might ask
        position_patterns = [
            # "give me the 23rd name" format
            r'(?:give|show|what\s+is|tell\s+me)(?:\s+about)?(?:\s+the)?\s+(\d+)(?:st|nd|rd|th)(?:\s+name)?',
            
            # "21st name" format
            r'^(\d+)(?:st|nd|rd|th)\s+name$',
            
            # "name in 21st position" format
            r'name\s+in\s+(\d+)(?:st|nd|rd|th)\s+position',
            
            # "position 21" format
            r'position\s+(\d+)$',
            
            # "what name is at position 21" format
            r'what\s+name\s+(?:is|at)\s+(?:at\s+)?position\s+(\d+)',
            
            # "which name is 21st" format
            r'which\s+name\s+is\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)'
        ]
        
        # Try each pattern until we find a match
        for pattern in position_patterns:
            position_match = re.search(pattern, query_lower)
            if position_match:
                try:
                    position = int(position_match.group(1))
                    return self.get_name_by_position(position)
                except (ValueError, IndexError):
                    continue
        
        # Continue with existing logic for partial queries
        if "partial_query" in self.context:
            prev_query = self.context["partial_query"]
            # Check if this is an affirmative response
            if query_lower in ["yes", "yeah", "y", "yep", "correct", "right", "1", "that's it", "yes please", "that's right"]:
                # Extract the suggested name from the previous response
                prev_response = self.context.get("last_response", "")
                if "Did you mean:" in prev_response:
                    suggestion = prev_response.split("Did you mean:")[1].split("(")[0].strip()
                    # Clear the partial query context
                    self.context.pop("partial_query", None)
                    # Process a query about this name
                    return self.process_complete_query(f"Tell me about {suggestion}")
            
            # Check if this is a negative response
            elif query_lower in ["no", "nope", "n", "not this", "wrong", "incorrect", "not what i meant", "not right"]:
                response = "I'm sorry that wasn't what you were looking for. Could you please type the full name or try a different search term?"
                # Clear the partial query context
                self.context.pop("partial_query", None)
                return response
            
            # Check if this is a selection from numbered options
            elif query.isdigit() and int(query) > 0 and int(query) <= 3:
                selection_idx = int(query) - 1
                prev_response = self.context.get("last_response", "")
                
                if "Did you mean:" in prev_response:
                    suggestions_part = prev_response.split("Did you mean:")[1].split("?")[0].strip()
                    suggestions = [s.strip().split(" (")[0].strip() for s in suggestions_part.split(",")]
                    
                    if selection_idx < len(suggestions):
                        selected_name = suggestions[selection_idx]
                        # Clear the partial query context
                        self.context.pop("partial_query", None)
                        return self.process_complete_query(f"Tell me about {selected_name}")
        
        # First, check if this might be a partial name query
        partial_response = self.handle_partial_name_query(query)
        if partial_response:
            # This is a partial name query, store the query and return suggestions
            self.context["partial_query"] = query
            self.context["last_response"] = partial_response
            return partial_response
        
        
        # If we get here, it's a new query - clear last_name from context
        # to prevent old names from affecting the current query
        self.context["last_name"] = None
        
        # Process as a complete query
        return self.process_complete_query(query)

    def process_concept_query(self, query):
        """
        Process a query asking for names related to a concept.
        
        Args:
            query (str): The user query
            
        Returns:
            str: Formatted response with names related to the concept
        """
        # Extract the concept from the query
        concept_patterns = [
            r"names? related to (\w+)",
            r"names? about (\w+)",
            r"show me (\w+) names?",
            r"give me (\w+) names?",
            r"(\w+) names?$",
            r"names? with (\w+)",
            r"(\w+) related names?",
            r"names? for (\w+)",
            r"find names? about (\w+)",
            r"search for (\w+) names?",
            r"list (\w+) names?",
            r"what names? (?:are|is) related to (\w+)"
        ]
        
        concept = None
        for pattern in concept_patterns:
            match = re.search(pattern, query.lower())
            if match:
                # If the pattern has 'what names' format, the concept is in group 2
                if "what names" in pattern:
                    concept = match.group(2)
                else:
                    concept = match.group(1)
                break
        
        # If no pattern matched, try to extract the key concept word
        if not concept:
            words = query.lower().split()
            # Remove common words
            filtered_words = [w for w in words if w not in ["give", "me", "names", "show", "about", "related", "to", "with", "the", "and", "or", "list", "search", "find"]]
            if filtered_words:
                concept = filtered_words[-1]  # Take the last word as the concept
        
        if not concept:
            return "I'm not sure what concept you're looking for. Please specify more clearly, like 'Show me names related to universe' or 'Give me lotus names'."
        
        # Handle multi-word concepts (if the query mentioned something like "names related to divine play")
        multi_word_concept_patterns = [
            r"names? related to ([a-z\s]+)",
            r"names? about ([a-z\s]+)",
            r"names? with ([a-z\s]+)",
            r"([a-z\s]+) related names?",
            r"names? for ([a-z\s]+)",
            r"find names? about ([a-z\s]+)",
            r"search for ([a-z\s]+) names?",
            r"what names? (?:are|is) related to ([a-z\s]+)"
        ]
        
        for pattern in multi_word_concept_patterns:
            match = re.search(pattern, query.lower())
            if match:
                potential_concept = match.group(1).strip()
                # If it's multiple words, use it
                if " " in potential_concept:
                    # Clean it up - remove trailing "names" if present
                    potential_concept = re.sub(r'\s+names?$', '', potential_concept)
                    concept = potential_concept
                    break
        
        # Search for names related to the concept
        results = self.search_names_by_concept(concept)
        
        # Format and return the results
        return self.format_concept_search_results(results, concept)

    def get_name_by_position(self, position):
        """
        Retrieve and provide information about a name at a specific position.
        
        Args:
            position (int): The position number to look for (1-based index)
            
        Returns:
            str: Response with information about the name at that position
        """
        # Find all names with position information
        names_with_position = {}
        for name, data in self.dictionary.items():
            if 'position' in data:
                # Position might be stored as string or int
                try:
                    pos = int(data['position'])
                    names_with_position[pos] = (name, data)
                except (ValueError, TypeError):
                    # Skip if position can't be converted to integer
                    continue
        
        # Check if the requested position exists
        if position in names_with_position:
            name, data = names_with_position[position]
            
            # Build response with available information
            response = [f"**{name}** is the {position}{'st' if position % 10 == 1 and position != 11 else 'nd' if position % 10 == 2 and position != 12 else 'rd' if position % 10 == 3 and position != 13 else 'th'} name in the Viṣṇu Aṣṭottaraśatanāmam."]
            
            # Add meaning if available
            if 'artha' in data:
                response.append(f"\n**Meaning**: {data['artha']}")
            
            # Add etymology if available
            if 'prakṛyā' in data:
                response.append(f"\n**Etymology**: {data['prakṛyā']}")
            
            # Add pranam mantra if available
            if 'caturthī' in data:
                response.append(f"\n**Pranam Mantra**: {data['caturthī']}")
            
            # Suggest what else they can ask
            response.append("\nYou can ask for more details about this name.")
            
            # Update context with this name for follow-up questions
            self.context["last_name"] = name
            
            result = "\n".join(response)
            self.context["last_response"] = result
            return result
        else:
            # No name found at that position
            if position > 108:
                return f"There are only 108 names in the Viṣṇu Aṣṭottaraśatanāmam. Please ask for a position between 1 and 108."
            else:
                return f"I couldn't find a name at position {position} in my database."

    def handle_partial_name_query(self, query):
        """
        Process queries with potential partial names, offering suggestions in a more
        conversational way.
        """
        # Extract potential name
        words = query.split()
        potential_name = words[-1] if words else query
        
        # Try to find matches for the potential name
        matches = self.phonetic_engine.find_matches(potential_name, self.dictionary)
        
        # Check if we have exact matches
        exact_matches = {name: data for name, data in matches.items() 
                        if data.get('match_type') == 'exact'}
        
        if exact_matches:
            # Process as normal query
            return None  # Return None to indicate normal processing
        
        # Check if we have partial or other matches
        if matches:
            # Format suggestions - get top 3 matches for better user experience
            top_matches = sorted(matches.items(), key=lambda x: x[1]['score'], reverse=True)[:3]
            
            suggestions = []
            for i, (name, match_data) in enumerate(top_matches):
                match_type = match_data.get('match_type', 'match')
                score = match_data.get('score', 0)
                suggestions.append(f"{name} ({match_type}, {score:.0f}%)")
            
            response = f"I found partial matches for '{potential_name}'.\n\n"
            response += f"Did you mean: {', '.join(suggestions)}?\n\n"
            response += f"Please confirm by typing Yes or No, or select, from the option below."
            
            return response
        
        # No matches found
        return None  # Continue with normal processing

    def process_complete_query(self, query):
        """
        Process a complete query (not a partial name query) with improved error handling.
        """
        # Normalize query
        query = query.strip()
        
        # Catch empty queries
        if not query:
            response = "Please enter a query about a name from the Viṣṇu Aṣṭottaraśatanāmam."
            print(f"DEBUG: Empty query - returning: {response}")
            return response
        
        # Normal query processing
        intent = self.detect_intent(query)
        name = self.extract_name_from_query(query, intent)
        
        # If name is found, find matches in the dictionary
        matches = {}
        if name:
            matches = self.phonetic_engine.find_matches(name, self.dictionary)
        
        # Update context - but DON'T preserve old name if the new query has no name
        if name:
            self.context["last_name"] = name
                
        self.context["last_intent"] = intent
        
        # No match found handling
        if not matches:
            if name:
                response = self.generate_response(intent, name, matches)
                print(f"DEBUG: No matches found for name '{name}' - returning: {response}")
                return response 
            else:
                response = (
                    "I'm not sure what you're asking. Please try one of these:\n"
                    "- Ask about a specific name (e.g., 'meaning of Govinda')\n"
                    "- Search for names related to a concept (e.g., 'names related to cows')\n"
                    "- Ask about a name's position (e.g., 'what is the 21st name')"
                )
                print(f"DEBUG: No name extracted - returning: {response}")
                return response
        
        # Generate response based on intent and matches
        response = self.generate_response(intent, name, matches)
        self.context["last_response"] = response
        print(f"DEBUG: Generated response for '{name}' - returning: {response}")
        return response

    def detect_intent(self, query):
        """
        Determine the user's intent from the query.
        """
        query = query.lower().strip()
        
        # First try matching against patterns with name extraction
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    # Extract name from pattern match
                    extracted_name = match.group(1).strip()
                    self.context["name_in_query"] = extracted_name
                    return intent
        
        # If no pattern match, try keyword matching
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query:
                    score += 1
            intent_scores[intent] = score
        
        # Get the intent with the highest score
        if intent_scores:
            max_intent = max(intent_scores.items(), key=lambda x: x[1])
            if max_intent[1] > 0:
                return max_intent[0]
        
        # Default to "search" if no clear intent is found
        return "search"
    
    def extract_name_from_query(self, query, intent):
        """
        Extract the Sanskrit name or term from the query.
        """
        # If we already extracted name from pattern match
        if self.context.get("name_in_query"):
            name = self.context["name_in_query"]
            self.context["name_in_query"] = None  # Clear it after using
            return name
        
        # Check if this is a direct name query (e.g., just "Narayana")
        # This is important for when users type just a name
        if query.strip() and len(query.split()) == 1 and query[0].isupper():
            return query.strip()
        
        # Otherwise, extract using other methods
        # 1. Look for Sanskrit terms with diacritics
        sanskrit_terms = self.phonetic_engine.extract_sanskrit_terms(query)
        if sanskrit_terms:
            return sanskrit_terms[0]  # Return the first one found
        
        # 2. Try extracting capitalized words that might be names
        name_pattern = r'\b[A-Z][a-z]+\b'
        names = re.findall(name_pattern, query)
        if names:
            return names[0]
        
        # Note: We do NOT use the last name from context here, as it leads to the issue
        # where previous names incorrectly affect new queries
        
        # 4. Extract the most likely noun as a fallback
        words = query.split()
        for word in words:
            if len(word) > 3 and word not in ["what", "where", "when", "how", "tell", "show", "find", "give"]:
                return word
        
        return None
    
    def classify_query(self, query):
        """
        Classify a query into different types to help determine response strategy.
        """
        query_lower = query.lower()
        
        # Check each pattern
        classification = []
        for category, pattern_list in self.query_classes.items():
            for pattern in pattern_list:
                if re.search(pattern, query_lower):
                    classification.append(category)
                    break
        
        # If no patterns match, default to general query
        if not classification:
            classification = ['general']
        
        return classification

    def identify_grammatical_category(self, query):
        """
        Identify grammatical categories mentioned in the query.
        """
        query_lower = query.lower()
        identified = []
        
        for category, terms in self.grammatical_categories.items():
            for term in terms:
                if term in query_lower:
                    identified.append({
                        'category': category,
                        'matched_term': term
                    })
        
        return identified

    def identify_ontological_category(self, query):
        """
        Identify ontological concepts mentioned in the query.
        """
        query_lower = query.lower()
        identified = []
        
        for category, terms in self.ontological_categories.items():
            for term in terms:
                if term in query_lower:
                    identified.append({
                        'category': category,
                        'matched_term': term
                    })
        
        return identified

    def generate_response(self, intent, name, matches):
        """
        Generate a response based on intent, name, and matches.
        """
        response = ""
        if not matches:
            if name:
                # No matches found for the given name
                suggestions = self.phonetic_engine.guess_sanskrit_name(name, self.dictionary)
                if suggestions:
                    suggestion_names = list(suggestions.keys())
                    suggestions_text = ", ".join(suggestion_names[:3])
                    response = f"I couldn't find information about '{name}'. Did you mean: {suggestions_text}?"
                else:
                    response = f"I couldn't find any information about '{name}' in my database."
            else:
                # No name was extracted from the query
                response = "I'm not sure which name you're asking about. Could you please specify a Sanskrit name?"
            print(f"DEBUG: No matches in generate_response - returning: {response}")
            return response

        # If we have matches, process them
        # If multiple matches, use the one with highest score
        top_match_name = max(matches.items(), key=lambda x: x[1]['score'])[0]
        top_match_data = matches[top_match_name]['data']
        score = matches[top_match_name]['score']
        
        # Format responses based on intent
        if intent == "meaning":
            if 'artha' in top_match_data:
                response = f"**{top_match_name}** means: {top_match_data['artha']}"
            else:
                response = f"I don't have meaning information for {top_match_name}."
                
        elif intent == "etymology":
            if 'prakṛyā' in top_match_data:
                response = f"**Etymology of {top_match_name}**: {top_match_data['prakṛyā']}"
            else:
                response = f"I don't have etymology information for {top_match_name}."
                
        elif intent == "vigrahavākya":
            if 'vigrahavākya' in top_match_data:
                response = f"**Vigrahavākya of {top_match_name}**: {top_match_data['vigrahavākya']}"
            else:
                response = f"I don't have vigrahavākya information for {top_match_name}."
                
        elif intent == "pranam":
            if 'caturthī' in top_match_data:
                response = f"**Pranam mantra for {top_match_name}**: {top_match_data['caturthī']}"
            else:
                response = f"I don't have pranam information for {top_match_name}."
                
        elif intent == "position":
            if 'position' in top_match_data:
                response = f"**{top_match_name}** is at position {top_match_data['position']} in the Viṣṇu Aṣṭottaraśatanāmam."
            else:
                response = f"I don't have position information for {top_match_name}."
                
        elif intent == "analysis":
            # Comprehensive analysis combining multiple aspects
            analysis = []
            if 'artha' in top_match_data:
                analysis.append(f"\n**Meaning**: {top_match_data['artha']}")
            if 'prakṛyā' in top_match_data:
                analysis.append(f"\n**Etymology**: {top_match_data['prakṛyā']}")
            if 'vigrahavākya' in top_match_data:
                analysis.append(f"\n**Vigrahavākya**: {top_match_data['vigrahavākya']}")
            if 'position' in top_match_data:
                analysis.append(f"\n**Position**: {top_match_data['position']}")
            if 'caturthī' in top_match_data:
                analysis.append(f"\n**Pranam Mantra**: {top_match_data['caturthī']}")
                
            if analysis:
                response = f"**Analysis of {top_match_name}**:\n\n" + "\n\n".join(analysis)
            else:
                response = f"I don't have detailed information for {top_match_name}."
        
        elif intent == "search":
            # Provide basic information and suggest what else they can ask
            response = [f"**{top_match_name}** found in the Viṣṇu Aṣṭottaraśatanāmam."]
            
            # Add brief meaning if available
            if 'artha' in top_match_data:
                meaning = top_match_data['artha']
                # Truncate if very long
                if len(meaning) > 100:
                    meaning = meaning[:97] + "..."
                response.append(f"\n**Meaning**: {meaning}")
            
            # Add position if available
            if 'position' in top_match_data:
                response.append(f"\n**Position**: {top_match_data['position']}")
            
            # Suggest what else they can ask
            response.append("\nYou can ask about:")
            available_info = []
            if 'artha' in top_match_data:
                available_info.append("meaning")
            if 'prakṛyā' in top_match_data:
                available_info.append("etymology")
            if 'vigrahavākya' in top_match_data:
                available_info.append("vigrahavākya (word breakdown)")
            if 'caturthī' in top_match_data:
                available_info.append("pranam mantra")
            
            response.append(", ".join(available_info))
            
            response = "\n".join(response)
        
        # Default response if intent handling not specified
        if not response:
            response = f"Found information about **{top_match_name}** (match score: {score:.2f}). What would you like to know about it?"
        
        print(f"DEBUG: Generated response for intent '{intent}' - returning: {response}")
        return response

    def search_by_category(self, category, value=None):
        """
        Search for names based on a category and optional value.
        For example, search all names related to 'creation'.
        """
        results = {}
        
        # Check all names in the dictionary
        for name, data in self.dictionary.items():
            # Search in meaning/artha
            if 'artha' in data:
                if value is None or value.lower() in data['artha'].lower():
                    if category.lower() in data['artha'].lower():
                        results[name] = {
                            'match_field': 'artha',
                            'data': data
                        }
            
            # Search in etymology/prakṛyā
            if 'prakṛyā' in data:
                prakṛyā = data['prakṛyā']
                if isinstance(prakṛyā, dict):  # Handle prakṛyā as dictionary
                    prakṛyā_text = str(prakṛyā)
                else:  # Handle as string
                    prakṛyā_text = prakṛyā
                
                if value is None or value.lower() in prakṛyā_text.lower():
                    if category.lower() in prakṛyā_text.lower():
                        results[name] = {
                            'match_field': 'prakṛyā',
                            'data': data
                        }
            
            # Search in vigrahavākya
            if 'vigrahavākya' in data:
                if value is None or value.lower() in data['vigrahavākya'].lower():
                    if category.lower() in data['vigrahavākya'].lower():
                        results[name] = {
                            'match_field': 'vigrahavākya',
                            'data': data
                        }
        
        return results

    def suggest_related_names(self, name, max_suggestions=5):
        """
        Suggest names related to the given name based on semantic or etymological similarity.
        """
        if not name in self.dictionary:
            # Try to find the name using matching
            matches = self.phonetic_engine.find_matches(name, self.dictionary)
            if matches:
                name = list(matches.keys())[0]
            else:
                return []
        
        # Get the data for the name
        name_data = self.dictionary[name]
        
        # Extract key terms from meaning and etymology
        key_terms = []
        if 'artha' in name_data:
            # Split by common delimiters and extract words
            words = re.findall(r'\b\w+\b', name_data['artha'].lower())
            key_terms.extend([w for w in words if len(w) > 3 and w not in ['that', 'this', 'with', 'from', 'which']])
        
        if 'prakṛyā' in name_data:
            prakṛyā = name_data['prakṛyā']
            if isinstance(prakṛyā, dict):
                prakṛyā_text = str(prakṛyā)
            else:
                prakṛyā_text = prakṛyā
            
            # Extract words from prakṛyā
            words = re.findall(r'\b\w+\b', prakṛyā_text.lower())
            key_terms.extend([w for w in words if len(w) > 3 and w not in ['that', 'this', 'with', 'from', 'which']])
        
        # Find other names that share these key terms
        related_names = {}
        for other_name, data in self.dictionary.items():
            if other_name == name:
                continue  # Skip the original name
            
            match_count = 0
            match_terms = set()
            
            # Check in meaning
            if 'artha' in data:
                for term in key_terms:
                    if term in data['artha'].lower():
                        match_count += 1
                        match_terms.add(term)
            
            # Check in etymology
            if 'prakṛyā' in data:
                prakṛyā = data['prakṛyā']
                if isinstance(prakṛyā, dict):
                    prakṛyā_text = str(prakṛyā)
                else:
                    prakṛyā_text = prakṛyā
                
                for term in key_terms:
                    if term in prakṛyā_text.lower():
                        match_count += 1
                        match_terms.add(term)
            
            if match_count > 0:
                related_names[other_name] = {
                    'score': match_count,
                    'matching_terms': list(match_terms),
                    'data': data
                }
        
        # Sort by match score and return top suggestions
        sorted_related = sorted(related_names.items(), key=lambda x: x[1]['score'], reverse=True)
        return sorted_related[:max_suggestions]
        
    def _search_by_concept(self, concept):
        """
        Backward compatibility method for the Flask interface
        """
        return self.search_by_category(concept)
    
    def search_names_by_concept(self, concept, field=None, limit=10):
        """
        Search for names related to a concept or meaning term by searching through artha, prakṛyā, and vigrahavākya.
        
        Args:
            concept (str): The concept to search for (e.g., "universe", "lotus", "wealth", "cows")
            field (str, optional): Specific field to search in ('artha', 'prakṛyā', or 'vigrahavākya'). If None, search all fields.
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of (name, data, field_matched, matched_term) tuples that match the concept
        """
        # Expand concept to include related synonyms and variations
        concept_synonyms = {
            'cows': ['cow', 'cattle', 'cow herding', 'cowherds', 'bovine'],
            'lotus': ['padma', 'water lily'],
            'wealth': ['prosperity', 'abundance', 'riches'],
            'creation': ['create', 'generating', 'birth', 'origin']
        }
        
        # Get synonyms for the concept, defaulting to the original concept
        search_terms = [concept.lower().strip()]
        if concept.lower() in concept_synonyms:
            search_terms.extend(concept_synonyms[concept.lower()])
        
        results = []
        
        # Search all names in the dictionary
        for name, data in self.dictionary.items():
            # Search in specified field or all fields if field is None
            matched_field = None
            matched_term = None
            
            # Search in meaning/artha
            if (field is None or field == 'artha') and 'artha' in data:
                artha_lower = data['artha'].lower()
                for term in search_terms:
                    if term in artha_lower:
                        matched_field = 'artha'
                        matched_term = term
                        break
            
            # Search in etymology/prakṛyā
            if not matched_field and (field is None or field == 'prakṛyā') and 'prakṛyā' in data:
                prakṛyā = data['prakṛyā']
                # Handle prakṛyā as either string or dictionary
                if isinstance(prakṛyā, dict):
                    prakṛyā_text = str(prakṛyā).lower()
                else:
                    prakṛyā_text = str(prakṛyā).lower()
                
                for term in search_terms:
                    if term in prakṛyā_text:
                        matched_field = 'prakṛyā'
                        matched_term = term
                        break
            
            # Search in vigrahavākya
            if not matched_field and (field is None or field == 'vigrahavākya') and 'vigrahavākya' in data:
                vigrahavākya_lower = data['vigrahavākya'].lower()
                for term in search_terms:
                    if term in vigrahavākya_lower:
                        matched_field = 'vigrahavākya'
                        matched_term = term
                        break
            
            # If a match was found, add to results
            if matched_field:
                results.append((name, data, matched_field, matched_term))
        
        # Sort results by relevance
        def get_priority(match_tuple):
            _, _, field, matched_term = match_tuple
            # Prioritize exact concept match over synonyms
            base_priority = 3 if matched_term == concept.lower() else 2
            
            if field == 'artha':
                return base_priority + 1
            elif field == 'vigrahavākya':
                return base_priority
            else:  # prakṛyā
                return base_priority - 1
        
        results.sort(key=get_priority, reverse=True)
        
        # Return limited number of results
        return results[:limit]

    def format_concept_search_results(self, results, concept):
        """
        Format the results from search_names_by_concept into a readable response.
        
        Args:
            results (list): List of (name, data, field_matched, matched_term) tuples
            concept (str): The concept that was searched for
            
        Returns:
            str: Formatted response
        """
        if not results:
            return f"I couldn't find any names related to '{concept}' in the Viṣṇu Aṣṭottaraśatanāmam dictionary."
        
        response_lines = [f"## Names related to '{concept}' in the Viṣṇu Aṣṭottaraśatanāmam:\n"]
        
        for name, data, field_matched, matched_term in results:
            # Begin with name and position if available
            position_info = f" (#{data['position']})" if 'position' in data else ""
            response_lines.append(f"**{name}**{position_info}")
            
            # Add the matched field and highlight the matched term
            if field_matched == 'artha':
                # Highlight the matched term in the meaning
                artha = data['artha']
                highlighted_artha = re.sub(r'\b' + re.escape(matched_term) + r'\b', 
                                        f"**{matched_term}**", 
                                        artha, 
                                        flags=re.IGNORECASE)
                response_lines.append(f"**Meaning**: {highlighted_artha}")
            elif field_matched == 'prakṛyā':
                if isinstance(data['prakṛyā'], dict):
                    response_lines.append(f"**Etymology**: (Complex etymology with multiple components)")
                else:
                    # Highlight the matched term in etymology
                    prakṛyā = str(data['prakṛyā'])
                    highlighted_prakṛyā = re.sub(r'\b' + re.escape(matched_term) + r'\b', 
                                                f"**{matched_term}**", 
                                                prakṛyā, 
                                                flags=re.IGNORECASE)
                    response_lines.append(f"**Etymology**: {highlighted_prakṛyā}")
            elif field_matched == 'vigrahavākya':
                # Highlight the matched term in vigrahavākya
                vigrahavākya = data['vigrahavākya']
                highlighted_vigrahavākya = re.sub(r'\b' + re.escape(matched_term) + r'\b', 
                                                f"**{matched_term}**", 
                                                vigrahavākya, 
                                                flags=re.IGNORECASE)
                response_lines.append(f"**Vigrahavākya**: {highlighted_vigrahavākya}")
            
            response_lines.append("") # Add empty line between entries
        
        return "\n".join(response_lines)
