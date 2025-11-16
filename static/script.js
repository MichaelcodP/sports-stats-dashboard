document.getElementById('team-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const teamName = document.getElementById('team-name').value.trim();
    if (!teamName) return;
    await fetchAndDisplay('/api/analyze/team/' + encodeURIComponent(teamName), 'Team Analysis Results');
});

document.getElementById('all-models-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const team1 = document.getElementById('team1').value.trim();
    const team2 = document.getElementById('team2').value.trim();
    if (!team1 || !team2) return;
    await fetchAndDisplay('/api/analyze/all-models/' + encodeURIComponent(team1) + '/' + encodeURIComponent(team2), 'All Models Analysis');
});

document.getElementById('metrics-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    await fetchAndDisplay('/api/metrics', 'Metrics');
});

async function fetchAndDisplay(url, title) {
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const resultsTitle = document.getElementById('results-title');
    const teamInfoDiv = document.getElementById('team-info');
    const matchesDiv = document.getElementById('matches');
    const analysisDiv = document.getElementById('analysis');
    const metricsDiv = document.getElementById('metrics');

    // Show loading
    resultsDiv.style.display = 'block';
    resultsTitle.textContent = title;
    loadingDiv.style.display = 'block';
    teamInfoDiv.innerHTML = '';
    matchesDiv.innerHTML = '';
    analysisDiv.innerHTML = '';
    metricsDiv.innerHTML = '';

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();

        // Hide loading
        loadingDiv.style.display = 'none';

        if (url.includes('/api/analyze/team/')) {
            displayTeamAnalysis(data);
        } else if (url.includes('/api/analyze/all-models/')) {
            displayAllModels(data);
        } else if (url.includes('/api/metrics')) {
            displayMetrics(data);
        }

    } catch (error) {
        loadingDiv.style.display = 'none';
        teamInfoDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

function displayTeamAnalysis(data) {
    const teamInfoDiv = document.getElementById('team-info');
    const matchesDiv = document.getElementById('matches');
    const analysisDiv = document.getElementById('analysis');

    // Display team info
    teamInfoDiv.innerHTML = `
        <div class="team-info">
            <h3>${data.team_name}</h3>
            <p><strong>Country:</strong> ${data.country || 'N/A'}</p>
            <p><strong>Sport:</strong> ${data.sport || 'N/A'}</p>
            <p><strong>League:</strong> ${data.league || 'N/A'}</p>
        </div>
    `;

    // Display matches
    if (data.matches && data.matches.length > 0) {
        matchesDiv.innerHTML = '<h3>Recent Matches</h3>';
        data.matches.forEach(match => {
            const homeScore = match.home_score !== null && match.home_score !== undefined ? match.home_score : 'N/A';
            const awayScore = match.away_score !== null && match.away_score !== undefined ? match.away_score : 'N/A';
            matchesDiv.innerHTML += `
                <div class="match">
                    <p><strong>${match.home_team} vs ${match.away_team}</strong></p>
                    <p><strong>Score:</strong> ${homeScore} - ${awayScore}</p>
                    <p><strong>Date:</strong> ${match.date || 'N/A'}</p>
                    <p><strong>League:</strong> ${match.league || 'N/A'}</p>
                </div>
            `;
        });
    } else {
        matchesDiv.innerHTML = '<p>No recent matches found.</p>';
    }

    // Display analysis
    if (data.analysis) {
        analysisDiv.innerHTML = `
            <h3>AI Analysis</h3>
            <div class="analysis">
                <p>${data.analysis.replace(/\n/g, '<br>')}</p>
            </div>
        `;
    } else {
        analysisDiv.innerHTML = '<p>No analysis available.</p>';
    }
}

function displayAllModels(data) {
    const analysisDiv = document.getElementById('analysis');
    if (data.models) {
        analysisDiv.innerHTML = `
            <h3>All Models Analysis</h3>
            <p><strong>Teams:</strong> ${data.teams}</p>
            <p><strong>Event ID:</strong> ${data.event_id}</p>
        `;
        for (const [model, analysis] of Object.entries(data.models)) {
            if (analysis) {
                analysisDiv.innerHTML += `
                    <div class="model-analysis">
                        <h4>${model.toUpperCase()}</h4>
                        <p><strong>Summary:</strong> ${analysis.summary}</p>
                        <p><strong>Key Insights:</strong> ${analysis.key_insights.join(', ')}</p>
                        <p><strong>Performance Analysis:</strong> ${analysis.performance_analysis}</p>
                        <p><strong>Prediction:</strong> ${analysis.prediction || 'N/A'}</p>
                    </div>
                `;
            } else {
                analysisDiv.innerHTML += `<div class="model-analysis"><h4>${model.toUpperCase()}</h4><p>Analysis failed</p></div>`;
            }
        }
    } else {
        analysisDiv.innerHTML = '<p>No analysis available.</p>';
    }
}

function displayMetrics(data) {
    const metricsDiv = document.getElementById('metrics');
    if (data) {
        metricsDiv.innerHTML = `
            <h3>Metrics</h3>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
    } else {
        metricsDiv.innerHTML = '<p>No metrics available.</p>';
    }
}