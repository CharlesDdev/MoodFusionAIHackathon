import os
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import secretmanager

from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
import random
import logging

# Configure logging to ensure messages appear in Cloud Run logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'moodfusion-hackathon')
REGION = os.environ.get('GCP_REGION', 'us-central1')

# --- Secret Manager Client ---
secret_manager_client = secretmanager.SecretManagerServiceClient()

# --- Helper Function to Get Secrets ---
def get_secret(secret_name):
    """Fetches a secret from Secret Manager."""
    try:
        resource_name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_manager_client.access_secret_version(request={"name": resource_name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret '{secret_name}': {e}")
        raise

# --- Global variables for API keys (fetched once on startup) ---
try:
    SPOONACULAR_API_KEY = get_secret('spoonacular_api_key')
    logger.info("Spoonacular API Key loaded.")
except Exception as e:
    logger.critical("Failed to load Spoonacular API key. Exiting.")
    exit(1)

# --- Vertex AI (Gemini) Client ---
aiplatform.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel('gemini-2.0-flash')


# --- Meal Recommendation Logic (Core of the Agent) ---
def get_meal_recommendation(mood: str, meal_context: str): # MODIFIED: Accepts meal_context
    """
    Recommends a meal based on the user's mood and time of day using Spoonacular and Gemini.
    """
    logger.info(f"Entering get_meal_recommendation for mood: '{mood}', context: '{meal_context}'")

    # --- NEW: Dynamic Gemini Prompt and Spoonacular Type based on meal_context ---
    prompt_meal_type_description = ""
    spoonacular_meal_type_filter = ""
    
    # Adjust prompt wording and Spoonacular filter based on context
    if meal_context == "breakfast":
        prompt_meal_type_description = "a delicious **breakfast or brunch** meal"
        spoonacular_meal_type_filter = "breakfast"
    elif meal_context == "lunch":
        prompt_meal_type_description = "a satisfying **lunch** meal"
        spoonacular_meal_type_filter = "lunch" # Specific Spoonacular type for lunch
    elif meal_context == "dinner":
        prompt_meal_type_description = "a hearty **dinner** meal"
        spoonacular_meal_type_filter = "main course" # 'main course' is good for dinner
    else: # Default or 'general' context
        prompt_meal_type_description = "a satisfying **meal (breakfast, lunch, or dinner)**"
        # For general, allow Spoonacular to search across common meal types for flexibility
        spoonacular_meal_type_filter = "main course,breakfast,lunch,appetizer,salad,soup" # Broader types for general context

    gemini_prompt = f"""
The user is feeling: "{mood}".
Your task is to suggest 3-5 distinct food-related keywords that would perfectly match this mood for {prompt_meal_type_description}.

**STRICTLY AVOID** suggesting any:
- Desserts (e.g., cake, cookie, pie, ice cream, tart, sweet pastries)
- Sweet-only snacks (e.g., fruit by itself, nuts, plain yogurt, smoothies if primarily sweet)
- Drinks (e.g., coffee, tea, juice)

Keywords can include:
- Cuisine types (e.g., "Italian", "Mexican", "Thai", "Mediterranean")
- Meal categories specific to the context (e.g., "omelette", "pancakes", "sandwich", "soup", "stir-fry", "roast", "casserole", "curry", "burrito", "toast", "pasta", "pizza", "waffles")
- Main protein/vegetable (e.g., "chicken", "beef", "fish", "pork", "lentil", "tofu", "vegetable medley")
- Preparation styles (e.g., "grilled", "baked", "braised", "quick", "easy")

Examples of keywords for different moods and meal types:
- If mood is "cozy" and meal type is "breakfast", keywords: "warm oatmeal", "breakfast casserole", "fluffy pancakes".
- If mood is "energetic" and meal type is "lunch", keywords: "grilled chicken salad", "lean protein bowl", "fresh wrap".
- If mood is "romantic" and meal type is "dinner", keywords: "elegant steak", "seafood pasta", "wine pairing meal".
- If mood is "happy" and meal type is "breakfast", keywords: "pancakes with berries", "breakfast burrito", "omelette".
- If mood is "happy" and meal type is "dinner", keywords: "celebratory feast", "pizza night", "BBQ ribs".
- If mood is "tired" and meal type is "any", keywords: "easy one-pan meal", "quick pasta", "simple chicken", "soup and sandwich".

Return the keywords as a comma-separated list.
"""
    logger.info(f"Gemini prompt constructed for mood '{mood}', context '{meal_context}'.")

    inferred_keywords = ""
    try:
        gemini_response = model.generate_content(gemini_prompt)
        if gemini_response.candidates and gemini_response.candidates[0].content.parts:
            inferred_keywords = gemini_response.candidates[0].content.parts[0].text.strip()
            logger.info(f"Gemini inferred meal keywords for '{mood}' ({meal_context}): {inferred_keywords}")
        else:
            logger.warning(f"Gemini returned no content for mood '{mood}' ({meal_context}). Response: {gemini_response}")

        meal_keywords = [k.strip() for k in inferred_keywords.split(',') if k.strip()]
        logger.info(f"Processed meal_keywords: {meal_keywords}")
        
        if not meal_keywords:
            logger.warning("Gemini inferred no keywords. Falling back to default 'comfort food'.")
            meal_keywords = ["comfort food"]

    except Exception as e:
        logger.error(f"Error using Gemini for meal inference: {e}. Falling back to default 'comfort food'.")
        meal_keywords = ["comfort food"]

    # Step 2: Search Spoonacular using inferred keywords
    spoonacular_url = "https://api.spoonacular.com/recipes/complexSearch"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": meal_keywords[0] if meal_keywords else "food",
        "number": 5, # Get a few options to randomly pick from
        "addRecipeInformation": True,
        "instructionsRequired": True,
        "minCalories": 250, # Adjusted min calories to allow for lighter breakfast/lunch options
        "maxReadyTime": 90,
        "type": spoonacular_meal_type_filter, # MODIFIED: Use dynamically determined type
        "sort": "random",
        "excludeIngredients": "muffin, pastry, cookie, cake, ice cream, donut, sweet, honey, chocolate, tart, dessert, pie, brownie"
    }
    logger.info(f"Spoonacular API call parameters: {params}")

    try:
        response = requests.get(spoonacular_url, params=params)
        response.raise_for_status()
        data = response.json()
        recipes = data.get("results", [])
        logger.info(f"Spoonacular returned {len(recipes)} recipes for keywords: {meal_keywords}, type: {spoonacular_meal_type_filter}")

        if not recipes:
            logger.warning(f"No recipes found for keywords: {meal_keywords}, type: {spoonacular_meal_type_filter}. Trying popular food fallback.")
            params_fallback = {
                "apiKey": SPOONACULAR_API_KEY,
                "query": "popular food",
                "number": 5,
                "addRecipeInformation": True,
                "instructionsRequired": True,
                "type": "main course,breakfast,lunch", # Broader fallback type
                "sort": "random"
            }
            response_fallback = requests.get(spoonacular_url, params=params_fallback)
            response_fallback.raise_for_status()
            data_fallback = response_fallback.json()
            recipes = data_fallback.get("results", [])
            
            if not recipes:
                raise ValueError("Could not find any recipes with fallback.")

        # Step 3: Pick a meal and get details
        selected_meal = random.choice(recipes) if recipes else None

        if not selected_meal:
            raise ValueError("No meal could be selected after Spoonacular search.")

        meal_title = selected_meal.get("title")
        meal_image_url = selected_meal.get("image")
        meal_source_url = selected_meal.get("sourceUrl")

        meal_description = selected_meal.get("summary") or selected_meal.get("instructions", "No detailed instructions available, please visit the source URL.")

        logger.info(f"Selected Meal: {meal_title}, Image: {meal_image_url}")
        return {
            "mealTitle": meal_title,
            "mealImageUrl": meal_image_url,
            "mealDescription": meal_description,
            "mealSourceUrl": meal_source_url
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Spoonacular API: {e}")
        if response.status_code == 402:
            raise Exception("Spoonacular API Daily Limit Reached or Plan Expired.")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_meal_recommendation: {e}")
        raise

# --- Flask Route ---
@app.route('/recommend_meal', methods=['POST'])
def recommend_meal():
    """
    HTTP endpoint for the Meal Agent.
    Expects a JSON payload with 'mood' and optionally 'mealContext'.
    """
    try:
        data = request.get_json()
        mood = data.get('mood')
        meal_context = data.get('mealContext', 'general') # NEW: Get mealContext, default to 'general'

        if not mood:
            logger.warning("Missing 'mood' in request body")
            return jsonify({"error": "Missing 'mood' in request body"}), 400

        logger.info(f"Received request for mood: {mood}, mealContext: {meal_context} in meal agent")
        meal_recommendation = get_meal_recommendation(mood, meal_context) # MODIFIED: Pass meal_context
        return jsonify(meal_recommendation), 200

    except Exception as e:
        logger.error(f"Unhandled error in recommend_meal endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# --- Entry Point for Cloud Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
