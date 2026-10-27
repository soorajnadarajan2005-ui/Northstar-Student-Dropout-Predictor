const form = document.querySelector('#prediction-form');
const resultEmpty = document.querySelector('#result-empty');
const resultContent = document.querySelector('#result-content');
const resultTitle = document.querySelector('#result-title');
const riskPercent = document.querySelector('#risk-percent');
const riskBadge = document.querySelector('#risk-badge');
const recommendation = document.querySelector('#recommendation');
const resultCopy = document.querySelector('#result-copy');
const recentBody = document.querySelector('#recent-body');
const featureList = document.querySelector('#feature-list');
const exportButton = document.querySelector('#export-button');

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'}[character]));
}

function renderRecent(items) {
  if (!items.length) return;
  recentBody.innerHTML = items.map((item) => `<tr><td><strong>${escapeHtml(item.student_name)}</strong></td><td><span class="level ${escapeHtml(item.risk_level.toLowerCase())}">${escapeHtml(item.risk_level.toUpperCase())}</span></td><td>${Math.round(item.risk_probability * 100)}%</td><td>${new Date(`${item.created_at}Z`).toLocaleDateString()}</td></tr>`).join('');
  document.querySelector('#assessment-count').textContent = `${items.length} most recent records`;
}

async function loadRecent() {
  const response = await fetch('/api/recent');
  renderRecent(await response.json());
}

async function loadOverview() {
  const data = await (await fetch('/api/overview')).json();
  document.querySelector('#students-count').textContent = data.students;
  document.querySelector('#risk-rate').textContent = `${Math.round(data.elevated_rate * 100)}%`;
  document.querySelector('#risk-count').textContent = `${data.elevated_risk} students in elevated-risk class`;
  document.querySelector('#risk-progress').style.width = `${Math.round(data.elevated_rate * 100)}%`;
  document.querySelector('#model-accuracy').textContent = `${Math.round(data.metrics.balanced_accuracy * 100)}%`;
  document.querySelector('#roc-auc').textContent = `${Math.round(data.metrics.roc_auc * 100)}%`;
  document.querySelector('#trained-on').textContent = data.metrics.trained_on;
  const max = Math.max(...data.features.map((item) => item.importance));
  featureList.innerHTML = data.features.sort((a, b) => b.importance - a.importance).map((item) => `<div class="feature-row"><div><span>${item.name.replaceAll('_', ' ')}</span><strong>${Math.round(item.importance * 100)}%</strong></div><div class="feature-track"><i style="width:${Math.round(item.importance / max * 100)}%"></i></div></div>`).join('');
}

function exportHistory() {
  const rows = [...document.querySelectorAll('#recent-body tr')].map((row) => [...row.children].map((cell) => cell.textContent.trim()));
  if (!rows.length || rows[0].length < 4) return;
  const csv = [['Student', 'Risk level', 'Probability', 'Assessed'], ...rows].map((row) => row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(',')).join('\n');
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
  link.download = 'northstar-assessments.csv';
  link.click();
  URL.revokeObjectURL(link.href);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button');
  button.disabled = true;
  button.firstChild.textContent = 'Calculating... ';
  const payload = Object.fromEntries(new FormData(form));
  Object.keys(payload).forEach((key) => { if (key !== 'student_name') payload[key] = Number(payload[key]); });
  try {
    const response = await fetch('/api/predict', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    const percent = Math.round(data.probability * 100);
    resultEmpty.classList.add('hidden');
    resultContent.classList.remove('hidden');
    resultTitle.textContent = `${payload.student_name}'s result`;
    riskPercent.textContent = `${percent}%`;
    riskBadge.textContent = `${data.risk_level.toUpperCase()} RISK`;
    riskBadge.className = `risk-badge ${data.risk_level.toLowerCase()}`;
    recommendation.textContent = data.risk_level === 'High' ? 'Consider an intervention plan' : data.risk_level === 'Medium' ? 'A little more support could help' : 'Keep supporting this student';
    resultCopy.textContent = data.risk_level === 'High' ? 'Prioritize a conversation with the student and their support network.' : 'The current signals suggest a healthy trajectory.';
    document.querySelector('#confidence-value').textContent = `${Math.round(data.confidence * 100)}%`;
    document.querySelector('#recommended-action').textContent = data.recommended_action;
    document.querySelector('#action-box').classList.remove('hidden');
    resultCopy.textContent = data.signals.map((signal) => `${signal.label}: ${signal.impact.toLowerCase()}`).join(' · ');
    const ringColor = data.risk_level === 'High' ? '#d45c4c' : data.risk_level === 'Medium' ? '#e6a52c' : '#208c5b';
    document.querySelector('.risk-ring').style.background = `radial-gradient(circle at center,#e5f4e7 57%,transparent 58%),conic-gradient(${ringColor} ${percent * 3.6}deg,#b5dfc0 ${percent * 3.6}deg 360deg)`;
    renderRecent(data.recent);
  } catch (error) { window.alert(error.message); }
  button.disabled = false;
  button.firstChild.textContent = 'Run risk assessment ';
});

loadRecent();
loadOverview();
exportButton.addEventListener('click', exportHistory);
