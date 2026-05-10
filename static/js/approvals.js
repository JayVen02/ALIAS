/* ═══════════════════════════════════════════════
   ALIAS – approvals.js
   Admin: approve / reject inventory change requests
═══════════════════════════════════════════════ */
'use strict';

(function () {

  // ── DOM refs ─────────────────────────────────
  const tabs          = document.querySelectorAll('.appr-tab');
  const rows          = document.querySelectorAll('.appr-row');
  const payloadModal  = document.getElementById('payloadModal');
  const payloadBody   = document.getElementById('payloadBody');
  const payloadClose  = document.getElementById('payloadClose');
  const reviewModal   = document.getElementById('reviewModal');
  const reviewTitle   = document.getElementById('reviewTitle');
  const reviewNote    = document.getElementById('reviewNote');
  const reviewCancel  = document.getElementById('reviewCancel');
  const reviewConfirm = document.getElementById('reviewConfirm');
  const toast         = document.getElementById('apprToast');

  let pendingAction  = null; // { id, type: 'approve'|'reject' }

  // ── Tab filtering ─────────────────────────────
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const filter = tab.dataset.filter;
      rows.forEach(row => {
        const status = row.dataset.status;
        const show = filter === 'all' || status === filter;
        row.style.display = show ? '' : 'none';
      });
    });
  });

  // ── View Payload Details ──────────────────────
  document.querySelectorAll('.btn-view-payload').forEach(btn => {
    btn.addEventListener('click', () => {
      const raw    = btn.dataset.payload || '{}';
      const action = btn.dataset.action  || '';
      let parsed;
      try { parsed = JSON.parse(raw); } catch { parsed = {}; }
      payloadBody.innerHTML = buildPayloadHtml(action, parsed);
      payloadModal.classList.remove('hidden');
    });
  });

  payloadClose.addEventListener('click', () => payloadModal.classList.add('hidden'));
  payloadModal.addEventListener('click', e => {
    if (e.target === payloadModal) payloadModal.classList.add('hidden');
  });

  function buildPayloadHtml(action, payload) {
    const labels = {
      name:           'Item Name',
      category_id:    'Category ID',
      subcategory_id: 'Subcategory ID',
      stock_number:   'Stock Number',
      quantity:       'Quantity',
      article:        'Article',
      unit_of_measure:'Unit of Measure',
      unit_value:     'Unit Value',
      remarks:        'Remarks',
    };
    let html = `<div style="margin-bottom:0.8rem; color:var(--text-muted); font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;">Action: ${escHtml(action)}</div>`;
    for (const [k, v] of Object.entries(payload)) {
      if (v === null || v === undefined || v === '') continue;
      const label = labels[k] || k;
      html += `<div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px dashed #e2e8f0;">
        <span style="color:var(--text-muted); font-size:0.82rem;">${escHtml(label)}</span>
        <span style="font-weight:700;">${escHtml(String(v))}</span>
      </div>`;
    }
    return html || '<em style="color:var(--text-muted);">No details available.</em>';
  }

  // ── Approve / Reject buttons ──────────────────
  document.querySelectorAll('.btn-approve').forEach(btn => {
    btn.addEventListener('click', () => openReview(btn.dataset.id, 'approve'));
  });

  document.querySelectorAll('.btn-reject').forEach(btn => {
    btn.addEventListener('click', () => openReview(btn.dataset.id, 'reject'));
  });

  function openReview(id, type) {
    pendingAction = { id, type };
    reviewNote.value = '';
    reviewTitle.textContent = type === 'approve'
      ? '✓ Approve this request?'
      : '✕ Reject this request?';
    reviewConfirm.textContent  = type === 'approve' ? 'Approve' : 'Reject';
    reviewConfirm.style.background = type === 'approve' ? '#27ae60' : 'var(--danger)';
    reviewModal.classList.remove('hidden');
  }

  reviewCancel.addEventListener('click', () => {
    reviewModal.classList.add('hidden');
    pendingAction = null;
  });

  reviewModal.addEventListener('click', e => {
    if (e.target === reviewModal) {
      reviewModal.classList.add('hidden');
      pendingAction = null;
    }
  });

  reviewConfirm.addEventListener('click', async () => {
    if (!pendingAction) return;
    const { id, type } = pendingAction;
    const note = reviewNote.value.trim() || null;
    reviewModal.classList.add('hidden');

    const endpoint = `/api/requests/${id}/${type}`;
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_note: note }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

      showToast(data.message || 'Done!', 'success');
      // Reload after short delay so user sees the toast
      setTimeout(() => location.reload(), 1200);
    } catch (e) {
      showToast('Error: ' + e.message, 'error');
    }
    pendingAction = null;
  });

  // ── Utility ───────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function showToast(msg, type = '') {
    toast.textContent = msg;
    toast.className = 'toast' + (type ? ' ' + type : '');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3500);
  }

})();
