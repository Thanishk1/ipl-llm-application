const BATTING_ORDER = [
    'Number of Matches', 'Runs Scored', 'Balls Faced', 'Strike Rate',
    'Number of Fours', 'Number of Sixes', 'Number of Hundreds',
    'Number of Fifties', 'Number of Not Outs', 'Average'
];

const BOWLING_ORDER = [
    'Number of Matches', 'Wickets Taken', 'Balls Bowled',
    'Runs Conceded', 'Economy Rate', 'Bowling Strike Rate', 'Average', 'Bowler Extras'
];

async function loadTeams() {
    const res = await fetch('/api/teams');
    const teams = await res.json();
    const select = document.getElementById('team_select');
    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        select.appendChild(option);
    });
}

async function loadSeasons() {
    const res = await fetch('/api/seasons');
    const seasons = await res.json();
    const select = document.getElementById('season_select');
    seasons.forEach(season => {
        const option = document.createElement('option');
        option.value = season;
        option.textContent = season;
        select.appendChild(option);
    });
}

async function loadSquad() {
    const team = document.getElementById('team_select').value;
    const season = document.getElementById('season_select').value;
    if (!team || !season) return;

    const res = await fetch(`/api/squad?team=${encodeURIComponent(team)}&season=${season}`);
    const players = await res.json();

    const select = document.getElementById('player_select');
    select.innerHTML = '';
    players.forEach(player => {
        const option = document.createElement('option');
        option.value = player;
        option.textContent = player;
        select.appendChild(option);
    });
}

function renderStats(stats, order) {
    if (stats.error) {
        document.getElementById('stats_result').innerHTML = `<p style="color:red">${stats.error}</p>`;
        return;
    }
    let html = '<table>';
    order.forEach(key => {
        if (key in stats) {
            const value = stats[key];
            html += `<tr><td><b>${key}</b></td><td>${typeof value === 'number' ? value.toFixed(2) : value}</td></tr>`;
        }
    });
    html += '</table>';
    document.getElementById('stats_result').innerHTML = html;
}

async function fetchBattingStats() {
    const season = document.getElementById('season_select').value;
    const player = document.getElementById('player_select').value;
    const res = await fetch(`/api/batsman_stats?season=${season}&player=${encodeURIComponent(player)}`);
    const stats = await res.json();
    renderStats(stats, BATTING_ORDER);
}

async function fetchBowlingStats() {
    const season = document.getElementById('season_select').value;
    const player = document.getElementById('player_select').value;
    const res = await fetch(`/api/bowler_stats?season=${season}&player=${encodeURIComponent(player)}`);
    const stats = await res.json();
    renderStats(stats, BOWLING_ORDER);
}

async function askQuestion() {
    const query = document.getElementById('ask_input').value;
    await runAsk(query);
}

// runAsk does the actual request. match_id is only passed in when the user
// has already resolved an earlier ambiguous-match prompt by clicking a candidate.
async function runAsk(query, match_id) {
    document.getElementById('ask_result').innerHTML = "Thinking...";
    const body = match_id ? { query, match_id } : { query };
    const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json();

    if (data.ambiguous) {
        let html = '<p>This query matches more than one game. Which one did you mean?</p><ul>';
        data.candidates.forEach(c => {
            html += `<li><a href="#" onclick="runAsk('${query.replace(/'/g, "\\'")}', ${c.match_id}); return false;">
                        ${c.date} at ${c.venue}
                     </a></li>`;
        });
        html += '</ul>';
        document.getElementById('ask_result').innerHTML = html;
        return;
    }

    document.getElementById('ask_result').innerText = data.answer || data.error;
}

document.getElementById('team_select').addEventListener('change', loadSquad);
document.getElementById('season_select').addEventListener('change', loadSquad);

loadTeams();
loadSeasons();