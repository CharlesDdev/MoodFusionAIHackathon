// Define API endpoints globally - these can be outside DOMContentLoaded
const MEAL_AGENT_URL = 'https://meal-agent-702694291445.us-central1.run.app/recommend_meal';
const MOVIE_AGENT_URL = 'https://movie-agent-702694291445.us-central1.run.app/recommend_movie';

const hoverMovieTitleElem = document.getElementById('hoverMovieTitle');
const hoverMovieYearElem = document.getElementById('hoverMovieYear');
const hoverMovieRuntimeElem = document.getElementById('hoverMovieRuntime');
const hoverMovieRatingElem = document.getElementById('hoverMovieRating');
const hoverMovieVoteAverageElem = document.getElementById('hoverMovieVoteAverage');// Ensure all DOM-dependent code runs after the DOM is fully loaded

document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const moodInput = document.getElementById('moodInput');
    const getRecommendationsBtn = document.getElementById('getRecommendationsBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const buttonText = document.getElementById('buttonText');
    const quickMoodSelect = document.getElementById('quickMoodSelect'); // NEW: Reference to the dropdown
    
    const mealResultDiv = document.getElementById('mealResultDiv');
    const mealTitleElem = document.getElementById('mealTitle');
    const mealImageElem = document.getElementById('mealImage');
    const mealDescriptionElem = document.getElementById('mealDescription');
    const mealSourceUrlElem = document.getElementById('mealSourceUrl');

    const movieResultDiv = document.getElementById('movieResultDiv');
    const movieTitleElem = document.getElementById('movieTitle');
    const movieImageElem = document.getElementById('movieImage');
    const movieDescriptionElem = document.getElementById('movieDescription');
    const movieSourceUrlElem = document.getElementById('movieSourceUrl');

    // --- Event Listener for the Main Button ---
    getRecommendationsBtn.addEventListener('click', async () => {
        const mood = moodInput.value.trim();
        if (!mood) {
            alert('Please enter your mood!'); 
            return;
        }

        hideAllResults();
        showLoading();

        const mealContext = getMealContext();
        console.log("Determined meal context:", mealContext);

        try {
            const [mealResponse, movieResponse] = await Promise.allSettled([
                fetchRecommendation(MEAL_AGENT_URL, mood, mealContext), 
                MOVIE_AGENT_URL !== 'YOUR_MOVIE_AGENT_CLOUD_RUN_URL/recommend_movie' ? fetchRecommendation(MOVIE_AGENT_URL, mood) : Promise.resolve(null)
            ]);

            hideLoading();

            if (mealResponse.status === 'fulfilled' && mealResponse.value) {
                displayMealRecommendation(mealResponse.value);
            } else {
                console.error('Meal recommendation failed:', mealResponse.reason);
                alert('Failed to get meal recommendation. Please try again.');
            }

            if (movieResponse.status === 'fulfilled' && movieResponse.value) {
                displayMovieRecommendation(movieResponse.value);
            } else if (MOVIE_AGENT_URL !== 'YOUR_MOVIE_AGENT_CLOUD_RUN_URL/recommend_movie') {
                console.error('Movie recommendation failed:', movieResponse.reason);
                alert('Failed to get movie recommendation. (Meal might still be available).');
            }

        } catch (error) {
            console.error('Overall fetch error:', error);
            hideLoading();
            alert('An unexpected error occurred. Please try again.');
        }
    });

    // --- NEW: Event Listener for the Quick Mood Select Dropdown ---
    quickMoodSelect.addEventListener('change', () => {
        const selectedMood = quickMoodSelect.value;
        if (selectedMood) { // Only if a valid mood is selected (not the default option)
            moodInput.value = selectedMood; // Update the text input with the selected mood
            getRecommendationsBtn.click(); // Programmatically click the main button
        }
        quickMoodSelect.value = ""; // Reset dropdown to default option after selection
    });

    // --- Helper Functions ---

    function getMealContext() {
        const now = new Date();
        const hour = now.getHours(); // 0-23

        if (hour >= 5 && hour < 11) { // 5 AM to 10:59 AM
            return "breakfast";
        } else if (hour >= 11 && hour < 15) { // 11 AM to 2:59 PM
            return "lunch";
        } else if (hour >= 15 && hour < 21) { // 3 PM to 8:59 PM
            return "dinner";
        } else {
            return "general"; // For late night, early morning, or unspecified
        }
    }

    async function fetchRecommendation(url, mood, mealContext = null) {
        const bodyData = { mood: mood };
        if (mealContext && url === MEAL_AGENT_URL) {
            bodyData.mealContext = mealContext;
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || response.statusText}`);
        }
        return response.json();
    }

    function displayMealRecommendation(data) {
        if (data.mealTitle) {
            mealTitleElem.textContent = data.mealTitle;
            mealImageElem.src = data.mealImageUrl || 'https://via.placeholder.com/312x231?text=No+Image';
            mealImageElem.alt = data.mealTitle;
            mealDescriptionElem.innerHTML = data.mealDescription || 'No description available.';
            mealSourceUrlElem.href = data.mealSourceUrl || '#';
            mealResultDiv.classList.remove('hidden');
        } else {
            console.warn('Meal data is incomplete:', data);
            mealResultDiv.classList.add('hidden');
        }
    }

    function displayMovieRecommendation(data) {
    if (data.movieTitle) {
        movieTitleElem.textContent = data.movieTitle;
        movieImageElem.src = data.moviePosterUrl;
        movieImageElem.alt = data.movieTitle;

        // NEW: Populate hover details
        hoverMovieTitleElem.textContent = data.movieTitle; // Title for hover overlay
        hoverMovieYearElem.textContent = `Year: ${data.movieYear || 'N/A'}`;
        hoverMovieRuntimeElem.textContent = `Runtime: ${data.movieRuntime || 'N/A'}`;
        hoverMovieRatingElem.textContent = `Rating: ${data.movieRating || 'N/A'}`; // MPAA rating
        hoverMovieVoteAverageElem.textContent = `TMDB Score: ${data.movieVoteAverage || 'N/A'}`; // TMDB 0-10 score

        movieDescriptionElem.textContent = data.movieDescription || 'No description available.';
        movieSourceUrlElem.href = data.movieSourceUrl || '#';
        movieResultDiv.classList.remove('hidden');
    } else {
        console.warn('Movie data is incomplete or invalid:', data);
        movieResultDiv.classList.add('hidden');
    }
}

    function showLoading() {
        loadingSpinner.classList.remove('hidden');
        buttonText.textContent = 'Getting Recommendations...';
        getRecommendationsBtn.disabled = true;
    }

    function hideLoading() {
        loadingSpinner.classList.add('hidden');
        buttonText.textContent = 'Get Recommendations';
        getRecommendationsBtn.disabled = false;
    }

    function hideAllResults() {
        mealResultDiv.classList.add('hidden');
        movieResultDiv.classList.add('hidden');
    }
});
