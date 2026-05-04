/* ═══════════════════════════════════════════════════════════
   ALIAS – manage_accounts.js
   Handles: create / edit / delete account modals + API calls
═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Notification banner ────────────────────────────────────────────────────
  function showNotif(msg, type = 'success') {
    const banner = document.getElementById('notifBanner');
    banner.textContent = msg;
    banner.className   = type;
    banner.style.display = 'flex';
    setTimeout(() => { banner.style.display = 'none'; }, 4000);
  }

  function showErr(el, msg) {
    el.textContent    = msg;
    el.style.display  = 'block';
  }

  // ── Password visibility toggle ─────────────────────────────────────────────
  function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const isHidden = input.type === 'password';
    input.type     = isHidden ? 'text' : 'password';
    btn.textContent = isHidden ? 'HIDE' : 'SHOW';
  }

  // ── Role hint ──────────────────────────────────────────────────────────────
  const ROLE_HINTS = {
    staff: 'Inventory Staff can view and manage inventory items.',
    admin: 'Admins have full access, including account management.',
  };

  function bindRoleHint() {
    const roleSelect = document.getElementById('c_role');
    const hint       = document.getElementById('roleHint');
    if (!roleSelect || !hint) return;
    roleSelect.addEventListener('change', () => {
      hint.textContent = ROLE_HINTS[roleSelect.value] || '';
    });
  }

  // ── Create modal ───────────────────────────────────────────────────────────
  function openCreateModal() {
    ['c_full_name', 'c_email', 'c_password', 'c_confirm_password']
      .forEach(id => { document.getElementById(id).value = ''; });
    document.getElementById('c_role').value = 'staff';
    document.getElementById('createError').style.display = 'none';
    document.getElementById('createModal').classList.remove('hidden');
  }

  function closeCreateModal() {
    document.getElementById('createModal').classList.add('hidden');
  }

  async function submitCreate() {
    const btn    = document.getElementById('createBtn');
    const errEl  = document.getElementById('createError');
    errEl.style.display = 'none';

    const password  = document.getElementById('c_password').value;
    const confirm   = document.getElementById('c_confirm_password').value;
    const email     = document.getElementById('c_email').value.trim();
    const full_name = document.getElementById('c_full_name').value.trim();
    const role      = document.getElementById('c_role').value;

    if (!email)                 { showErr(errEl, 'Email is required.');                 return; }
    if (!password)              { showErr(errEl, 'Password is required.');              return; }
    if (password !== confirm)   { showErr(errEl, 'Passwords do not match.');            return; }
    if (password.length < 6)    { showErr(errEl, 'Password must be at least 6 characters.'); return; }

    btn.disabled    = true;
    btn.textContent = 'CREATING…';

    try {
      const res  = await apiFetch('/api/users', {
        method: 'POST',
        body: JSON.stringify({ email, password, full_name, role }),
      });
      closeCreateModal();
      showNotif(`Account "${email}" created successfully!`, 'success');
      setTimeout(() => location.reload(), 1200);
    } catch (err) {
      showErr(errEl, err.message || 'Failed to create account.');
    } finally {
      btn.disabled    = false;
      btn.textContent = 'CREATE ACCOUNT';
    }
  }

  // ── Edit modal ─────────────────────────────────────────────────────────────
  function openEditModal(id, email, full_name, role) {
    document.getElementById('e_id').value       = id;
    document.getElementById('e_email').value    = email;
    document.getElementById('e_full_name').value = full_name;
    document.getElementById('e_role').value     = role;
    document.getElementById('e_password').value         = '';
    document.getElementById('e_confirm_password').value = '';
    document.getElementById('editError').style.display  = 'none';
    document.getElementById('editModal').classList.remove('hidden');
  }

  function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
  }

  async function submitEdit() {
    const errEl = document.getElementById('editError');
    errEl.style.display = 'none';

    const id        = document.getElementById('e_id').value;
    const email     = document.getElementById('e_email').value.trim();
    const full_name = document.getElementById('e_full_name').value.trim();
    const role      = document.getElementById('e_role').value;
    const password  = document.getElementById('e_password').value;
    const confirm   = document.getElementById('e_confirm_password').value;

    if (!email)                             { showErr(errEl, 'Email is required.');            return; }
    if (password && password !== confirm)   { showErr(errEl, 'Passwords do not match.');       return; }
    if (password && password.length < 6)   { showErr(errEl, 'Password must be at least 6 characters.'); return; }

    const body = { email, full_name, role };
    if (password) body.password = password;

    try {
      await apiFetch(`/api/users/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      closeEditModal();
      showNotif(`Account "${email}" updated successfully!`, 'success');
      setTimeout(() => location.reload(), 1200);
    } catch (err) {
      showErr(errEl, err.message || 'Update failed.');
    }
  }

  // ── Delete ─────────────────────────────────────────────────────────────────
  async function deleteAccount(id, email) {
    if (!confirm(`Delete account "${email}"?\nThis action cannot be undone.`)) return;
    try {
      await apiFetch(`/api/users/${id}`, { method: 'DELETE' });
      showNotif(`Account "${email}" deleted.`, 'success');
      setTimeout(() => location.reload(), 1000);
    } catch (err) {
      showNotif(err.message || 'Delete failed.', 'error');
    }
  }

  // ── Handlers for data-attributes ───────────────────────────────────────────
  function handleEditAccount(el) {
    const { id, email, fullname, role } = el.dataset;
    openEditModal(id, email, fullname, role);
  }

  function handleDeleteAccount(el) {
    const { id, email } = el.dataset;
    deleteAccount(id, email);
  }

  // ── Shared fetch helper ────────────────────────────────────────────────────
  async function apiFetch(url, options = {}) {
    const res  = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const text = await res.text();
    let data = {};
    try { data = JSON.parse(text); } catch (_) { /* non-JSON body */ }
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  // ── Modal backdrop close ───────────────────────────────────────────────────
  function bindModalBackdropClose() {
    ['createModal', 'editModal'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('click', e => {
          if (e.target === el) el.classList.add('hidden');
        });
      }
    });
  }

  // ── Expose to HTML inline onclick attributes ───────────────────────────────
  window.handleEditAccount   = handleEditAccount;
  window.handleDeleteAccount = handleDeleteAccount;
  window.openCreateModal  = openCreateModal;
  window.closeCreateModal = closeCreateModal;
  window.submitCreate     = submitCreate;
  window.openEditModal    = openEditModal;
  window.closeEditModal   = closeEditModal;
  window.submitEdit       = submitEdit;
  window.deleteAccount    = deleteAccount;
  window.togglePassword   = togglePassword;

  // ── Init ───────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    bindRoleHint();
    bindModalBackdropClose();
  });

})();
