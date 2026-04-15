/* briefing.js — Daily Briefing
 * Handles: JSON rendering, checkbox toggle, snooze, GitHub memory sync.
 * Compatible with both template.html (JSON-driven) and legacy dated HTML files.
 */
(function () {
  'use strict';

  const REPO        = 'jon-goldman/briefings';
  const MEMORY_PATH = 'memory.json';

  let _token     = null;
  let _memorySha = null;
  let _memory    = { completed: {}, snoozed: {}, updatedAt: null };

  // ── Tiny helpers ─────────────────────────────────────────────────────────────

  function $  (sel) { return document.querySelector(sel); }
  function esc(s)   {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  // Escape for a single-quoted JS string inside an HTML attribute
  function jsq(s) { return String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }

  function setStatus(msg) {
    const el = $('#mem-status'); if (el) el.textContent = msg;
  }
  function setSave(msg) {
    const el = $('#mem-save-indicator'); if (el) el.textContent = msg;
  }

  // ── Memory load / save ───────────────────────────────────────────────────────

  async function loadMemory() {
    if (!_token) return;
    setStatus('Loading…');
    try {
      const resp = await fetch(
        'https://api.github.com/repos/' + REPO + '/contents/' + MEMORY_PATH,
        { headers: { Authorization: 'Bearer ' + _token, Accept: 'application/vnd.github+json' } }
      );
      if (!resp.ok) { setStatus('⚠ Load failed (' + resp.status + ')'); return; }
      const d = await resp.json();
      _memorySha = d.sha;
      _memory = JSON.parse(atob(d.content.replace(/\n/g, '')));
      if (!_memory.completed) _memory.completed = {};
      if (!_memory.snoozed)   _memory.snoozed   = {};
      applyMemory();
      setStatus('✓ Synced');
    } catch (e) {
      setStatus('⚠ ' + e.message);
    }
  }

  async function saveMemory() {
    if (!_token) { setSave('Connect GitHub to save'); return; }
    setSave('Saving…');
    _memory.updatedAt = new Date().toISOString();
    const raw     = JSON.stringify(_memory, null, 2);
    const content = btoa(unescape(encodeURIComponent(raw)));
    const body    = { message: 'Update memory', content };
    if (_memorySha) body.sha = _memorySha;
    try {
      const resp = await fetch(
        'https://api.github.com/repos/' + REPO + '/contents/' + MEMORY_PATH,
        {
          method: 'PUT',
          headers: {
            Authorization: 'Bearer ' + _token,
            Accept: 'application/vnd.github+json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body)
        }
      );
      if (resp.ok) {
        const d = await resp.json();
        _memorySha = d.content.sha;
        setSave('Saved ✓');
      } else {
        setSave('⚠ Save failed');
      }
    } catch (e) {
      setSave('⚠ ' + e.message);
    }
  }

  function applyMemory() {
    // Completed
    Object.keys(_memory.completed || {}).forEach(function (id) {
      var cb = document.querySelector('[data-id="' + id + '"]');
      if (!cb) return;
      if (cb.tagName !== 'INPUT') cb = cb.querySelector('input');
      if (!cb) return;
      cb.checked = true;
      var span = cb.closest('.action-item').querySelector('.al');
      if (span) span.classList.add('done');
    });

    // Snoozed
    Object.entries(_memory.snoozed || {}).forEach(function (entry) {
      var id = entry[0], label = entry[1];
      var cb = document.querySelector('[data-id="' + id + '"]');
      if (cb) {
        var item = cb.closest ? cb.closest('.action-item') : cb.parentElement;
        if (item) item.style.display = 'none';
      }
      _addSnoozedEntry(id, label);
    });
    _updateSnoozeCount();
  }

  // ── Snooze helpers ───────────────────────────────────────────────────────────

  function _addSnoozedEntry(id, label) {
    var list = $('#snoozed-list');
    if (!list) return;
    if (list.querySelector('[data-snooze-id="' + id + '"]')) return;
    var li  = document.createElement('li');
    li.dataset.snoozeId = id;
    li.innerHTML =
      esc(label) +
      ' <button onclick="unsnoozeItem(\'' + jsq(id) + '\')">↩ unsnooze</button>';
    list.appendChild(li);
  }

  function _updateSnoozeCount() {
    var el = $('#snooze-count');
    if (el) el.textContent = Object.keys(_memory.snoozed || {}).length;
  }

  // ── Public API ───────────────────────────────────────────────────────────────

  window.connectGitHub = async function () {
    var pat = prompt('Enter your GitHub Personal Access Token:');
    if (!pat) return;
    _token = pat.trim();
    sessionStorage.setItem('gh_token', _token);
    var btn = $('#mem-btn');
    if (btn) btn.textContent = 'Disconnect';
    await loadMemory();
  };

  window.toggle = function (checkbox) {
    var id   = checkbox.dataset.id;
    var item = checkbox.closest('.action-item');
    var span = item ? item.querySelector('.al') : null;
    if (checkbox.checked) {
      _memory.completed[id] = new Date().toISOString().slice(0, 10);
      if (span) span.classList.add('done');
    } else {
      delete _memory.completed[id];
      if (span) span.classList.remove('done');
    }
    saveMemory();
  };

  window.snoozeItem = function (id, label) {
    _memory.snoozed[id] = label;
    var cb = document.querySelector('[data-id="' + id + '"]');
    if (cb) {
      var item = cb.closest ? cb.closest('.action-item') : cb.parentElement;
      if (item) item.style.display = 'none';
    }
    _addSnoozedEntry(id, label);
    _updateSnoozeCount();
    saveMemory();
  };

  window.unsnoozeItem = function (id) {
    var label = _memory.snoozed[id];
    delete _memory.snoozed[id];
    var li = document.querySelector('[data-snooze-id="' + id + '"]');
    if (li) li.remove();
    var cb = document.querySelector('[data-id="' + id + '"]');
    if (cb) {
      var item = cb.closest ? cb.closest('.action-item') : cb.parentElement;
      if (item) item.style.display = '';
    }
    _updateSnoozeCount();
    saveMemory();
  };

  // ── renderBriefing — called by template.html after fetching today.json ────────

  window.renderBriefing = function (data) {
    // Page title + date
    document.title = 'Daily Briefing — ' + data.date;
    var dateEl = $('.date');
    if (dateEl) dateEl.textContent = data.date;

    // Weather
    var weather = $('.weather-bar');
    if (weather) weather.textContent = data.weather;

    // Today at a Glance
    var glance = $('.glance-section');
    if (glance) {
      var html = '';
      if (data.schedule && data.schedule.length) {
        html += '<ul class="timeline">';
        data.schedule.forEach(function (e) {
          html += '<li><strong>' + esc(e.time) + '</strong> — ' + esc(e.label) + '</li>';
        });
        html += '</ul>';
      }
      if (data.focusBlocks && data.focusBlocks.length) {
        html += '<div class="focus-header">Focus Blocks</div>';
        data.focusBlocks.forEach(function (b) {
          html += '<div class="focus-block"><strong>' +
            esc(b.emoji) + ' ' + esc(b.time) +
            '</strong> — ' + esc(b.label) + '</div>';
        });
      }
      glance.innerHTML = html;
    }

    // On the Radar
    var radar = $('.radar-section');
    if (radar) {
      var rhtml = '';
      (data.radar || []).forEach(function (r) {
        rhtml += '<p><strong>' + esc(r.day) + '</strong> — ' +
          r.items.map(esc).join(' · ') + '</p>';
      });
      if (data.radarNote) {
        rhtml += '<p style="color:#888;font-size:0.9em;">' + esc(data.radarNote) + '</p>';
      }
      radar.innerHTML = rhtml;
    }

    // Inbox
    var inbox = $('.inbox-section');
    if (inbox && data.inbox) {
      var ihtml = '';
      if (data.inbox.attention && data.inbox.attention.length) {
        ihtml += '<p><strong>Needs attention:</strong></p><ul>';
        data.inbox.attention.forEach(function (m) {
          ihtml += '<li><strong>' + esc(m.sender) + '</strong> (' +
            esc(m.date) + ') — ' + esc(m.detail) + '</li>';
        });
        ihtml += '</ul>';
      }
      if (data.inbox.lingering && data.inbox.lingering.length) {
        ihtml += '<p><strong>Lingering:</strong></p><ul>';
        data.inbox.lingering.forEach(function (m) {
          ihtml += '<li><strong>' + esc(m.sender) + '</strong> (' +
            esc(m.date) + ') — ' + esc(m.detail) + '</li>';
        });
        ihtml += '</ul>';
      }
      inbox.innerHTML = ihtml;
    }

    // Improvement Idea (field is trusted HTML from Claude — contains <code> tags)
    var impSection = $('.improvement-section');
    if (impSection) {
      if (data.improvement) {
        impSection.innerHTML = data.improvement;
        impSection.closest('section').style.display = '';
      } else {
        impSection.closest('section').style.display = 'none';
      }
    }

    // Action Items
    var actions = $('.actions-section');
    if (actions && data.actionGroups) {
      var ahtml = '';
      data.actionGroups.forEach(function (group) {
        ahtml += '<div class="group-label">' + esc(group.label) + '</div>';
        group.items.forEach(function (item) {
          var checked   = group.done ? ' checked' : '';
          var doneClass = group.done ? ' done' : '';
          ahtml +=
            '<div class="action-item">' +
            '<input type="checkbox" data-id="' + esc(item.id) + '"' + checked +
            ' onchange="toggle(this)">' +
            '<span class="al' + doneClass + '">' + esc(item.label) + '</span>' +
            '<button class="snooze-btn" onclick="snoozeItem(\'' +
            jsq(item.id) + '\',\'' + jsq(item.label) + '\')">⏸</button>' +
            '</div>';
        });
      });
      // Snooze drawer
      ahtml +=
        '<details>' +
        '<summary>Snoozed (<span id="snooze-count">0</span>)</summary>' +
        '<ul id="snoozed-list"></ul>' +
        '</details>';
      actions.innerHTML = ahtml;
    }

    // Apply memory now that DOM is populated
    applyMemory();
  };

  // ── Init ─────────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', async function () {
    _token = sessionStorage.getItem('gh_token');
    if (_token) {
      var btn = $('#mem-btn');
      if (btn) btn.textContent = 'Disconnect';
      await loadMemory();
    }
  });

}());
