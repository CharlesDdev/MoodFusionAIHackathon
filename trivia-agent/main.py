import os
import requests # Though not directly used for external APIs yet, good to include if needed later
from flask import Flask, request, jsonify
from flask_cors import CORS

from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
# GCP Project ID
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'moodfusion-hackathon')
REGION = os.environ.get('GCP_REGION', 'us-central1')

# --- Vertex AI (Gemini) Client ---
aiplatform.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel('gemini-2.0-flash')

# --- Trivia Generation Logic ---
def generate_trivia(meal_data=None, movie_data=None):
    """
    Generates a trivia fact based on meal and/or movie data using Gemini.
    """
    prompt_parts = []
    
    if meal_data:
        meal_title = meal_data.get('mealTitle', 'a meal')
        meal_description = meal_data.get('mealDescription', '')
        prompt_parts.append(f"Regarding the meal '{meal_title}' which is described as: {meal_description}")
        
    if movie_data:
        movie_title = movie_data.get('movieTitle', 'a movie')
        movie_description = movie_data.get('movieDescription', '')
        prompt_parts.append(f"Regarding the movie '{movie_title}' which is described as: {movie_description}")

    if not prompt_parts:
        return "No specific meal or movie provided for trivia."

    # Constructing the prompt for Gemini
    full_prompt = (
        "Generate one interesting, short, and surprising trivia fact based on the following information. "
        "The fact should be concise and engaging. Do not start with 'Did you know' or similar phrases. "
        "Keep it to a single sentence, or two very short sentences.\n\n" +
        "\n".join(prompt_parts) +
        "\n\nTrivia Fact:"
    )

    try:
        gemini_response = model.generate_content(full_prompt)
        trivia_fact = gemini_response.candidates[0].content.parts[0].text.strip()
        print(f"Gemini generated trivia: {trivia_fact}")
        return trivia_fact
    except Exception as e:
        print(f"Error generating trivia with Gemini: {e}")
        return "Could not generate trivia fact at this time."

# --- Flask Route ---
@app.route('/get_trivia', methods=['POST'])
def get_trivia_endpoint():
    """
    HTTP endpoint for the Trivia Agent.
    Expects a JSON payload that can optionally contain 'meal' and/or 'movie' objects.
    """
    try:
        data = request.get_json()
        meal = data.get('meal')
        movie = data.get('movie')

        if not meal and not movie:
            return jsonify({"error": "Missing 'meal' or 'movie' data in request body"}), 400

        trivia = generate_trivia(meal_data=meal, movie_data=movie)
        return jsonify({"triviaFact": trivia}), 200

    except Exception as e:
        print(f"Unhandled error in get_trivia endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# --- Entry Point for Cloud Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))