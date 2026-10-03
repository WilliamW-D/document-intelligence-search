// Document Intelligence Search - Frontend Application
let currentSearchMode = 'hybrid';
let currentResults = [];
let currentCitations = [];

document.addEventListener('DOMContentLoaded', () => {
    executeSearch();
});

function setSearchMode(mode) {
    currentSearchMode = mode;
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-mode-${mode}`).classList.add('active');
    document.getElementById('search-mode-tag').textContent = mode.toUpperCase() + ' SEARCH';
    executeSearch();
}

function updateWeights(val) {
    const semPct = Math.round(val * 100);
    const kwPct = 100 - semPct;
    document.getElementById('weight-val').textContent = `Semantic ${semPct}% / Keyword ${kwPct}%`;
    executeSearch();
}

function handleKeyDown(e) {
    if (e.key === 'Enter') {
        executeSearch();
    }
}

async function executeSearch() {
    const query = document.getElementById('query-input').value.trim();
    if (!query) return;

    const category = document.getElementById('category-select').value;
    const semWeight = parseFloat(document.getElementById('weight-slider').value);
    const kwWeight = 1.0 - semWeight;

    const reqPayload = {
        query: query,
        category_filter: category,
        top_k: 5,
        search_mode: currentSearchMode,
        semantic_weight: semWeight,
        keyword_weight: kwWeight
    };

    const resultsList = document.getElementById('results-list');
    resultsList.innerHTML = '<div class="loading-spinner">Searching vectors and keyword index...</div>';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reqPayload)
        });

        const data = await response.json();
        currentResults = data.results || [];
        currentCitations = data.citations || [];
        renderResults(data);
    } catch (err) {
        console.error('Search error:', err);
        resultsList.innerHTML = '<div class="empty-state">Search request failed. Ensure backend API is active.</div>';
    }
}

function renderResults(data) {
    const resultsList = document.getElementById('results-list');
    const resultsCount = document.getElementById('results-count');

    resultsCount.textContent = `Ranked Search Results (${currentResults.length} Sources Found)`;

    if (!currentResults.length) {
        resultsList.innerHTML = '<div class="empty-state"><span class="empty-icon">🔍</span><p>No matching document passages found for query.</p></div>';
        return;
    }

    let html = '';
    currentResults.forEach((res, i) => {
        const citationKey = `[${i + 1}]`;
        html += `
            <div class="result-card ${i === 0 ? 'selected' : ''}" onclick="selectCitation(${i})">
                <div class="result-card-header">
                    <div class="doc-info">
                        <span class="citation-key">${citationKey}</span>
                        <div>
                            <div class="doc-title">${escapeHtml(res.document_title)}</div>
                            <span class="cat-badge">${escapeHtml(res.category)} • Version v${res.version_number}</span>
                        </div>
                    </div>
                    <span class="score-badge">Score: ${res.rrf_score}</span>
                </div>
                <div class="result-snippet">"${escapeHtml(res.content)}"</div>
                <div class="result-footer">
                    <span>Section: ${escapeHtml(res.section_title || 'General')}</span>
                    <span>Semantic Rank: #${res.semantic_rank}</span>
                    <span>Keyword Rank: #${res.keyword_rank}</span>
                </div>
            </div>
        `;
    });

    resultsList.innerHTML = html;
    if (currentResults.length > 0) {
        selectCitation(0);
    }
}

function selectCitation(index) {
    document.querySelectorAll('.result-card').forEach((card, i) => {
        if (i === index) card.classList.add('selected');
        else card.classList.remove('selected');
    });

    const res = currentResults[index];
    if (!res) return;

    const citationKey = `[${index + 1}]`;
    const inspector = document.getElementById('citation-inspector');

    inspector.innerHTML = `
        <div class="inspector-content">
            <div class="doc-info">
                <span class="citation-key">${citationKey}</span>
                <div>
                    <h3>${escapeHtml(res.document_title)}</h3>
                    <p class="subtitle">Document Identifier: <code>${res.doc_identifier}</code></p>
                </div>
            </div>

            <div class="inspector-meta">
                <div class="meta-row">
                    <span class="meta-label">Category:</span>
                    <span class="meta-val">${res.category}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Document Version:</span>
                    <span class="meta-val">v${res.version_number}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Section Heading:</span>
                    <span class="meta-val">${res.section_title || 'General'}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Character Offsets:</span>
                    <span class="meta-val">Chars ${res.start_char} - ${res.end_char}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Semantic Cosine Score:</span>
                    <span class="meta-val">${res.semantic_score} (Rank #${res.semantic_rank})</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Keyword BM25 Score:</span>
                    <span class="meta-val">${res.keyword_score} (Rank #${res.keyword_rank})</span>
                </div>
            </div>

            <label class="meta-label">Full Passage Context:</label>
            <div class="source-box">${escapeHtml(res.content)}</div>
        </div>
    `;
}

async function runBenchmarkEval() {
    const modal = document.getElementById('eval-modal');
    const body = document.getElementById('eval-modal-body');
    modal.classList.add('active');
    body.innerHTML = '<div class="loading-spinner">Evaluating Hit@K and Mean Reciprocal Rank (MRR) across all search modes...</div>';

    try {
        const response = await fetch('/api/evaluation/run');
        const data = await response.json();
        renderEvalResults(data);
    } catch (err) {
        console.error('Eval error:', err);
        body.innerHTML = '<div class="empty-state">Failed to run benchmark evaluation suite.</div>';
    }
}

function renderEvalResults(data) {
    const body = document.getElementById('eval-modal-body');
    const summary = data.comparison_summary || [];

    let tableRows = '';
    summary.forEach(s => {
        tableRows += `
            <tr>
                <td><strong>${s.mode}</strong></td>
                <td><span class="score-badge">${s.mrr}</span></td>
                <td>${s.hit_at_1}</td>
                <td>${s.hit_at_3}</td>
                <td>${s.hit_at_5}</td>
            </tr>
        `;
    });

    let html = `
        <p style="margin-bottom: 12px;">Comparative performance evaluation across 5 ground-truth benchmark queries measuring retrieval effectiveness:</p>
        <table class="eval-table">
            <thead>
                <tr>
                    <th>Retrieval Mode</th>
                    <th>Mean Reciprocal Rank (MRR)</th>
                    <th>Hit@1 Rate</th>
                    <th>Hit@3 Rate</th>
                    <th>Hit@5 Rate</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
        <div style="margin-top: 20px; font-size: 13px; color: #94a3b8; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
            💡 <strong>Why Hybrid Search Matters:</strong> Hybrid Reciprocal Rank Fusion (RRF) combines exact keyword precision with semantic vector search, achieving higher MRR and Hit@K scores compared to single-mode vector search alone.
        </div>
    `;
    body.innerHTML = html;
}

function closeEvalModal() {
    document.getElementById('eval-modal').classList.remove('active');
}

async function openDocCatalogModal() {
    const modal = document.getElementById('catalog-modal');
    const body = document.getElementById('catalog-modal-body');
    modal.classList.add('active');
    body.innerHTML = '<div class="loading-spinner">Loading document catalog...</div>';

    try {
        const response = await fetch('/api/documents');
        const data = await response.json();
        const docs = data.documents || [];

        let rows = '';
        docs.forEach(d => {
            rows += `
                <tr>
                    <td><code>${d.doc_identifier}</code></td>
                    <td><strong>${escapeHtml(d.title)}</strong></td>
                    <td><span class="cat-badge">${d.category}</span></td>
                    <td>v${d.version_count}</td>
                    <td>${d.total_chunks} chunks</td>
                </tr>
            `;
        });

        body.innerHTML = `
            <table class="eval-table">
                <thead>
                    <tr>
                        <th>Identifier</th>
                        <th>Document Title</th>
                        <th>Category</th>
                        <th>Versions</th>
                        <th>Chunks</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    } catch (err) {
        body.innerHTML = '<div class="empty-state">Failed to load document catalog.</div>';
    }
}

function closeCatalogModal() {
    document.getElementById('catalog-modal').classList.remove('active');
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
