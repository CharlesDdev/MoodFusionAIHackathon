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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'moodfusion-hackathon')
REGION = os.environ.get('GCP_REGION', 'us-central1')
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500/" # Base URL for TMDB movie posters

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
    TMDB_API_KEY = get_secret('tmdb_api_key')
    logger.info("TMDB API Key loaded.")
except Exception as e:
    logger.critical("Failed to load TMDB API key. Exiting.")
    exit(1)

# --- TMDB Genre Mapping ---
# Fetch TMDB movie genres once on startup
TMDB_GENRES = {}
try:
    genre_list_url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    response = requests.get(genre_list_url)
    response.raise_for_status()
    genres_data = response.json().get('genres', [])
    for genre in genres_data:
        TMDB_GENRES[genre['name'].lower()] = genre['id']
    logger.info("TMDB Genres loaded: %s", TMDB_GENRES)
except Exception as e:
    logger.error(f"Error fetching TMDB genres: {e}. Movie recommendations might be less accurate.")
    TMDB_GENRES = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "science fiction": 878,
        "tv movie": 10770, "thriller": 53, "war": 10752, "western": 37,
        "animation": 16, "documentary": 99, "family": 10751, "music": 10402
    }

# --- Vertex AI (Gemini) Client ---
aiplatform.init(project=PROJECT_ID, location=REGION)
model = GenerativeModel('gemini-2.0-flash')

# --- Movie Recommendation Logic (Core of the Agent) ---
def get_movie_recommendation(mood: str):
    """
    Recommends a movie based on the user's mood using TMDB and Gemini.
    Handles internal errors and raises specific exceptions if necessary.
    """
    logger.info(f"Entering get_movie_recommendation for mood: '{mood}'")

    # --- Step 1: Use Gemini to infer TMDB genre names from the mood ---
    available_genres = list(TMDB_GENRES.keys())
    gemini_prompt = f"""
    The user is feeling: "{mood}".
    Suggest 3-5 distinct TMDB movie genre names that would perfectly match this mood.
    Do not suggest specific movies, actors, or genre IDs.
    Choose ONLY from the following common TMDB genres: {', '.join(sorted(available_genres))}.
    If a mood doesn't directly map to a genre, pick the closest fitting ones.
    Examples:
    - If mood is "sad", genres could be "Drama", "Family", "Music".
    - If mood is "adventurous", genres could be "Action", "Adventure", "Fantasy".
    - If mood is "cozy and thoughtful", genres could be "Drama", "Family", "Comedy", "Romance", "Animation".
    Return the genre names as a comma-separated list.
    """
    inferred_genre_names = ""
    genre_ids = []
    try:
        gemini_response = model.generate_content(gemini_prompt)
        if gemini_response.candidates and gemini_response.candidates[0].content.parts:
            inferred_genre_names = gemini_response.candidates[0].content.parts[0].text.strip()
            logger.info(f"Gemini inferred genre names for '{mood}': {inferred_genre_names}")
        else:
            logger.warning(f"Gemini returned no content for mood '{mood}'. Response: {gemini_response}")

        for genre_name in [g.strip().lower() for g in inferred_genre_names.split(',')]:
            if genre_name in TMDB_GENRES:
                genre_ids.append(str(TMDB_GENRES[genre_name]))
            else:
                logger.warning(f"Inferred genre '{genre_name}' not found in TMDB_GENRES. Skipping.")

        if not genre_ids:
            logger.warning("No valid TMDB genre IDs inferred by Gemini. Falling back to default genres (Drama).")
            genre_ids = [str(TMDB_GENRES.get("drama", 18))]

    except Exception as e:
        logger.error(f"Error using Gemini for mood inference: {e}. Falling back to default genres (Drama).")
        genre_ids = [str(TMDB_GENRES.get("drama", 18))]

    logger.info(f"Using TMDB genre IDs: {genre_ids}")

    # --- Step 2: Discover movies on TMDB using genre IDs ---
    tmdb_url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "include_adult": False,
        "include_video": False,
        "with_genres": ','.join(genre_ids)
    }

    all_movies = []
    try:
        for page_num in range(1, 4): # Fetch from first 3 pages for more variety
            current_params = params.copy()
            current_params["page"] = page_num
            response = requests.get(tmdb_url, params=current_params)
            response.raise_for_status()
            data = response.json()
            all_movies.extend(data.get("results", []))
            if data.get("total_pages") and page_num >= data.get("total_pages"):
                break
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching movies from TMDB: {e}")
        all_movies = []

    movies = all_movies
    logger.info(f"TMDB search returned {len(movies)} movies across multiple pages for genres: {genre_ids}")

    if not movies:
        logger.warning(f"No movies found for inferred genres: {genre_ids} across multiple pages. Trying popular movies as a last resort.")
        params_fallback_popular = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "include_adult": False,
            "include_video": False,
            "page": 1
        }
        try:
            response_fallback_popular = requests.get("https://api.themoviedb.org/3/discover/movie", params=params_fallback_popular)
            response_fallback_popular.raise_for_status()
            data_fallback_popular = response_fallback_popular.json()
            movies = data_fallback_popular.get("results", [])
            logger.info(f"Fallback popular search returned {len(movies)} movies.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during popular movies fallback: {e}")
            movies = []

        if not movies:
            raise ValueError("Could not find any movies with discover or popular fallback.")

    # --- Step 3: Pick a movie and get details ---
    selected_movie = random.choice(movies) if movies else None

    if not selected_movie:
        raise ValueError("No movie could be selected after TMDB search or fallback.")

    movie_title = selected_movie.get("title")
    poster_path = selected_movie.get("poster_path")
    overview = selected_movie.get("overview")
    movie_id = selected_movie.get("id") # Get the movie ID for detailed lookup - THIS WAS MISPLACED BEFORE!

    # NEW: Fetch additional movie details using the /movie/{movie_id} endpoint
    release_year = "N/A"
    runtime = "N/A"
    vote_average = "N/A"
    certification = "N/A" # MPAA Rating

    if movie_id: # Only attempt detail fetch if movie_id is available
        movie_details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        details_params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "append_to_response": "release_dates" # To get certification info
        }
        try:
            details_response = requests.get(movie_details_url, params=details_params)
            details_response.raise_for_status()
            movie_details = details_response.json()
            
            # Extracting details
            release_date_full = movie_details.get("release_date")
            if release_date_full:
                release_year = release_date_full.split('-')[0] # Get just the year

            runtime_minutes = movie_details.get("runtime")
            if runtime_minutes is not None: # Check for None explicitly
                hours = runtime_minutes // 60
                minutes = runtime_minutes % 60
                runtime = f"{hours}h {minutes}min"
            
            vote_avg = movie_details.get("vote_average")
            if vote_avg is not None: # Check for None explicitly
                vote_average = f"{vote_avg:.1f}/10" # Format to one decimal place

            # Extracting certification (MPAA rating) from release_dates
            release_dates_data = movie_details.get("release_dates", {}).get("results", [])
            for rd in release_dates_data:
                if rd.get("iso_3166_1") == "US": # Look for US certification
                    for c in rd.get("release_dates", []):
                        if c.get("certification"):
                            certification = c.get("certification")
                            break # Found certification, break inner loop
                if certification != "N/A": # If US certification found, break outer loop
                    break
            
            logger.info(f"Fetched movie details: Year={release_year}, Runtime={runtime}, Vote={vote_average}, Cert={certification}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching detailed movie info for ID {movie_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing detailed movie info for ID {movie_id}: {e}")

    movie_poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else "https://via.placeholder.com/300x450"
    movie_description = overview
    movie_source_url = f"https://www.themoviedb.org/movie/{movie_id}" # Ensure this uses movie_id from the detailed fetch

    logger.info(f"Selected Movie: {movie_title}, Poster URL: {movie_poster_url}")
    return {
        "movieTitle": movie_title,
        "moviePosterUrl": movie_poster_url,
        "movieDescription": movie_description,
        "movieSourceUrl": movie_source_url,
        "movieYear": release_year,        # NEW
        "movieRuntime": runtime,          # NEW
        "movieRating": certification,     # NEW (MPAA rating)
        "movieVoteAverage": vote_average  # NEW (TMDB user score)
    }

# --- Flask Route ---
@app.route('/recommend_movie', methods=['POST'])
def recommend_movie():
    """
    HTTP endpoint for the Movie Agent.
    Expects a JSON payload with 'mood'.
    """
    try:
        data = request.get_json()
        mood = data.get('mood')

        if not mood:
            logger.warning("Missing 'mood' in request body in movie agent")
            return jsonify({"error": "Missing 'mood' in request body"}), 400

        logger.info(f"Received request for mood: {mood} in movie agent")
        movie_recommendation = get_movie_recommendation(mood) # Call the core logic
        logger.info(f"DEBUG MOVIE_AGENT_RESPONSE: {json.dumps(movie_recommendation, indent=2)}")
        return jsonify(movie_recommendation), 200

    except Exception as e:
        logger.error(f"Unhandled error in recommend_movie endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# --- Entry Point for Cloud Run ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
