/* ═══════════════════════════════════════════════
   ALIAS – inventory.js
   Handles: category tabs, subcategory tabs, table
   rendering, expand/detail, create, edit, delete
═══════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── State ────────────────────────────────────
  let categories     = [];
  let subcategories  = [];
  let items          = [];

  let activeCatIndex = 0;   // index into categories[]
  let activeSubId    = null; // null = all subcats
  let expandedItemId = null; // row currently expanded
  let editingItemId  = null; // row in edit-save mode
  let deleteTargetId = null;

  // ── DOM refs ─────────────────────────────────
  const catLabel       = document.getElementById('catLabel');
  const catPrev        = document.getElementById('catPrev');
  const catNext        = document.getElementById('catNext');
  const subTabs        = document.getElementById('subcategoryTabs');
  const tableBody      = document.getElementById('inventoryBody');
  const searchInput    = document.getElementById('searchInput');
  const sortSelect     = document.getElementById('sortSelect');
  const btnCreateNew   = document.getElementById('btnCreateNew');
  const createModal    = document.getElementById('createModal');
  const createBack     = document.getElementById('createBack');
  const createNext     = document.getElementById('createNext');
  const createCategory = document.getElementById('createCategory');
  const createSubcat   = document.getElementById('createSubcategory');
  const createQty      = document.getElementById('createQuantity');
  const createName     = document.getElementById('createName');
  const deleteModal    = document.getElementById('deleteModal');
  const deleteCancelBtn= document.getElementById('deleteCancelBtn');
  const deleteConfirmBtn=document.getElementById('deleteConfirmBtn');
  const toast          = document.getElementById('toast');

  // ── Init ─────────────────────────────────────
  async function init() {
    await loadCategories();
    await loadSubcategories();
    renderCategoryBar();
    await loadItems();
    bindEvents();
  }

  // ── API helpers ──────────────────────────────
  async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.description || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async function loadCategories() {
    categories = await apiFetch('/api/categories');
  }

  async function loadSubcategories() {
    subcategories = await apiFetch('/api/subcategories');
  }

  async function loadItems() {
    const cat = categories[activeCatIndex];
    const params = new URLSearchParams();
    if (cat)          params.set('category_id', cat.id);
    if (activeSubId)  params.set('subcategory_id', activeSubId);
    const search = searchInput.value.trim();
    if (search)       params.set('search', search);
    params.set('sort', sortSelect.value);

    items = await apiFetch(`/api/inventory?${params}`);
    renderTable();
  }

  // ── Category Bar ─────────────────────────────
  function renderCategoryBar() {
    if (!categories.length) return;
    const cat = categories[activeCatIndex];
    catLabel.textContent = cat ? cat.name : 'Category';

    // Subcategory tabs for this category
    const subs = subcategories.filter(s => s.category_id === cat.id);
    subTabs.innerHTML = '';
    subs.forEach(s => {
      const btn = document.createElement('button');
      btn.className = 'sub-tab' + (activeSubId === s.id ? ' active' : '');
      btn.textContent = s.name;
      btn.dataset.id = s.id;
      btn.addEventListener('click', () => {
        activeSubId = activeSubId === s.id ? null : s.id;
        renderCategoryBar();
        loadItems();
      });
      subTabs.appendChild(btn);
    });
  }

  catPrev.addEventListener('click', () => {
    activeCatIndex = (activeCatIndex - 1 + categories.length) % categories.length;
    activeSubId = null;
    renderCategoryBar();
    loadItems();
  });
  catNext.addEventListener('click', () => {
    activeCatIndex = (activeCatIndex + 1) % categories.length;
    activeSubId = null;
    renderCategoryBar();
    loadItems();
  });

  // ── Table ─────────────────────────────────────
  function renderTable() {
    tableBody.innerHTML = '';
    if (!items.length) {
      tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--muted)">No items found.</td></tr>';
      return;
    }
    items.forEach(item => {
      const tr = buildItemRow(item);
      tableBody.appendChild(tr);

      // If this row is expanded, append detail row below
      if (expandedItemId === item.id) {
        const detailTr = buildDetailRow(item, editingItemId === item.id);
        tableBody.appendChild(detailTr);
      }
    });
  }

  function buildItemRow(item) {
    const tr = document.createElement('tr');
    tr.dataset.id = item.id;

    const isExpanded = expandedItemId === item.id;
    const chevron = isExpanded ? '&#x2303;' : '&#x2304;';

    tr.innerHTML = `
      <td class="td-category">${escHtml(item.category_name)}</td>
      <td class="td-subcategory">${escHtml(item.subcategory_name)}</td>
      <td class="td-name">${escHtml(item.name)}</td>
      <td class="td-date">${escHtml(item.date_created)}</td>
      <td class="td-date">${escHtml(item.date_updated)}</td>
      <td>
        <div class="row-actions">
          <span class="td-qty">${item.quantity}</span>
          <button class="btn-expand" title="Details">${chevron}</button>
          <div style="position:relative">
            <button class="btn-kebab" title="Options">&#8942;</button>
          </div>
        </div>
      </td>
      <td></td>
    `;

    tr.querySelector('.btn-expand').addEventListener('click', () => toggleExpand(item.id));
    tr.querySelector('.btn-kebab').addEventListener('click', (e) => {
      e.stopPropagation();
      showKebab(e.currentTarget, item);
    });

    return tr;
  }

  function buildDetailRow(item, isEditing) {
    const tr = document.createElement('tr');
    tr.classList.add('detail-row');
    tr.dataset.detailFor = item.id;

    const fields = [
      { label: 'ARTICLE',                  key: 'article' },
      { label: 'STOCK NUMBER',             key: 'stock_number' },
      { label: 'UNIT OF MEASURE',          key: 'unit_of_measure' },
      { label: 'UNIT VALUE',               key: 'unit_value' },
      { label: 'BALANCE PER CARD (QUANTITY)', key: 'balance_per_card' },
      { label: 'ON HAND PER COUNT (QUANTITY)',key: 'on_hand_per_count' },
      { label: 'SHORTAGE (QUANTITY)',      key: 'shortage_quantity' },
      { label: 'OVERAGE (VALUE)',          key: 'overage_value' },
    ];

    const fieldRows = fields.map(f => {
      const val = item[f.key] != null ? item[f.key] : '';
      if (isEditing) {
        return `
          <div class="detail-field">
            <span class="df-label">${f.label}</span>
            <span class="df-line"></span>
            <input class="df-input" data-key="${f.key}" value="${escHtml(String(val))}" />
          </div>`;
      }
      return `
        <div class="detail-field">
          <span class="df-label">${f.label}</span>
          <span class="df-line"></span>
          <span class="df-value">${escHtml(String(val))}</span>
        </div>`;
    }).join('');

    const remarksContent = isEditing
      ? `<textarea class="df-input" data-key="remarks" rows="2">${escHtml(item.remarks || '')}</textarea>`
      : `<div class="remarks-box">${escHtml(item.remarks || '')}</div>`;

    const actions = isEditing
      ? `<button class="btn-save" id="saveBtn-${item.id}">Save</button>
         <button class="btn-back" id="cancelEditBtn-${item.id}">Back</button>`
      : (/* view mode: delete button shown when opened via Delete Item flow */ '');

    const deleteBtn = (!isEditing && editingItemId === null)
      ? '' : '';

    tr.innerHTML = `
      <td colspan="7">
        <div class="detail-panel">
          <div class="detail-heading">DETAILS</div>
          <div class="detail-fields" id="detailFields-${item.id}">
            ${fieldRows}
            <div class="detail-field remarks-area">
              <span class="df-label">REMARKS</span>
              ${remarksContent}
            </div>
          </div>
          <div class="detail-panel-actions">${actions}</div>
        </div>
      </td>
    `;

    if (isEditing) {
      tr.querySelector(`#saveBtn-${item.id}`).addEventListener('click', () => saveEdit(item.id, tr));
      tr.querySelector(`#cancelEditBtn-${item.id}`).addEventListener('click', () => {
        editingItemId = null;
        renderTable();
      });
    }

    return tr;
  }

  function toggleExpand(itemId) {
    if (expandedItemId === itemId) {
      expandedItemId = null;
      editingItemId  = null;
    } else {
      expandedItemId = itemId;
      editingItemId  = null;
    }
    renderTable();
  }

  // ── Kebab menu ────────────────────────────────
  function showKebab(btn, item) {
    // Remove any existing kebab
    document.querySelectorAll('.kebab-menu').forEach(el => el.remove());

    const menu = document.createElement('div');
    menu.className = 'kebab-menu';
    menu.innerHTML = `
      <button data-action="edit">Edit Item</button>
      <button data-action="delete" class="danger">Delete Item</button>
    `;

    menu.querySelector('[data-action="edit"]').addEventListener('click', () => {
      menu.remove();
      openEdit(item.id);
    });
    menu.querySelector('[data-action="delete"]').addEventListener('click', () => {
      menu.remove();
      openDeleteConfirm(item.id, item.name);
    });

    btn.parentElement.appendChild(menu);

    // Close on outside click
    setTimeout(() => {
      document.addEventListener('click', function close(e) {
        if (!menu.contains(e.target)) {
          menu.remove();
          document.removeEventListener('click', close);
        }
      });
    }, 0);
  }

  // ── Edit ──────────────────────────────────────
  function openEdit(itemId) {
    expandedItemId = itemId;
    editingItemId  = itemId;
    renderTable();
    // Scroll to detail
    const el = document.querySelector(`[data-detail-for="${itemId}"]`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  async function saveEdit(itemId, detailTr) {
    const inputs = detailTr.querySelectorAll('.df-input');
    const payload = {};
    inputs.forEach(inp => {
      const key = inp.dataset.key;
      const val = inp.value.trim();
      payload[key] = val === '' ? null : val;
    });

    try {
      await apiFetch(`/api/inventory/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      editingItemId  = null;
      expandedItemId = null;
      await loadItems();
      showToast('Item updated successfully.', 'success');
    } catch (e) {
      showToast('Error: ' + e.message, 'error');
    }
  }

  // ── Delete ────────────────────────────────────
  function openDeleteConfirm(itemId, itemName) {
    deleteTargetId = itemId;
    document.getElementById('deleteMsg').textContent =
      `Are you sure you want to delete "${itemName}"?`;
    deleteModal.classList.remove('hidden');
  }

  deleteCancelBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
    deleteTargetId = null;
  });

  deleteConfirmBtn.addEventListener('click', async () => {
    if (!deleteTargetId) return;
    deleteModal.classList.add('hidden');
    try {
      await apiFetch(`/api/inventory/${deleteTargetId}`, { method: 'DELETE' });
      expandedItemId = null;
      editingItemId  = null;
      deleteTargetId = null;
      await loadItems();
      showToast('Item deleted.', 'success');
    } catch (e) {
      showToast('Error: ' + e.message, 'error');
    }
  });

  // ── Create New Item ───────────────────────────
  btnCreateNew.addEventListener('click', () => {
    populateCreateDropdowns();
    createModal.classList.remove('hidden');
  });
  createBack.addEventListener('click', () => createModal.classList.add('hidden'));

  function populateCreateDropdowns() {
    createCategory.innerHTML = '<option value="">Category</option>';
    categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id; opt.textContent = c.name;
      createCategory.appendChild(opt);
    });
    createSubcat.innerHTML = '<option value="">Subcategory</option>';
  }

  createCategory.addEventListener('change', () => {
    const catId = parseInt(createCategory.value);
    createSubcat.innerHTML = '<option value="">Subcategory</option>';
    subcategories
      .filter(s => s.category_id === catId)
      .forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id; opt.textContent = s.name;
        createSubcat.appendChild(opt);
      });
  });

  createNext.addEventListener('click', async () => {
    const catId  = parseInt(createCategory.value);
    const subId  = parseInt(createSubcat.value);
    const qty    = parseInt(createQty.value) || 0;
    const name   = createName.value.trim();

    if (!catId || !subId || !name) {
      showToast('Please fill in Category, Subcategory, and Name.', 'error');
      return;
    }

    try {
      const newItem = await apiFetch('/api/inventory', {
        method: 'POST',
        body: JSON.stringify({ category_id: catId, subcategory_id: subId, quantity: qty, name })
      });
      createModal.classList.add('hidden');
      createCategory.value = '';
      createSubcat.innerHTML = '<option value="">Subcategory</option>';
      createQty.value = '';
      createName.value = '';

      // Open in edit mode so user can fill full details (continuation screen)
      await loadItems();
      expandedItemId = newItem.id;
      editingItemId  = newItem.id;
      renderTable();
      showToast('Item created! Fill in the details below.', 'success');
      const el = document.querySelector(`[data-detail-for="${newItem.id}"]`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
      showToast('Error: ' + e.message, 'error');
    }
  });

  // ── Search & Sort ─────────────────────────────
  let searchTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadItems, 300);
  });
  sortSelect.addEventListener('change', loadItems);

  // ── Utility ───────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function showToast(msg, type = '') {
    toast.textContent = msg;
    toast.className = 'toast' + (type ? ' ' + type : '');
    setTimeout(() => toast.classList.add('hidden'), 3000);
  }

  function bindEvents() {
    // Close kebab on table scroll
    document.addEventListener('scroll', () => {
      document.querySelectorAll('.kebab-menu').forEach(el => el.remove());
    }, { passive: true });
  }

  // ── Start ─────────────────────────────────────
  init().catch(console.error);

})();
