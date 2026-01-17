const form = document.getElementById("story-form");
const loadingSection = document.getElementById("loading-section");
const resultsSection = document.getElementById("results-section");
const errorSection = document.getElementById("error-section");

const titleEl = document.getElementById("story-title");
const storyTextEl = document.getElementById("story-text");
const cultureEl = document.getElementById("culture-value");
const languageEl = document.getElementById("language-value");
const moralBox = document.getElementById("story-moral");
const moralText = document.querySelector(".moral-text");

const generateBtn = document.getElementById("generate-btn");
const newStoryBtn = document.getElementById("new-story-btn");
const retryBtn = document.getElementById("retry-btn");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const culture = document.getElementById("culture-select").value;
    const language = document.getElementById("language-select").value;
    const theme = document.getElementById("theme-select").value;

    loadingSection.hidden = false;
    resultsSection.hidden = true;
    errorSection.hidden = true;
    generateBtn.disabled = true;

    try {
        const response = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ culture, language, theme })
        });

        if (!response.ok) {
            throw new Error("Story generation failed");
        }

        const data = await response.json();

        titleEl.textContent = data.title;
        storyTextEl.textContent = data.story_text;
        cultureEl.textContent = data.culture;
        languageEl.textContent = data.language;

        if (data.moral) {
            moralText.textContent = data.moral;
            moralBox.hidden = false;
        } else {
            moralBox.hidden = true;
        }

        loadingSection.hidden = true;
        resultsSection.hidden = false;

    } catch (err) {
        loadingSection.hidden = true;
        errorSection.hidden = false;
        document.getElementById("error-message").textContent = err.message;
    } finally {
        generateBtn.disabled = false;
    }
});

newStoryBtn.addEventListener("click", () => {
    resultsSection.hidden = true;
});

retryBtn.addEventListener("click", () => {
    errorSection.hidden = true;
});
