# Cinemunch - Meal and Movie Recommender
## Find Your Perfect Vibe: Curated Meals & Movies for Every Mood!

## Table of Contents
- [Cinemunch - Meal and Movie Recommender](#cinemunch---meal-and-movie-recommender)
  - [Find Your Perfect Vibe: Curated Meals \& Movies for Every Mood!](#find-your-perfect-vibe-curated-meals--movies-for-every-mood)
  - [Table of Contents](#table-of-contents)
  - [Demo](#demo)
  - [Problem Statement](#problem-statement)
  - [Solution](#solution)
  - [Key Features](#key-features)
  - [Technology Stack](#technology-stack)
  - [Architecture](#architecture)
  - [Workflow:](#workflow)
  - [Google Agent Development Kit (ADK) Usage](#google-agent-development-kit-adk-usage)
  - [Setup \& Deployment](#setup--deployment)
  - [Usage](#usage)
  - [Future Enhancements](#future-enhancements)
  - [Challenges \& Learnings](#challenges--learnings)
  - [Attribution](#attribution)
  - [Contact](#contact)

## Demo
(If you have deployed the frontend publicly, insert a link here. Otherwise, judges will follow the "Setup & Deployment" instructions to run it locally.)

* **Live Demo (if applicable):** https://your-public-frontend-url.com

* **Video Demo (if applicable):** [Link to a short video showcasing features]

## Problem Statement

In an age of endless content, deciding "what to eat" and "what to watch" can be overwhelming. Users often seek recommendations that align with their current mood, but generic suggestions fall flat. Existing platforms rarely offer a cohesive, mood-aware pairing of meal and entertainment, leaving users to juggle multiple apps and decision fatigue. This hackathon challenged me to build intelligent, modular agents to solve real-world problems.

## Solution

Cinemunch's Meal & Movie Recommender is an intelligent web application built using the Google Agent Development Kit (ADK). It solves the decision fatigue problem by providing curated meal and movie recommendations based on the user's emotional state and the time of day. Leveraging the power of Generative AI (Gemini API), specialized external APIs (Spoonacular, TMDB), and the scalable microservice architecture facilitated by the ADK, MoodFusion offers personalized pairings, simplifying decision-making and enhancing the user experience.

## Key Features

* **Mood-Based Recommendations:** Get personalized meal and movie suggestions by simply typing or selecting your current mood (e.g., "happy," "cozy," "adventurous").

* **Time-of-Day Aware Meals:** The meal agent intelligently detects the time of day (morning, midday, evening) and tailors meal recommendations accordingly (Breakfast, Lunch, or Dinner).

* **Intelligent Meal Filtering:** Robustly excludes desserts, sweet snacks, and inappropriate meal types (e.g., no muffins for dinner!).

* **Diverse Movie Selections:** The movie agent's recommendations are now highly diversified, avoiding excessive animated/kid-like films for adult-oriented moods, and providing a wider range of genres.

* **Interactive Movie Details (Hover Effect):** Hover over a movie card to instantly reveal key details like release year, runtime, MPAA rating, and TMDB user score, enhancing usability.

* **Quick Mood Dropdown:** A convenient dropdown with pre-defined moods allows for rapid recommendation generation without typing.

* **Dynamic Dark Mode:** Toggle between light and dark themes with a click, and the application remembers your preference across sessions using localStorage.

* **Responsive UI/UX:** A clean, modern interface built with Tailwind CSS ensures optimal viewing and interaction across all devices (desktop, tablet, mobile).

* **Robust Error Handling:** Provides user feedback for empty inputs and handles API errors gracefully.

* **Containerized Microservices:** Backend logic is separated into independent, scalable Cloud Run services (meal-agent, movie-agent), developed using the principles of the ADK.

## Technology Stack
* **`Google Agent Development Kit (ADK)`:** The framework and tools enabling the development of modular, scalable agents.
* **Frontend:**
    * HTML5
    * CSS3 (Tailwind CSS for utility-first styling)
    * JavaScript (ES6+)
    * `Google Fonts` (Inter)
* **Backend (Microservices):**
    * Python 3.9+
    * Flask (Web Framework)
    * Requests (HTTP library)
    * `Google Cloud Secret Manager` (for API key security)
    * `Google Cloud aiplatform` library (for Vertex AI Gemini API)
* **APIs:**
    * **`Gemini API (via Vertex AI GenerativeModel`):** Powers mood-to-keyword/genre inference for both meal and movie agents, core to our ADK agents.
    * **Spoonacular API:** Provides comprehensive meal recipes, images, and details based on food keywords.
    * **TMDB (The Movie Database) API:** Offers movie discovery, posters, overviews, and detailed metadata (year, runtime, ratings).
* **Deployment:**
    * Docker (Containerization)
    * `Google Cloud Run` (Serverless compute for backend agents, ideal for ADK microservices)
    * `Google Cloud Project` (overall management)
* **Version Control:**
    * Git
    * GitHub (Public Remote Repository)

## Architecture
The MoodFusion Recommender follows a client-server architecture with specialized backend microservices, designed with ADK principles:

    graph TD
        UserBrowser[User Browser (Frontend)] -->|HTTP Request| MoodFusionApp[MoodFusion Frontend (index.html, script.js)]
        MoodFusionApp -->|POST /recommend_meal {mood, mealContext}| MealAgent[Meal Agent (Cloud Run)]
        MoodFusionApp -->|POST /recommend_movie {mood}| MovieAgent[Movie Agent (Cloud Run)]

        MealAgent -->|Gemini API Request (mood -> keywords)| Gemini[Vertex AI Gemini API]
        MealAgent -->|Spoonacular API Request (keywords, type)| Spoonacular[Spoonacular API]
        Spoonacular -->|Meal Data| MealAgent
        Gemini -->|Keywords| MealAgent
        MealAgent -->|JSON Response (Meal Data)| MoodFusionApp

        MovieAgent -->|Gemini API Request (mood -> genres)| Gemini
        MovieAgent -->|TMDB Discover API Request (genres)| TMDBDiscover[TMDB API (Discover)]
        MovieAgent -->|TMDB Details API Request (movie_id)| TMDBDetails[TMDB API (Details)]
        TMDBDiscover -->|Movie List| MovieAgent
        TMDBDetails -->|Detailed Movie Data| MovieAgent
        Gemini -->|Genres| MovieAgent
        MovieAgent -->|JSON Response (Movie Data)| MoodFusionApp

        subgraph Google Cloud Project
            MealAgent -- Managed Service --> CloudRun[Cloud Run]
            MovieAgent -- Managed Service --> CloudRun
            Gemini -- API Access --> VertexAI[Vertex AI]
            SecretManager[Secret Manager] -->|API Keys| MealAgent
            SecretManager -->|API Keys| MovieAgent
        end

## Workflow:
1. The user enters a mood in the frontend.

2. The frontend determines the current time of day for meal context.

3. Simultaneously, two asynchronous API calls are made from the frontend to the deployed Cloud Run agents: meal-agent and movie-agent.

4. **Meal Agent (Built with ADK Principles):**
    * Receives mood and mealContext.
    * Uses Gemini to infer food keywords matching the mood and meal context.
    * Calls Spoonacular API with these keywords and a meal type filter, ensuring no desserts.
    * Selects a random recipe and returns its title, image, description, and source URL.

5. **Movie Agent (Built with ADK Principles):**
    * Receives mood.
    * Uses Gemini to infer movie genres matching the mood, explicitly avoiding animated/family genres for general moods.
    * Calls TMDB Discover API to find movies by genre.  
    * Makes a second TMDB API call to fetch detailed information (year, runtime, ratings) for the selected movie.
    * Returns movie title, poster URL, description, source URL, and detailed info.

6. The frontend receives responses from both agents and dynamically updates the UI to display the meal and movie recommendations.

## Google Agent Development Kit (ADK) Usage
The Google Agent Development Kit (ADK) provided the foundational tools and architectural patterns that significantly streamlined the development of our MoodFusion Recommender.

* **How ADK was utilized:**
    * **Modular Agent Design:**The ADK encouraged the creation of distinct, independent agents (meal-agent and movie-agent). This modularity makes the system highly scalable, maintainable, and allows for individual agent updates or expansions without affecting the entire application.

    * **Generative AI Integration:** The ADK provided the framework and best practices for integrating the Gemini API (via Vertex AI GenerativeModel) into our agents. This allowed us to quickly implement sophisticated mood-to-keyword/genre inference directly within our Python services.

    * **Scalable Deployment:** The ADK's emphasis on containerization (Docker) and serverless deployment (Google Cloud Run) was pivotal. This enabled us to deploy our agents as highly scalable, cost-effective microservices that can handle varying loads without manual infrastructure management.

    * **Secure Credential Management:** The recommended use of Google Secret Manager within the ADK ecosystem ensured that our API keys were securely stored and accessed by our agents, a crucial security best practice.

    * **Rapid Prototyping & Iteration:** The ADK's streamlined approach allowed for rapid development and iterative improvements, enabling us to quickly experiment with prompt engineering and API integrations to achieve precise recommendation quality.

## Setup & Deployment
Follow these steps to set up and deploy your MoodFusion Recommender.

**Prerequisites**
1. **`Google Cloud` Project:**

    * Create a new Google Cloud Project or use an existing one.
    * Enable the following APIs:

        * Cloud Run API
        * Secret Manager API
        * Vertex AI API

    * Set up billing for the project.

2. **`Google Cloud SDK`:** Install and initialize the `gcloud` CLI tool on your local machine.

    * `gcloud init`
    * `gcloud auth login`
    * `gcloud config set project [YOUR_PROJECT_ID]`

3. **Docker:** Install Docker Desktop (or Docker Engine) on your local machine.

4. **Git:** Install Git.

5. **API Keys:**
    * **Spoonacular API Key:** Get one from Spoonacular.com.

    * **TMDB API Key:** Get one from TheMovieDB.org/settings/api.

**Google Cloud Setup**
1. **Create Secrets in Secret Manager:**
    * Store your Spoonacular API key:
  
    * echo "YOUR_SPOONACULAR_API_KEY" | gcloud secrets create spoonacular_api_key --data-file=- --project=[YOUR_PROJECT_ID]

    * Store your TMDB API key:
  
    * echo "YOUR_TMDB_API_KEY" | gcloud secrets create tmdb_api_key --data-file=- --project=[YOUR_PROJECT_ID]

    * Grant your Cloud Run service accounts access to these secrets. For each secret:
  
    * gcloud secrets add-iam-policy-binding spoonacular_api_key \
    --member="serviceAccount:[YOUR_PROJECT_NUMBER]-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project=[YOUR_PROJECT_ID]

    * gcloud secrets add-iam-policy-binding tmdb_api_key \
    --member="serviceAccount:[YOUR_PROJECT_NUMBER]-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" --project=[YOUR_PROJECT_ID]```

    * (Replace [YOUR_PROJECT_NUMBER] with your actual Google Cloud Project Number, found in your GCP console dashboard).

**Agent Deployment (Backend)**
Navigate to your project's root directory in your terminal.
1. **Deploy the** meal-agent:
* Navigate to the meal-agent directory:

cd meal-agent

* Build the Docker image:

docker build --platform linux/amd64 -t gcr.io/[YOUR_PROJECT_ID]/meal-agent:latest .

* Push the image to Google Container Registry:

docker push gcr.io/[YOUR_PROJECT_ID]/meal-agent:latest

* Deploy to Cloud Run:

gcloud run deploy meal-agent --image gcr.io/[YOUR_PROJECT_ID]/meal-agent:latest \
    --platform managed --region us-central1 --allow-unauthenticated \
    --set-env-vars GCP_PROJECT_ID=[YOUR_PROJECT_ID]

* **IMPORTANT:** Note down the URL provided after successful deployment. This will be your MEAL_AGENT_URL.

* Navigate back to the project root:

cd ..

2. **Deploy the** movie-agent:

Navigate to the movie-agent directory:

cd movie-agent

Build the Docker image:

docker build --platform linux/amd64 -t gcr.io/[YOUR_PROJECT_ID]/movie-agent:latest .

Push the image to Google Container Registry:

docker push gcr.io/[YOUR_PROJECT_ID]/movie-agent:latest

Deploy to Cloud Run:

gcloud run deploy movie-agent --image gcr.io/[YOUR_PROJECT_ID]/movie-agent:latest \
    --platform managed --region us-central1 --allow-unauthenticated \
    --set-env-vars GCP_PROJECT_ID=[YOUR_PROJECT_ID]

* **IMPORTANT:** Note down the URL provided after successful deployment. This will be your MOVIE_AGENT_URL.

Navigate back to the project root:

cd ..

**Frontend Setup**
    * **Update** frontend/script.js:

    * Open frontend/script.js.

    * Replace https://meal-agent-702694291445.us-central1.run.app/recommend_meal with your actual MEAL_AGENT_URL.

    * Replace https://movie-agent-702694291445.us-central1.run.app/recommend_movie with your actual MOVIE_AGENT_URL.

    * Save frontend/script.js.

**Run Locally (or Deploy to Static Hosting):**
Open frontend/index.html directly in your web browser. All interactions will be handled by your deployed Cloud Run agents.

## Usage
1. **Enter your Mood:** Type how you're feeling into the text input box (e.g., "happy," "tired," "adventurous").

2. **Use Quick Mood:** Alternatively, select a pre-defined mood from the dropdown for rapid recommendation generation.

3. **Get Recommendations:** Click the "Get Recommendations" button (or select from the dropdown) to receive a paired meal and movie.

4. **Explore Meal Details:** View the meal title, image, description, and click "View Full Recipe" to go to the Spoonacular source.

5. **Explore Movie Details:** View the movie title, poster, and description. Hover over the movie card to reveal additional details like year, runtime, MPAA rating, and TMDB user score. Click "View on TMDB" for more info.

6. **Switch Themes:** Use the "Light" and "Dark" buttons to toggle the application's theme. Your preference will be saved.

## Future Enhancements
* **Mobile Application (Flutter):** Port the frontend to a native mobile application using Flutter, enabling use on phones and tablets, leveraging the existing backend microservices.

* **Refined Movie Genre Inference:** Further enhance the movie agent's Gemini prompt and/or implement post-processing to completely eliminate animated/kid-focused content for non-child-specific moods, ensuring more precise adult/teenager-oriented recommendations.

* **User Accounts & Favorites:** Allow users to save their favorite meal/movie pairings.
* **Recommendation History:** Keep a log of past recommendations.
* **More Recommendation Categories:** Integrate music, books, activities, or games.
* **Refined Filtering:** Add more explicit filters (e.g., "vegetarian meal," "action movie only").
* **Advanced Mood Analysis:** Utilize more sophisticated NLP for deeper mood understanding.
* **User Feedback Loop:** Allow users to rate recommendations, improving future suggestions.
* **Custom Modals for Alerts:** Replace native alert() with custom UI for better styling.

## Challenges & Learnings
* **Leveraging the ADK:** Understanding how to effectively build, containerize, and deploy modular agents on Cloud Run to achieve scalable and independent services.

* **Debugging Distributed Systems:** Identifying issues across frontend JavaScript, Flask agents, and external APIs required extensive use of browser developer tools (Console, Network tab) and Cloud Run logging.

* **Docker Caching:** Overcoming issues where Dockerfile changes weren't picked up required implementing explicit cache-busting mechanisms (ARG CACHE_BREAKER_COPY).

* **Frontend-Backend Data Mismatch:** Resolving subtle mismatches in JSON key names (movieImageUrl vs moviePosterUrl) was crucial for displaying content correctly.

* **Prompt Engineering for Specificity:** Iteratively refining Gemini prompts with strong positive and negative constraints was key to achieving desired meal types (e.g., preventing desserts) and movie genres (e.g., reducing animated bias).

* **DOM Manipulation & Styling:** Ensuring JavaScript correctly interacted with dynamically styled HTML elements (especially with CSS variables for theming) required careful sequencing with DOMContentLoaded.

* **Third-Party API Nuances:** Learning how to effectively query Spoonacular (e.g., type parameter) and TMDB (e.g., secondary call for detailed movie data, release_dates for certification) for optimal results.

## Attribution
* **Agent Development Kit:** Google ADK

* **Large Language Model:** Gemini API (via Google Cloud Vertex AI)

* **Meal Data:** Spoonacular API

* **Movie Data:** The Movie Database (TMDB) API

* **Styling Framework:** Tailwind CSS

* **Font:** `Google Fonts` - Inter

## Contact
Team Cinemunch
[Your GitHub Profile Link (Optional)]
[Your LinkedIn Profile Link (Optional)]
[Your Email (Optional)]