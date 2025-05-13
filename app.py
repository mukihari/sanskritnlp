"""
Flask Web Interface for the Vishnu Sahasranama Nirukti Project
"""
 
from flask import Flask, render_template, request, jsonify
import traceback
import os
import logging

# Import the Sanskrit NLP module
from nlp_engine import SanskritNLP
from dictionary_108 import vishnu_ashtottaram

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize the Flask app
app = Flask(__name__)

# Initialize the Sanskrit NLP system
sanskrit_nlp = SanskritNLP(vishnu_ashtottaram)

@app.route('/')
def home():
    """Render the home page with the chat interface"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def process_query():
    """Process a query and return the response"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Log the query for debugging
        logger.info(f"Processing query: {query}")
        
        # Process the query with the Sanskrit NLP system
        response = sanskrit_nlp.process_query(query)
        
        # Log the response
        logger.info(f"Response: {response}")
        
        # Return the response and context
        return jsonify({
            'response': response,
            'context': sanskrit_nlp.context
        })
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/list_names')
def list_names():
    """List all names in the dictionary"""
    try:
        names = list(vishnu_ashtottaram.keys())
        names.sort()
        return jsonify({'names': names})
    except Exception as e:
        error_msg = f"Error listing names: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/name_details/<name>')
def name_details(name):
    """Get details for a specific name"""
    try:
        # First try an exact match
        if name in vishnu_ashtottaram:
            return jsonify({'name': name, 'details': vishnu_ashtottaram[name]})
        
        # If no exact match, try the phonetic engine
        engine = sanskrit_nlp.phonetic_engine
        matches = engine.find_matches(name, vishnu_ashtottaram)
        
        if matches:
            # Return the best match
            best_match = max(matches.items(), key=lambda x: x[1]['score'])[0]
            return jsonify({
                'name': best_match, 
                'details': vishnu_ashtottaram[best_match],
                'match_score': matches[best_match]['score']
            })
        
        return jsonify({'error': 'Name not found'}), 404
    except Exception as e:
        error_msg = f"Error getting name details: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/search_concept/<concept>')
def search_concept(concept):
    """Search for names related to a concept"""
    try:
        # Use the NLP system to search by category
        results = sanskrit_nlp.search_by_category(concept)
        
        # Format the results
        formatted_results = {}
        for name, data in results.items():
            formatted_results[name] = {
                'match_field': data.get('match_field', ''),
                'data': {
                    'artha': data.get('data', {}).get('artha', ''),
                    'position': data.get('data', {}).get('position', '')
                }
            }
        
        return jsonify({'results': formatted_results})
    except Exception as e:
        error_msg = f"Error searching concept: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/analyze_query', methods=['POST'])
def analyze_query():
    """
    Analyze a query to show how the NLP system processes it
    (useful for development and debugging)
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Analyze the query
        intent = sanskrit_nlp.detect_intent(query)
        name = sanskrit_nlp.extract_name_from_query(query, intent)
        
        # Find matches for the extracted name
        matches = {}
        if name:
            matches = sanskrit_nlp.phonetic_engine.find_matches(name, vishnu_ashtottaram)
        
        # Format the analysis
        analysis = {
            'query': query,
            'intent': intent,
            'extracted_name': name,
            'matches': {}
        }
        
        # Format the matches
        for match_name, match_data in matches.items():
            analysis['matches'][match_name] = match_data['score']
        
        return jsonify(analysis)
    except Exception as e:
        error_msg = f"Error analyzing query: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/reset_context', methods=['POST'])
def reset_context():
    """Reset the conversation context"""
    try:
        sanskrit_nlp.context = {
            "last_name": None,
            "last_intent": None,
            "name_in_query": None,
            "last_response": None,
            "partial_query": None
        }
        return jsonify({'message': 'Context reset successfully'})
    except Exception as e:
        error_msg = f"Error resetting context: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Start the Flask app
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, host='0.0.0.0', port=port)