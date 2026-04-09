
const GH_REPO = 'jon-goldman/briefings';
const GH_API = 'https://api.github.com';
const MEMORY_FILE = 'memory.json';
let ghToken = localStorage.getItem('gh_briefing_token') || '';
let memorySha = null;
let mem = { completed: {}, snoozed: {} };
let saveTimer = null;
const TODAY = new Date().toISOString().split('T')[0];

async function connectGitHub() {
  const t = prompt('Paste your GitHub Personal Access Token (starts with github_pat_):\n\nStored in this browser\'s localStorage — enter once per device.');
  if (!t || !t.trim()) return;
  localStorage.setItem('gh_briefing_token', t.trim());
  ghToken = t.trim();
  await loadMemory();
}

async function loadMemory() {
  if (!ghToken) return;
  setMemStatus('Connecting…');
  try {
    const r = await fetch(`${GH_API}/repos/${GH_REPO}/contents/${MEMORY_FILE}`,
      { headers: { 'Authorization': `Bearer ${ghToken}`, 'Accept': 'application/vnd.github+json' } });
    if (!r.ok) throw new Error(`GitHub API ${r.status}`);
    const d = await r.json();
    memorySha = d.sha;
    const parsed = JSON.parse(atob(d.content.replace(/\s/g, '')));
    mem.completed = parsed.completed || {};
    mem.snoozed = parsed.snoozed || {};
    applyMemory();
    const btn = document.getElementById('mem-btn');
    btn.textContent = '✓ GitHub synced'; btn.classList.add('connected'); btn.onclick = null;
    setMemStatus('Memory loaded ✓', 2000);
  } catch(e) { setMemStatus(`⚠ ${e.message}`); }
}

function setMemStatus(msg, ms) {
  const el = document.getElementById('mem-status');
  if (el) { el.textContent = msg; if (ms) setTimeout(() => { el.textContent = ''; }, ms); }
}

function applyMemory() {
  const snoozeList = document.getElementById('snoozed-list');
  let snoozeCount = 0;
  document.querySelectorAll('input[type="checkbox"][data-id]').forEach(cb => {
    const id = cb.dataset.id;
    if (mem.completed[id]) {
      cb.checked = true;
      cb.closest('.action-item')?.querySelector('.al')?.classList.add('done');
    }
    if (mem.snoozed[id]) {
      if (mem.snoozed[id] > TODAY) {
        cb.closest('.action-item')?.style.setProperty('display','none');
        snoozeCount++;
        if (snoozeList) {
          const label = cb.closest('.action-item')?.querySelector('.al')?.textContent || id;
          snoozeList.insertAdjacentHTML('beforeend',
            `<li class="snoozed-item"><span class="al">${label}</span> <span class="snooze-date">until ${mem.snoozed[id]}</span> <button onclick="unsnooze('${id}')">↩ restore</button></li>`);
        }
      } else { delete mem.snoozed[id]; }
    }
  });
  const sc = document.getElementById('snooze-count');
  if (sc) sc.textContent = snoozeCount;
}

function scheduleSave() { clearTimeout(saveTimer); saveTimer = setTimeout(persistMemory, 500); }

async function persistMemory() {
  if (!ghToken || !memorySha) return;
  const payload = JSON.stringify({ completed: mem.completed, snoozed: mem.snoozed, updatedAt: new Date().toISOString() }, null, 2);
  try {
    const r = await fetch(`${GH_API}/repos/${GH_REPO}/contents/${MEMORY_FILE}`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${ghToken}`, 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `Update briefing memory ${TODAY}`, content: btoa(unescape(encodeURIComponent(payload))), sha: memorySha })
    });
    if (!r.ok) throw new Error(r.status);
    memorySha = (await r.json()).content.sha;
    const el = document.getElementById('mem-save-indicator');
    el.classList.add('visible'); setTimeout(() => el.classList.remove('visible'), 1500);
  } catch(e) { console.error('GitHub save error:', e); }
}

function toggle(cb) {
  const id = cb.dataset.id;
  cb.closest('.action-item')?.querySelector('.al')?.classList.toggle('done', cb.checked);
  if (!id) return;
  if (cb.checked) mem.completed[id] = TODAY; else delete mem.completed[id];
  scheduleSave();
}

function snoozeItem(id, label) {
  const input = prompt(`Snooze "${label}" until when?\nEnter date (e.g. Apr 15 or 2026-04-20):`);
  if (!input) return;
  let date = input.trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    const d = new Date(date.match(/\d{4}/) ? date : date + ' 2026');
    if (isNaN(d)) { alert('Try YYYY-MM-DD format'); return; }
    date = d.toISOString().split('T')[0];
  }
  if (date <= TODAY) { alert('Date must be in the future'); return; }
  mem.snoozed[id] = date;
  const cb = document.querySelector(`input[data-id="${id}"]`);
  cb?.closest('.action-item')?.style.setProperty('display','none');
  scheduleSave();
  setMemStatus(`Snoozed until ${date}`, 2000);
}

function unsnooze(id) {
  delete mem.snoozed[id];
  const cb = document.querySelector(`input[data-id="${id}"]`);
  cb?.closest('.action-item')?.style.removeProperty('display');
  document.querySelectorAll('.snoozed-item').forEach(li => { if (li.outerHTML.includes(`'${id}'`)) li.remove(); });
  const sc = document.getElementById('snooze-count');
  if (sc) sc.textContent = parseInt(sc.textContent || '0') - 1;
  scheduleSave();
}

if (ghToken) loadMemory();

