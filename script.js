// Define API endpoints globally - these can be outside DOMContentLoaded
const MEAL_AGENT_URL = 'https://meal-agent-702694291445.us-central1.run.app/recommend_meal';
const MOVIE_AGENT_URL = 'https://movie-agent-702694291445.us-central1.run.app/recommend_movie';

// Ensure all DOM-dependent code runs after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const partnerOneMoodInput = document.getElementById('partnerOneMoodInput');
    const partnerTwoMoodInput = document.getElementById('partnerTwoMoodInput');
    const moodValidation = document.getElementById('moodValidation');
    const moodChoiceButtons = document.querySelectorAll('.mood-choice');
    const getRecommendationsBtn = document.getElementById('getRecommendationsBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const buttonText = document.getElementById('buttonText');
    
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

    const hoverMovieTitleElem = document.getElementById('hoverMovieTitle');
    const hoverMovieYearElem = document.getElementById('hoverMovieYear');
    const hoverMovieRuntimeElem = document.getElementById('hoverMovieRuntime');
    const hoverMovieRatingElem = document.getElementById('hoverMovieRating');
    const hoverMovieVoteAverageElem = document.getElementById('hoverMovieVoteAverage');

    // NEW: Theme related element references
    const lightModeBtn = document.getElementById('lightModeBtn');
    const darkModeBtn = document.getElementById('darkModeBtn');
    const body = document.body; // Reference to the body element
    const selectedMoods = {
        one: '',
        two: ''
    };

    // --- Theme Logic ---
    // Function to set the theme
    function setTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
        updateThemeButtons(theme);
    }

    // Function to update the active theme button styles
    function updateThemeButtons(currentTheme) {
        if (currentTheme === 'dark') {
            darkModeBtn.classList.add('bg-gray-700', 'text-white');
            lightModeBtn.classList.remove('bg-gray-700', 'text-white');
        } else {
            lightModeBtn.classList.add('bg-gray-700', 'text-white');
            darkModeBtn.classList.remove('bg-gray-700', 'text-white');
        }
    }

    // Apply saved theme on load, or default to light, or system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // Check for system dark mode preference
        setTheme('dark');
    } else {
        setTheme('light'); // Default to light if no preference
    }

    // Event listeners for theme buttons
    lightModeBtn.addEventListener('click', () => setTheme('light'));
    darkModeBtn.addEventListener('click', () => setTheme('dark'));

    // --- Event Listener for the Main Button ---
    getRecommendationsBtn.addEventListener('click', async () => {
        const dateNightInput = getDateNightInput();
        const validationMessage = getValidationMessage(dateNightInput);
        if (validationMessage) {
            showValidation(validationMessage);
            return;
        }

        clearValidation();
        hideAllResults();
        showLoading();

        const mealContext = getMealContext();
        const combinedMood = toCombinedMoodString(dateNightInput);

        try {
            const [mealResponse, movieResponse] = await Promise.allSettled([
                fetchRecommendation(MEAL_AGENT_URL, combinedMood, mealContext),
                MOVIE_AGENT_URL !== 'YOUR_MOVIE_AGENT_CLOUD_RUN_URL/recommend_movie' ? fetchRecommendation(MOVIE_AGENT_URL, combinedMood) : Promise.resolve(null)
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

    moodChoiceButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const partner = button.dataset.partner;
            const mood = button.dataset.mood;
            selectedMoods[partner] = selectedMoods[partner] === mood ? '' : mood;
            updateMoodChoiceButtons(partner);
            clearValidationIfValid();
        });
    });

    partnerOneMoodInput.addEventListener('input', clearValidationIfValid);
    partnerTwoMoodInput.addEventListener('input', clearValidationIfValid);

    // --- Helper Functions ---

    function getDateNightInput() {
        return {
            partnerOneMood: getPartnerMood('one', partnerOneMoodInput),
            partnerTwoMood: getPartnerMood('two', partnerTwoMoodInput)
        };
    }

    function getPartnerMood(partner, inputElement) {
        const typedMood = inputElement.value.trim();
        return typedMood || selectedMoods[partner];
    }

    function toCombinedMoodString(dateNightInput) {
        return `Partner One feels: ${dateNightInput.partnerOneMood}. Partner Two feels: ${dateNightInput.partnerTwoMood}.`;
    }

    function getValidationMessage(dateNightInput) {
        const missingPartnerOne = !dateNightInput.partnerOneMood;
        const missingPartnerTwo = !dateNightInput.partnerTwoMood;

        if (missingPartnerOne && missingPartnerTwo) {
            return 'Please add a mood for Partner One and Partner Two before planning your night.';
        }
        if (missingPartnerOne) {
            return 'Please add a mood for Partner One before planning your night.';
        }
        if (missingPartnerTwo) {
            return 'Please add a mood for Partner Two before planning your night.';
        }
        return '';
    }

    function showValidation(message) {
        moodValidation.textContent = message;
        moodValidation.classList.remove('hidden');
    }

    function clearValidation() {
        moodValidation.textContent = '';
        moodValidation.classList.add('hidden');
    }

    function clearValidationIfValid() {
        if (!getValidationMessage(getDateNightInput())) {
            clearValidation();
        }
    }

    function updateMoodChoiceButtons(partner) {
        moodChoiceButtons.forEach((button) => {
            if (button.dataset.partner !== partner) {
                return;
            }

            const isSelected = selectedMoods[partner] === button.dataset.mood;
            button.setAttribute('aria-pressed', String(isSelected));
            button.classList.toggle('bg-[var(--button-bg)]', isSelected);
            button.classList.toggle('text-white', isSelected);
            button.classList.toggle('font-bold', isSelected);
            button.classList.toggle('shadow-md', isSelected);
            button.classList.toggle('border-transparent', isSelected);
            button.classList.toggle('bg-[var(--secondary-bg)]', !isSelected);
        });
    }

    function getMealContext() {
        const now = new Date();
        const hour = now.getHours();

        if (hour >= 5 && hour < 11) {
            return "breakfast";
        } else if (hour >= 11 && hour < 15) {
            return "lunch";
        } else if (hour >= 15 && hour < 21) {
            return "dinner";
        } else {
            return "general";
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
            // Sanitize any HTML from the API using DOMPurify to prevent XSS.
            const rawDescription = data.mealDescription || 'No description available.';
            const safeDescription = window.DOMPurify ? window.DOMPurify.sanitize(rawDescription, {ALLOWED_ATTR: ['href', 'title', 'target', 'rel'], ADD_ATTR: ['target', 'rel']}) : rawDescription;
            mealDescriptionElem.innerHTML = safeDescription;
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

            hoverMovieTitleElem.textContent = data.movieTitle;
            hoverMovieYearElem.textContent = `Year: ${data.movieYear || 'N/A'}`;
            hoverMovieRuntimeElem.textContent = `Runtime: ${data.movieRuntime || 'N/A'}`;
            hoverMovieRatingElem.textContent = `Rating: ${data.movieRating || 'N/A'}`;
            hoverMovieVoteAverageElem.textContent = `TMDB Score: ${data.movieVoteAverage || 'N/A'}`;

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
        buttonText.textContent = 'Planning Our Night...';
        getRecommendationsBtn.disabled = true;
    }

    function hideLoading() {
        loadingSpinner.classList.add('hidden');
        buttonText.textContent = 'Plan Our Night';
        getRecommendationsBtn.disabled = false;
    }

    function hideAllResults() {
        mealResultDiv.classList.add('hidden');
        movieResultDiv.classList.add('hidden');
    }
});
