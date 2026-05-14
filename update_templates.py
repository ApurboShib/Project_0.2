import os

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Legal Drafting Assistant - Professional</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      --bg-color: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.7);
      --card-border: rgba(255, 255, 255, 0.1);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #8b5cf6;
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
      --input-bg: rgba(15, 23, 42, 0.6);
      --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);
      --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-color);
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
      background-attachment: fixed;
      color: var(--text-main);
      min-height: 100vh;
      line-height: 1.6;
    }

    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

    /* Glassmorphism Navbar */
    .navbar {
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      position: sticky; top: 0; z-index: 100;
      padding: 16px 0;
    }
    .navbar .container { display: flex; justify-content: space-between; align-items: center; padding: 0 20px; }
    .navbar-brand { font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 12px; background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    .status-badge {
      display: flex; align-items: center; gap: 8px; padding: 6px 14px;
      background: rgba(255, 255, 255, 0.05); border: 1px solid var(--card-border);
      border-radius: 20px; font-size: 13px; font-weight: 500;
      transition: var(--transition);
    }
    .status-badge.active { border-color: rgba(16, 185, 129, 0.5); color: var(--success); box-shadow: 0 0 10px rgba(16,185,129,0.2); }
    .status-badge.inactive { border-color: rgba(239, 68, 68, 0.5); color: var(--danger); }

    /* Header */
    .header {
      text-align: center; padding: 60px 20px; margin-bottom: 40px;
      animation: fadeInDown 0.8s ease-out;
    }
    .header h1 { font-size: 42px; font-weight: 700; margin-bottom: 16px; letter-spacing: -1px; }
    .header p { color: var(--text-muted); font-size: 18px; max-width: 700px; margin: 0 auto; }

    /* Cards */
    .card {
      background: var(--card-bg); backdrop-filter: blur(16px);
      border: 1px solid var(--card-border); border-radius: 16px;
      padding: 32px; transition: var(--transition);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .card:hover { border-color: rgba(139, 92, 246, 0.3); box-shadow: var(--shadow-glow); transform: translateY(-2px); }
    
    .card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; border-bottom: 1px solid var(--card-border); padding-bottom: 16px; }
    .card-header h2 { font-size: 20px; font-weight: 600; color: var(--text-main); }
    .card-header .icon { font-size: 24px; }

    .content-wrapper { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }
    @media (max-width: 900px) { .content-wrapper { grid-template-columns: 1fr; } }

    /* Forms */
    .form-group { margin-bottom: 24px; }
    label { display: block; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 8px; }
    .label-hint { text-transform: none; font-weight: 400; font-size: 12px; opacity: 0.7; margin-left: 8px; }
    
    input[type="file"], input[type="text"], select, textarea {
      width: 100%; padding: 14px 16px; background: var(--input-bg);
      border: 1px solid var(--card-border); border-radius: 8px;
      color: var(--text-main); font-family: 'Inter', sans-serif; font-size: 14px;
      transition: var(--transition); outline: none;
    }
    select { appearance: none; background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e"); background-repeat: no-repeat; background-position: right 12px center; background-size: 16px; }
    
    input[type="file"]::file-selector-button {
      background: var(--primary-gradient); color: white; border: none;
      padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; margin-right: 12px; transition: var(--transition);
    }
    input[type="file"]::file-selector-button:hover { opacity: 0.9; transform: scale(1.02); }
    
    input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2); }
    textarea { resize: vertical; min-height: 120px; background: rgba(15, 23, 42, 0.4); }

    /* Buttons */
    button {
      padding: 14px 24px; border: none; border-radius: 8px; font-family: 'Inter', sans-serif;
      font-weight: 600; font-size: 14px; cursor: pointer; transition: var(--transition);
      display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%;
    }
    .btn-primary { background: var(--primary-gradient); color: white; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); }
    .btn-primary:hover { box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5); transform: translateY(-2px); }
    
    .btn-secondary { background: rgba(255, 255, 255, 0.05); color: var(--text-main); border: 1px solid var(--card-border); margin-bottom: 12px; }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); transform: translateY(-1px); }

    /* Status Items */
    .status-grid { display: flex; flex-direction: column; gap: 12px; margin-bottom: 30px; }
    .status-item {
      display: flex; justify-content: space-between; align-items: center;
      padding: 14px 16px; background: rgba(15, 23, 42, 0.4); border-radius: 8px;
      border-left: 3px solid var(--accent);
    }
    .status-item label { margin: 0; font-size: 11px; }
    .status-item-value { font-weight: 600; font-size: 14px; }
    .status-item-value.active { color: var(--success); }
    .status-item-value.inactive { color: var(--danger); }

    /* Modal */
    .modal-overlay {
      display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(4px); z-index: 2000; overflow-y: auto; padding: 40px 20px;
      opacity: 0; transition: opacity 0.3s ease;
    }
    .modal-overlay.active { display: flex; align-items: flex-start; justify-content: center; opacity: 1; }
    .modal-content {
      background: var(--bg-color); border: 1px solid var(--card-border); border-radius: 16px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); max-width: 900px; width: 100%; padding: 32px;
      transform: translateY(20px); transition: transform 0.3s ease;
    }
    .modal-overlay.active .modal-content { transform: translateY(0); }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 20px; margin-bottom: 24px; }
    .modal-header h2 { font-size: 24px; font-weight: 600; }
    .modal-close { background: rgba(239, 68, 68, 0.1); color: var(--danger); width: auto; padding: 8px 16px; border: 1px solid rgba(239, 68, 68, 0.2); }
    .modal-close:hover { background: rgba(239, 68, 68, 0.2); }

    /* Utilities */
    .loading { display: none; text-align: center; padding: 30px; }
    .loading.active { display: flex; flex-direction: column; align-items: center; gap: 16px; }
    .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--accent); border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }

    .status-msg { padding: 14px 16px; border-radius: 8px; font-size: 14px; margin-top: 16px; display: flex; align-items: center; gap: 10px; border: 1px solid transparent; }
    .status-msg.error { background: rgba(239, 68, 68, 0.1); color: #fca5a5; border-color: rgba(239, 68, 68, 0.3); }
    .status-msg.info { background: rgba(56, 189, 248, 0.1); color: #7dd3fc; border-color: rgba(56, 189, 248, 0.3); }

    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
    table th { text-align: left; padding: 12px; border-bottom: 1px solid var(--card-border); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 12px; }
    table td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    table tr:hover { background: rgba(255,255,255,0.02); }
    .grid-2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }
  </style>
</head>
<body>
  <nav class="navbar">
    <div class="container">
      <div class="navbar-brand">
        <span style="font-size: 26px;">⚖️</span>
        Legal Drafting Assistant
      </div>
      <div class="status-badge" id="apiStatusBadge">
        <span id="apiStatusText">Checking...</span>
      </div>
    </div>
  </nav>

  <div class="container">
    <div class="header">
      <h1>Intelligent Document Processing</h1>
      <p>Transform legal documents into professionally drafted summaries with AI-powered analysis, semantic search, and an intelligent learning engine.</p>
    </div>

    <div class="content-wrapper">
      <div class="card">
        <div class="card-header">
          <span class="icon">📤</span>
          <h2>Upload & Generate</h2>
        </div>

        <form id="processForm" enctype="multipart/form-data">
          <div class="form-group">
            <label for="file">Document File <span class="label-hint">PDF, TXT, MD</span></label>
            <input type="file" id="file" name="file" accept=".pdf,.txt,.md" required />
          </div>

          <div class="form-group">
            <label for="draft_type">Draft Type <span class="label-hint">Output format</span></label>
            <select id="draft_type" name="draft_type" required>
              <option value="">-- Select a Draft Type --</option>
              <option value="case_fact_summary">📋 Case Fact Summary</option>
              <option value="internal_memo">📝 Internal Memo</option>
              <option value="notice_summary">📢 Notice-Related Summary</option>
              <option value="document_checklist">✅ Document Checklist</option>
              <option value="title_review">🏷️ Title Review Summary</option>
            </select>
          </div>

          <div class="form-group">
            <label for="custom_instructions">Custom Instructions <span class="label-hint">(Optional)</span></label>
            <textarea id="custom_instructions" name="custom_instructions" placeholder="E.g., emphasize deadlines, maintain formal tone, focus on obligations..."></textarea>
          </div>

          <button type="submit" class="btn-primary">
            <span>🚀</span> Generate Draft
          </button>

          <div id="processStatus" class="status-msg" style="display: none;"></div>

          <div id="processLoading" class="loading">
            <div class="spinner"></div>
            <p style="color: var(--text-muted); font-size: 14px; font-weight: 500;">Analyzing Document & Generating Draft...</p>
          </div>
        </form>
      </div>

      <div>
        <div class="card" style="margin-bottom: 30px;">
          <div class="card-header">
            <span class="icon">📊</span>
            <h2>System Status</h2>
          </div>
          <div class="status-grid">
            <div class="status-item">
              <label>API Status</label>
              <div class="status-item-value" id="apiStatus">Checking...</div>
            </div>
            <div class="status-item">
              <label>AI Provider (LLM)</label>
              <div class="status-item-value" id="anthropicStatus">Checking...</div>
            </div>
            <div class="status-item">
              <label>Storage Engine</label>
              <div class="status-item-value active">Active</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="icon">⚡</span>
            <h2>Quick Actions</h2>
          </div>
          <button onclick="viewDocuments()" class="btn-secondary">📁 View Processed Documents</button>
          <button onclick="viewDrafts()" class="btn-secondary">📝 View Generated Drafts</button>
          <button onclick="viewRules()" class="btn-secondary">🎯 View Learned Rules</button>
        </div>
      </div>
    </div>
  </div>

  <div id="resultsModal" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-header">
        <h2 id="modalTitle">Results</h2>
        <button type="button" onclick="closeModal()" class="modal-close">✕ Close</button>
      </div>
      <div id="resultsContent"></div>
    </div>
  </div>

  <script>
    async function checkStatus() {
      try {
        const response = await fetch('/api/health');
        const statusBadge = document.getElementById('apiStatusBadge');
        const statusText = document.getElementById('apiStatusText');
        const statusValue = document.getElementById('apiStatus');

        if (response.ok) {
          statusBadge.classList.add('active'); statusBadge.classList.remove('inactive');
          statusText.textContent = '● System Online';
          statusValue.textContent = '✓ Running'; statusValue.classList.add('active');
        } else { throw new Error('API error'); }
      } catch (error) {
        const statusBadge = document.getElementById('apiStatusBadge');
        const statusText = document.getElementById('apiStatusText');
        const statusValue = document.getElementById('apiStatus');
        statusBadge.classList.remove('active'); statusBadge.classList.add('inactive');
        statusText.textContent = '● Offline';
        statusValue.textContent = '✗ Offline'; statusValue.classList.add('inactive');
      }
      const anthropicStatus = document.getElementById('anthropicStatus');
      anthropicStatus.textContent = '{{ anthropic_configured|default(false)|lower }}' === 'true' ? '✓ Configured' : '✗ Not Configured';
      anthropicStatus.classList.add(anthropicStatus.textContent.startsWith('✓') ? 'active' : 'inactive');
    }

    document.getElementById('processForm').addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(event.target);
      const loading = document.getElementById('processLoading');
      const status = document.getElementById('processStatus');

      loading.classList.add('active');
      status.style.display = 'none';

      try {
        const response = await fetch('/process', { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const html = await response.text();
        document.getElementById('resultsContent').innerHTML = html;
        document.getElementById('modalTitle').textContent = 'Draft Generated';
        document.getElementById('resultsModal').classList.add('active');
        event.target.reset();
      } catch (error) {
        status.className = 'status-msg error';
        status.innerHTML = `<span>⚠️</span><span>${error.message}</span>`;
        status.style.display = 'flex';
      } finally {
        loading.classList.remove('active');
      }
    });

    function closeModal() { document.getElementById('resultsModal').classList.remove('active'); }

    async function viewDocuments() {
      try {
        const response = await fetch('/api/documents');
        const data = await response.json();
        const content = formatTable(data, ['filename', 'doc_type', 'total_pages', 'word_count']);
        showModal('📁 Processed Documents', content);
      } catch (error) { showModal('Error', `<p class="status-msg error">⚠️ ${error.message}</p>`); }
    }

    async function viewDrafts() {
      try {
        const response = await fetch('/api/drafts');
        const data = await response.json();
        const content = formatDrafts(data);
        showModal('📝 Generated Drafts', content);
      } catch (error) { showModal('Error', `<p class="status-msg error">⚠️ ${error.message}</p>`); }
    }

    async function viewRules() {
      try {
        const response = await fetch('/api/rules');
        const data = await response.json();
        const content = formatRules(data);
        showModal('🎯 Learned Style Rules', content);
      } catch (error) { showModal('Error', `<p class="status-msg error">⚠️ ${error.message}</p>`); }
    }

    function formatTable(items, columns) {
      if (!items || !items.length) return '<p style="text-align:center; color: var(--text-muted); padding: 20px;">No items found.</p>';
      const headers = columns.map(col => `<th>${col.replace(/_/g, ' ').toUpperCase()}</th>`).join('');
      const rows = items.map(row => `<tr>${columns.map(col => `<td>${row[col] || '—'}</td>`).join('')}</tr>`).join('');
      return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    }

    function formatDrafts(drafts) {
      if (!drafts || !drafts.length) return '<p style="text-align:center; color: var(--text-muted); padding: 20px;">No drafts generated yet.</p>';
      return '<div class="grid-2">' + drafts.map(draft => `
        <div style="background: rgba(15,23,42,0.4); border: 1px solid var(--card-border); padding: 16px; border-radius: 8px;">
          <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-main);">${draft.title}</div>
          <div style="color: var(--text-muted); font-size: 13px;">
            <div>Type: ${draft.draft_type_label}</div>
            <div>Words: ${draft.word_count}</div>
          </div>
        </div>
      `).join('') + '</div>';
    }

    function formatRules(rules) {
      if (!rules || !Object.keys(rules).length) return '<p style="text-align:center; color: var(--text-muted); padding: 20px;">No style rules learned yet.</p>';
      return '<div>' + Object.entries(rules).map(([type, ruleList]) => `
        <div style="margin-bottom: 24px;">
          <div style="font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; margin-bottom: 12px; color: var(--accent);">${type}</div>
          ${ruleList.map(rule => `
            <div style="padding: 12px; margin-bottom: 8px; background: rgba(16,185,129,0.1); border-left: 3px solid var(--success); border-radius: 4px;">
              <div style="color: var(--text-main);">${rule.rule_text}</div>
              <div style="color: var(--text-muted); font-size: 12px; margin-top: 4px;">Frequency: ${rule.frequency}x</div>
            </div>
          `).join('')}
        </div>
      `).join('') + '</div>';
    }

    function showModal(title, content) {
      document.getElementById('modalTitle').textContent = title;
      document.getElementById('resultsContent').innerHTML = content;
      document.getElementById('resultsModal').classList.add('active');
    }

    document.addEventListener('DOMContentLoaded', checkStatus);
  </script>
</body>
</html>
"""

RESULT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Generated Draft - Legal Drafting Assistant</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
      --bg-color: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.7);
      --card-border: rgba(255, 255, 255, 0.1);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #8b5cf6;
      --success: #10b981;
      --danger: #ef4444;
      --input-bg: rgba(15, 23, 42, 0.6);
      --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      line-height: 1.6; padding: 30px 20px;
      /* Remove background image to look clean inside modal or page */
    }
    
    .container { max-width: 1000px; margin: 0 auto; }
    
    .card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 12px; padding: 30px; margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
      animation: slideIn 0.4s ease-out;
    }
    @keyframes slideIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

    .card h2 { font-size: 20px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border); color: #fff; }
    
    .error-card { border-left: 4px solid var(--danger); background: rgba(239,68,68,0.05); }
    .error-message { color: #fca5a5; font-weight: 500; font-size: 16px; }

    .draft-metadata { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-top: 16px; }
    .metadata-item { display: flex; flex-direction: column; gap: 4px; }
    .metadata-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .metadata-value { font-size: 15px; font-weight: 600; color: var(--text-main); }

    .draft-content {
      background: rgba(15, 23, 42, 0.5); padding: 24px; border-radius: 8px;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 13px; line-height: 1.7; white-space: pre-wrap; word-break: break-word;
      border: 1px solid var(--card-border); color: #e2e8f0;
    }

    .evidence-item {
      background: rgba(15, 23, 42, 0.4); border-left: 3px solid var(--accent);
      padding: 16px; margin-bottom: 16px; border-radius: 6px;
    }
    .evidence-badge { background: var(--primary-gradient); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 10px; display: inline-block; }
    .evidence-source { color: var(--text-muted); font-size: 12px; margin-bottom: 10px; }
    .evidence-text { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #cbd5e1; }

    textarea { width: 100%; padding: 16px; background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; color: var(--text-main); font-family: monospace; font-size: 13px; min-height: 200px; resize: vertical; outline: none; transition: var(--transition); margin-bottom: 16px; }
    textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2); }

    button { padding: 12px 24px; border: none; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; transition: var(--transition); display: inline-flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif; }
    .btn-primary { background: var(--primary-gradient); color: white; }
    .btn-primary:hover { box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); transform: translateY(-1px); }
    .btn-secondary { background: rgba(255,255,255,0.05); color: var(--text-main); border: 1px solid var(--card-border); text-decoration: none; }
    .btn-secondary:hover { background: rgba(255,255,255,0.1); }

    .status-msg { padding: 14px 16px; border-radius: 8px; font-size: 14px; margin-top: 16px; display: flex; align-items: center; gap: 10px; }
    .status-msg.success { background: rgba(16,185,129,0.1); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }

    .rule-item { background: rgba(16,185,129,0.05); padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 3px solid var(--success); display: flex; justify-content: space-between; align-items: center; }
    .rule-text { font-size: 13px; color: #e2e8f0; }
    .rule-badge { background: var(--success); color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; }

    .tag { background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 4px; font-size: 12px; border: 1px solid var(--card-border); margin-right: 6px; display: inline-block; margin-bottom: 6px; }
  </style>
</head>
<body>
  <div class="container">
    {% if error %}
      <div class="card error-card">
        <h2>⚠️ Error Processing Document</h2>
        <p class="error-message">{{ error }}</p>
        <p style="color: var(--text-muted); margin-top: 16px; font-size: 14px;">Please check that you have configured your AI API key and try again with a valid document.</p>
        <a href="/" class="btn-secondary" style="margin-top: 20px;">← Back to Upload</a>
      </div>
    {% else %}
      <div class="card">
        <h2><span>📝</span> {{ draft.title }}</h2>
        <div class="draft-metadata">
          <div class="metadata-item">
            <span class="metadata-label">Draft Type</span>
            <span class="metadata-value">{{ draft.draft_type_label }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Word Count</span>
            <span class="metadata-value">{{ draft.word_count }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">Evidence Used</span>
            <span class="metadata-value">{{ draft.evidence_used|length }} sources</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h2><span>📄</span> Generated Draft</h2>
        <div class="draft-content">{{ draft.content }}</div>
      </div>

      <div class="card">
        <h2><span>🔍</span> Evidence & Citations</h2>
        {% if draft.evidence_used %}
          <div>
            {% for evidence in draft.evidence_used %}
              <div class="evidence-item">
                <span class="evidence-badge">Evidence {{ loop.index }}</span>
                <div class="evidence-source">
                  <strong>📁 Source:</strong> {{ evidence.filename }} | 
                  <strong>📄 Page:</strong> {{ evidence.page_num }} | 
                  <strong>📊 Relevance:</strong> {{ (evidence.relevance_score * 100)|int }}%
                </div>
                <div class="evidence-text">{{ evidence.text }}</div>
              </div>
            {% endfor %}
          </div>
        {% else %}
          <p style="color: var(--text-muted); font-size: 14px;">No specific evidence citations in this draft.</p>
        {% endif %}
      </div>

      <div class="card">
        <h2><span>✏️</span> Refine & Learn</h2>
        <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 16px;">
          Edit the draft below. Your edits will be analyzed to extract style rules for future drafts.
        </p>
        <form action="/edits" method="post">
          <input type="hidden" name="draft_id" value="{{ draft.draft_id }}" />
          <textarea name="edited_content" id="edited_content">{{ draft.content }}</textarea>
          <button type="submit" class="btn-primary"><span>💾</span> Save Edits & Learn Preferences</button>
        </form>

        {% if edit_saved %}
          <div class="status-msg success">
            <span>✓</span> <strong>Success!</strong> Your edits have been saved and analyzed.
          </div>
          {% if learned_rules %}
            <div style="margin-top: 20px;">
              <h3 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; color: var(--success);">🎯 Newly Learned Rules</h3>
              {% for rule in learned_rules %}
                <div class="rule-item">
                  <span class="rule-text">{{ rule }}</span>
                  <span class="rule-badge">NEW</span>
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endif %}
      </div>

      <div class="card">
        <h2><span>📋</span> Source Information</h2>
        <div class="draft-metadata" style="margin-bottom: 20px;">
          <div class="metadata-item"><span class="metadata-label">Filename</span><span class="metadata-value">{{ processed.filename }}</span></div>
          <div class="metadata-item"><span class="metadata-label">Type</span><span class="metadata-value">{{ processed.structured.document_type|replace('_', ' ')|title }}</span></div>
          <div class="metadata-item"><span class="metadata-label">Pages</span><span class="metadata-value">{{ processed.total_pages }}</span></div>
        </div>
        
        {% if processed.structured.dates %}
          <div style="margin-bottom: 16px;">
            <div style="font-size: 12px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; font-weight: 600;">📅 Extracted Dates</div>
            <div>{% for date in processed.structured.dates %}<span class="tag">{{ date }}</span>{% endfor %}</div>
          </div>
        {% endif %}
        
        {% if processed.structured.parties %}
          <div>
            <div style="font-size: 12px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; font-weight: 600;">👥 Parties</div>
            <div>{% for party in processed.structured.parties %}<span class="tag">{{ party }}</span>{% endfor %}</div>
          </div>
        {% endif %}
      </div>

      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <a href="/" class="btn-secondary">← Back Home</a>
        <a href="/api/documents" class="btn-secondary">📁 All Documents</a>
        <a href="/api/drafts" class="btn-secondary">📝 All Drafts</a>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

with open("app/templates/index.html", "w") as f:
    f.write(INDEX_HTML)

with open("app/templates/result.html", "w") as f:
    f.write(RESULT_HTML)

print("Templates updated successfully.")
