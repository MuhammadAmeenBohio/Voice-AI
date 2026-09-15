let activeTab = 'patients';
let vapiInstance = null;
let debounceTimeout = null;
let patientsCache = [];

document.addEventListener('DOMContentLoaded', () => {
  loadKPIs();
  loadPatients();
  loadCalls();
  initVapi();
});

function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
  
  if (tab === 'patients') {
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    document.getElementById('tab-patients').classList.add('active');
  } else {
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
    document.getElementById('tab-calls').classList.add('active');
  }
}

function debounceLoad() {
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    loadPatients();
  }, 300);
}

async function loadKPIs() {
  try {
    const rPatients = await fetch('/patients');
    const bPatients = await rPatients.json();
    const countPatients = bPatients.data ? bPatients.data.length : 0;
    document.getElementById('kpi-patients-count').textContent = countPatients;

    const rCalls = await fetch('/calls');
    const bCalls = await rCalls.json();
    const countCalls = bCalls.data ? bCalls.data.length : 0;
    document.getElementById('kpi-calls-count').textContent = countCalls;
  } catch (e) {
    console.error('Failed to load KPIs', e);
  }
}

async function loadPatients() {
  const tbody = document.getElementById('patients-tbody');
  const lastName = document.getElementById('filter-last-name').value.trim();
  const phone = document.getElementById('filter-phone').value.trim();
  const dob = document.getElementById('filter-dob').value.trim();

  const params = new URLSearchParams();
  if (lastName) params.set('last_name', lastName);
  if (phone) params.set('phone_number', phone);
  if (dob) params.set('date_of_birth', dob);

  try {
    const res = await fetch('/patients?' + params.toString());
    const body = await res.json();
    const patients = body.data || [];
    patientsCache = patients;

    if (!patients.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No matching patient records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = patients.map(p => `
      <tr>
        <td>
          <strong>${escapeHtml(p.first_name)} ${escapeHtml(p.last_name)}</strong>
          <div style="font-size: 0.75rem; color: var(--text-dim);">${p.patient_id.slice(0, 8)}...</div>
        </td>
        <td>${p.date_of_birth}</td>
        <td><span class="pill pill-purple">${p.sex}</span></td>
        <td>${formatPhone(p.phone_number)}</td>
        <td>${escapeHtml(p.city)}, ${p.state}</td>
        <td>${p.zip_code}</td>
        <td><span class="pill pill-blue">${p.preferred_language || 'English'}</span></td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${formatDate(p.created_at)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openPatientModal('${p.patient_id}')">Details</button>
          <button class="btn btn-danger btn-sm" onclick="deletePatient('${p.patient_id}')" style="margin-left:4px;">&times;</button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">Error loading patients: ${e.message}</td></tr>`;
  }
}

async function loadCalls() {
  const container = document.getElementById('calls-container');
  try {
    const res = await fetch('/calls');
    const body = await res.json();
    const calls = body.data || [];

    if (!calls.length) {
      container.innerHTML = `<div class="empty-state">No call transcripts recorded yet. When a call completes, its summary and transcript appear here.</div>`;
      return;
    }

    container.innerHTML = calls.map(c => `
      <div class="call-item">
        <div class="call-header">
          <span class="call-caller">Caller: ${c.caller_phone || 'WebRTC Browser Caller'}</span>
          <span class="call-time">${formatDate(c.created_at)}</span>
        </div>
        ${c.summary ? `<div class="call-summary"><strong>Summary:</strong> ${escapeHtml(c.summary)}</div>` : ''}
        <div class="call-transcript">${escapeHtml(c.transcript || 'No transcript text available.')}</div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="empty-state">Error loading calls: ${e.message}</div>`;
  }
}

function openPatientModal(patientId) {
  const p = patientsCache.find(item => item.patient_id === patientId);
  if (!p) return;

  const content = document.getElementById('modal-content');
  content.innerHTML = `
    <div class="modal-grid">
      <div class="field-group">
        <div class="field-label">Full Name</div>
        <div class="field-value"><strong>${escapeHtml(p.first_name)} ${escapeHtml(p.last_name)}</strong></div>
      </div>
      <div class="field-group">
        <div class="field-label">Administrative Sex</div>
        <div class="field-value">${p.sex}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Date of Birth</div>
        <div class="field-value">${p.date_of_birth}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Phone Number</div>
        <div class="field-value">${formatPhone(p.phone_number)}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Email Address</div>
        <div class="field-value">${p.email ? escapeHtml(p.email) : '<em>Not provided</em>'}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Preferred Language</div>
        <div class="field-value">${p.preferred_language || 'English'}</div>
      </div>
      <div class="field-group" style="grid-column: 1 / -1;">
        <div class="field-label">Physical Address</div>
        <div class="field-value">${escapeHtml(p.address_line_1)}${p.address_line_2 ? ', ' + escapeHtml(p.address_line_2) : ''}, ${escapeHtml(p.city)}, ${p.state} ${p.zip_code}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Insurance Provider</div>
        <div class="field-value">${p.insurance_provider ? escapeHtml(p.insurance_provider) : '<em>None</em>'}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Member / Policy ID</div>
        <div class="field-value">${p.insurance_member_id ? escapeHtml(p.insurance_member_id) : '<em>None</em>'}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Emergency Contact</div>
        <div class="field-value">${p.emergency_contact_name ? escapeHtml(p.emergency_contact_name) : '<em>None</em>'}</div>
      </div>
      <div class="field-group">
        <div class="field-label">Emergency Phone</div>
        <div class="field-value">${p.emergency_contact_phone ? formatPhone(p.emergency_contact_phone) : '<em>None</em>'}</div>
      </div>
      <div class="field-group" style="grid-column: 1 / -1; margin-top: 0.5rem; border-top: 1px solid var(--border-color); padding-top: 0.5rem;">
        <div class="field-label">Patient Record UUID</div>
        <div class="field-value" style="font-family: monospace; font-size: 0.8rem; color: var(--accent);">${p.patient_id}</div>
      </div>
    </div>
  `;

  document.getElementById('patient-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('patient-modal').classList.add('hidden');
}

function closeModalOnBackdrop(e) {
  if (e.target.id === 'patient-modal') {
    closeModal();
  }
}

async function deletePatient(patientId) {
  if (!confirm('Are you sure you want to soft-delete this patient record?')) return;
  try {
    const res = await fetch(`/patients/${patientId}`, { method: 'DELETE' });
    if (res.ok) {
      loadPatients();
      loadKPIs();
    } else {
      alert('Delete failed');
    }
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// --- Vapi In-Browser Voice Call Integration --------------------------------

let vapiClient = null;

async function initVapi() {
  try {
    const resp = await fetch('/api/vapi-config');
    const cfg = await resp.json();
    if (!cfg.public_key || !cfg.assistant_id) {
      console.warn('Vapi public key or assistant ID missing from server config.');
      return;
    }

    // Wait up to 5 seconds for vapiSDK to load from CDN
    let attempts = 0;
    const checkInterval = setInterval(() => {
      attempts++;
      if (window.vapiSDK) {
        clearInterval(checkInterval);
        try {
          vapiClient = window.vapiSDK.run({
            apiKey: cfg.public_key,
            assistant: cfg.assistant_id,
            config: {
              position: "bottom-right",
              offset: "40px",
              width: "60px",
              height: "60px",
            }
          });

          let liveWebTranscript = [];

          vapiClient.on('call-start', () => {
            console.log('Call started');
            liveWebTranscript = [];
            document.getElementById('btn-start-call').classList.add('hidden');
            document.getElementById('btn-end-call').classList.remove('hidden');
            document.getElementById('call-pulse').classList.remove('hidden');
            document.getElementById('call-status-text').textContent = 'Connected! Speaking with Muhammad...';
          });

          vapiClient.on('call-end', async () => {
            console.log('Call ended');
            document.getElementById('btn-start-call').classList.remove('hidden');
            document.getElementById('btn-end-call').classList.add('hidden');
            document.getElementById('call-pulse').classList.add('hidden');
            document.getElementById('call-status-text').textContent = 'Call ended. Syncing records to database...';

            if (liveWebTranscript.length > 0) {
              try {
                await fetch('/vapi/webhook', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    message: {
                      type: 'end-of-call-report',
                      call: { id: 'web-' + Date.now(), customer: { number: 'In-Browser Caller' } },
                      artifact: { transcript: liveWebTranscript.join('\n') },
                      summary: 'WebRTC voice intake completed with Muhammad.'
                    }
                  })
                });
              } catch (e) {
                console.warn('Call report sync error:', e);
              }
            }

            setTimeout(() => {
              loadPatients();
              loadCalls();
              loadKPIs();
              document.getElementById('call-status-text').textContent = 'Patient records and transcripts updated!';
            }, 1000);
          });

          vapiClient.on('speech-start', () => {
            document.getElementById('call-status-text').textContent = 'Muhammad is speaking...';
          });

          vapiClient.on('speech-end', () => {
            document.getElementById('call-status-text').textContent = 'Muhammad is listening to you...';
          });

          // Intercept tool-calls and transcripts directly over WebRTC
          vapiClient.on('message', async (msg) => {
            console.log('Vapi Web event:', msg);

            if (msg.type === 'transcript' && msg.transcript) {
              const speaker = msg.role === 'assistant' ? 'Muhammad: ' : 'Caller: ';
              liveWebTranscript.push(speaker + msg.transcript);
            }

            if (msg.type === 'tool-calls' && msg.toolCallList) {
              document.getElementById('call-status-text').textContent = 'Processing demographic intake...';
              try {
                const resp = await fetch('/vapi/webhook', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ message: msg })
                });
                const data = await resp.json();
                console.log('Tool execution synced to SQLite:', data);

                // Send tool results back to Muhammad over WebRTC so the call continues!
                if (data.results && data.results.length > 0) {
                  vapiClient.send({
                    type: 'tool-results',
                    toolWithResults: data.results
                  });
                }

                // Immediately refresh table and KPIs
                loadPatients();
                loadKPIs();
              } catch (err) {
                console.error('Failed to sync tool call locally:', err);
              }
            }
          });

          vapiClient.on('error', (e) => {
            console.error('Vapi Web call error:', e);
            document.getElementById('call-status-text').textContent = 'Error: ' + (e.message || JSON.stringify(e));
            document.getElementById('btn-start-call').classList.remove('hidden');
            document.getElementById('btn-end-call').classList.add('hidden');
            document.getElementById('call-pulse').classList.add('hidden');
          });
        } catch (initErr) {
          console.error('Failed to init vapiSDK:', initErr);
        }
      } else if (attempts > 20) {
        clearInterval(checkInterval);
        console.warn('Vapi Web SDK CDN timed out.');
      }
    }, 250);
  } catch (err) {
    console.error('Config fetch failed:', err);
  }
}

async function startWebCall() {
  const btnStart = document.getElementById('btn-start-call');
  const btnEnd = document.getElementById('btn-end-call');
  const statusText = document.getElementById('call-status-text');
  const pulse = document.getElementById('call-pulse');

  statusText.textContent = 'Requesting mic access & connecting...';
  pulse.classList.remove('hidden');

  try {
    const resp = await fetch('/api/vapi-config');
    const cfg = await resp.json();

    if (!cfg.public_key || !cfg.assistant_id) {
      statusText.innerHTML = `Voice assistant ready! Set <code>VAPI_PUBLIC_KEY</code> in .env to connect live.`;
      return;
    }

    if (vapiClient && typeof vapiClient.start === 'function') {
      vapiClient.start(cfg.assistant_id);
    } else if (window.vapiSDK) {
      vapiClient = window.vapiSDK.run({
        apiKey: cfg.public_key,
        assistant: cfg.assistant_id,
      });
      vapiClient.start(cfg.assistant_id);
    } else {
      statusText.textContent = 'Loading voice SDK, please try again in 3 seconds...';
    }
  } catch (err) {
    statusText.textContent = 'Connecting error: ' + err.message;
  }
}

function endWebCall() {
  if (vapiClient && typeof vapiClient.stop === 'function') {
    vapiClient.stop();
  }
  document.getElementById('btn-start-call').classList.remove('hidden');
  document.getElementById('btn-end-call').classList.add('hidden');
  document.getElementById('call-pulse').classList.add('hidden');
  document.getElementById('call-status-text').textContent = 'Call ended.';
  setTimeout(() => {
    loadPatients();
    loadCalls();
    loadKPIs();
  }, 1000);
}

// Helpers
function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatPhone(digits) {
  if (!digits || digits.length !== 10) return digits || '';
  return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
