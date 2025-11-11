// Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const systemStatus = document.getElementById('system-status');
const docCount = document.getElementById('doc-count');
const modelName = document.getElementById('model-name');
const initSection = document.getElementById('init-section');
const qaSection = document.getElementById('qa-section');
const indexBtn = document.getElementById('index-btn');
const indexResult = document.getElementById('index-result');
const questionInput = document.getElementById('question-input');
const topKInput = document.getElementById('top-k');
const askBtn = document.getElementById('ask-btn');
const answerSection = document.getElementById('answer-section');
const answerContent = document.getElementById('answer-content');
const answerModel = document.getElementById('answer-model');
const chunksUsed = document.getElementById('chunks-used');
const tokenUsage = document.getElementById('token-usage');
const contextList = document.getElementById('context-list');
const exampleBtns = document.querySelectorAll('.example-btn');

// Initialize app
async function initialize() {
    await checkStatus();
}

// Check system status
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();

        if (response.ok) {
            systemStatus.textContent = 'Healthy';
            systemStatus.className = 'status-value healthy';
            docCount.textContent = data.documents_indexed;
            modelName.textContent = data.llm_model;

            // Show/hide sections based on whether documents are indexed
            if (data.documents_indexed > 0) {
                initSection.style.display = 'none';
                qaSection.style.display = 'block';
            } else {
                initSection.style.display = 'block';
                qaSection.style.display = 'none';
            }
        } else {
            throw new Error('Status check failed');
        }
    } catch (error) {
        console.error('Status check error:', error);
        systemStatus.textContent = 'Error';
        systemStatus.className = 'status-value error';
        docCount.textContent = '?';
        modelName.textContent = '?';
    }
}

// Index the paper
async function indexPaper() {
    const btnText = indexBtn.querySelector('.btn-text');
    const btnLoading = indexBtn.querySelector('.btn-loading');

    try {
        // Show loading state
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        indexBtn.disabled = true;
        indexResult.className = 'result-message';
        indexResult.style.display = 'none';

        const response = await fetch(`${API_BASE_URL}/index`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            indexResult.className = 'result-message success';
            indexResult.innerHTML = `
                <strong>Success!</strong><br>
                ${data.message}<br>
                Chunks created: ${data.chunks_created}<br>
                Documents indexed: ${data.documents_indexed}
            `;

            // Refresh status and show Q&A section
            setTimeout(() => {
                checkStatus();
            }, 1000);
        } else {
            throw new Error(data.detail || 'Indexing failed');
        }
    } catch (error) {
        console.error('Indexing error:', error);
        indexResult.className = 'result-message error';
        indexResult.innerHTML = `<strong>Error:</strong> ${error.message}`;
    } finally {
        btnText.style.display = 'flex';
        btnLoading.style.display = 'none';
        indexBtn.disabled = false;
    }
}

// Ask a question
async function askQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        alert('Please enter a question');
        return;
    }

    const btnText = askBtn.querySelector('.btn-text');
    const btnLoading = askBtn.querySelector('.btn-loading');

    try {
        // Show loading state
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        askBtn.disabled = true;
        answerSection.style.display = 'none';

        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                top_k: parseInt(topKInput.value)
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayAnswer(data);
        } else {
            throw new Error(data.detail || 'Failed to get answer');
        }
    } catch (error) {
        console.error('Question error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        btnText.style.display = 'flex';
        btnLoading.style.display = 'none';
        askBtn.disabled = false;
    }
}

// Display answer
function displayAnswer(data) {
    // Set answer content
    answerContent.textContent = data.answer;

    // Set metadata
    answerModel.textContent = data.model;
    chunksUsed.textContent = data.context_chunks_used;
    tokenUsage.textContent = `${data.usage.input_tokens} in / ${data.usage.output_tokens} out`;

    // Display context chunks
    contextList.innerHTML = '';
    data.context.forEach((ctx, index) => {
        const contextItem = document.createElement('div');
        contextItem.className = 'context-item';

        const contextText = document.createElement('div');
        contextText.className = 'context-text';
        contextText.textContent = ctx.text;

        const contextScore = document.createElement('div');
        contextScore.className = 'context-score';
        contextScore.textContent = `Relevance: ${(ctx.relevance_score * 100).toFixed(1)}%`;

        contextItem.appendChild(contextText);
        contextItem.appendChild(contextScore);
        contextList.appendChild(contextItem);
    });

    // Show answer section
    answerSection.style.display = 'block';

    // Scroll to answer
    answerSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Event listeners
indexBtn.addEventListener('click', indexPaper);
askBtn.addEventListener('click', askQuestion);

// Handle Enter key in textarea (Ctrl+Enter to submit)
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        askQuestion();
    }
});

// Example questions
exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.getAttribute('data-question');
        questionInput.value = question;
        questionInput.focus();
        // Optionally auto-submit
        // askQuestion();
    });
});

// Initialize on page load
initialize();
