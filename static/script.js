document.getElementById('team-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const teamName = document.getElementById('team-name').value.trim();
    if (!teamName) return;

    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const teamInfoDiv = document.getElementById('team-info');
    const matchesDiv = document.getElementById('matches');
    const analysisDiv = document.getElementById('analysis');

    // Show loading
    resultsDiv.style.display = 'block';
    loadingDiv.style.display = 'block';
    teamInfoDiv.innerHTML = '';
    matchesDiv.innerHTML = '';
    analysisDiv.innerHTML = '';

    try {
        // Fetch team analysis
        const response = await fetch(`/api/analyze/team/${encodeURIComponent(teamName)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();

        // Hide loading
        loadingDiv.style.display = 'none';

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

    } catch (error) {
        loadingDiv.style.display = 'none';
        teamInfoDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});