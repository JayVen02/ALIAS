/* ═══════════════════════════════════════════════
   ALIAS – inventory.js
   Handles: category tabs, subcategory tabs, table
   rendering, expand/detail, create, edit, delete
═══════════════════════════════════════════════ */

(function () {
  'use strict';

  window.initInventory = async function () {
    // ── State ────────────────────────────────────
    let categories = [];
    let subcategories = [];
    let items = [];

    let activeCatId = null;
    let activeSubId = null;
    let expandedItemId = null;
    let editingItemId = null;
    let deleteTargetId = null;

    // ── DOM refs ─────────────────────────────────
    const categorySelect = document.getElementById('categorySelect');
    const subcategorySelect = document.getElementById('subcategorySelect');
    const tableBody = document.getElementById('inventoryBody');
    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');
    const btnCreateNew = document.getElementById('btnCreateNew');
    const createModal = document.getElementById('createModal');
    const createBack = document.getElementById('createBack');
    const createNext = document.getElementById('createNext');
    const createCategory = document.getElementById('createCategory');
    const createSubcat = document.getElementById('createSubcategory');
    const createQty = document.getElementById('createQuantity');
    const createName = document.getElementById('createName');
    const deleteModal = document.getElementById('deleteModal');
    const deleteCancelBtn = document.getElementById('deleteCancelBtn');
    const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
    const successModal = document.getElementById('successModal');
    const successTitle = document.getElementById('successTitle');
    const successContBtn = document.getElementById('successContinueBtn');
    const toast = document.getElementById('toast');

    if (!categorySelect) return;

    // ── API helpers ──────────────────────────────
    async function apiFetch(url, options = {}) {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || data.description || `HTTP ${res.status}`);
      }
      return data;
    }

    async function loadCategories() {
      const resp = await apiFetch('/api/categories');
      categories = resp.categories || [];
    }

    async function loadSubcategories() {
      const resp = await apiFetch('/api/subcategories');
      subcategories = resp.subcategories || [];
    }

    async function loadItems() {
      const params = new URLSearchParams();
      if (activeCatId) params.set('category_id', activeCatId);
      if (activeSubId) params.set('subcategory_id', activeSubId);
      const search = searchInput.value.trim();
      if (search) params.set('search', search);
      params.set('sort', sortSelect.value);

      const resp = await apiFetch(`/api/inventory?${params}`);
      items = resp.items || [];
      renderTable();
    }

    // ── Category & Subcategory Filters ───────────
    function renderFilters() {
      if (!categories.length) return;

      // Populate Category Dropdown if not already done
      if (categorySelect.options.length <= 1) {
        categories.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c.id;
          opt.textContent = c.name;
          categorySelect.appendChild(opt);
        });
      }

      // Populate Subcategory Dropdown based on active category
      subcategorySelect.innerHTML = '<option value="">All Subcategories</option>';
      if (activeCatId) {
        const subs = subcategories.filter(s => s.category_id == activeCatId);
        subs.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = s.name;
          subcategorySelect.appendChild(opt);
        });
      }

      categorySelect.value = activeCatId || '';
      subcategorySelect.value = activeSubId || '';
    }

    categorySelect.addEventListener('change', () => {
      activeCatId = categorySelect.value || null;
      activeSubId = null;
      renderFilters();
      loadItems();
    });

    subcategorySelect.addEventListener('change', () => {
      activeSubId = subcategorySelect.value || null;
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
      const chevron = isExpanded ? '&#9652;' : '&#9662;';

      tr.innerHTML = `
        <td class="td-category">${escHtml(item.category_name)}</td>
        <td class="td-subcategory">${escHtml(item.subcategory_name)}</td>
        <td class="td-name">${escHtml(item.name)}</td>
        <td class="td-date">${escHtml(item.date_created)}</td>
        <td class="td-date">${escHtml(item.date_updated)}</td>
        <td>
          <div class="row-actions">
            <span class="td-qty ${item.quantity < 10 ? 'qty-red' : (item.quantity < 30 ? 'qty-yellow' : 'qty-green')}">${item.quantity}</span>
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
        { label: 'ARTICLE', key: 'article' },
        { label: 'STOCK NUMBER', key: 'stock_number' },
        { label: 'UNIT OF MEASURE', key: 'unit_of_measure' },
        { label: 'UNIT VALUE', key: 'unit_value' },
        { label: 'BALANCE PER CARD (QUANTITY)', key: 'balance_per_card' },
        { label: 'ON HAND PER COUNT (QUANTITY)', key: 'on_hand_per_count' },
        { label: 'SHORTAGE (QUANTITY)', key: 'shortage_quantity' },
        { label: 'OVERAGE (VALUE)', key: 'overage_value' },
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
        : '';

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
        editingItemId = null;
      } else {
        expandedItemId = itemId;
        editingItemId = null;
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
        const close = (e) => {
          if (!menu.contains(e.target)) {
            menu.remove();
            document.removeEventListener('click', close);
          }
        };
        document.addEventListener('click', close);
      }, 0);
    }

    // ── Edit ──────────────────────────────────────
    function openEdit(itemId) {
      expandedItemId = itemId;
      editingItemId = itemId;
      renderTable();
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
        editingItemId = null;
        expandedItemId = null;
        await loadItems();

        successTitle.textContent = 'ITEM EDITED!';
        successModal.classList.remove('hidden');
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
        editingItemId = null;
        deleteTargetId = null;
        await loadItems();

        successTitle.textContent = 'ITEM DELETED!';
        successModal.classList.remove('hidden');
      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });

// ── Create New Item ───────────────────────────
const createConfirmModal = document.getElementById('createConfirmModal');
const createConfirmBtn = document.getElementById('createConfirmBtn');
const createCancelBtn = document.getElementById('createCancelBtn');


let pendingCreateData = null;

btnCreateNew.addEventListener('click', () => {
  populateCreateDropdowns();
  createModal.classList.remove('hidden');
});

createBack.addEventListener('click', () => {
  createModal.classList.add('hidden');
});

function populateCreateDropdowns() {
  createCategory.innerHTML = '<option value="">Category</option>';
  categories.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name;
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
      opt.value = s.id;
      opt.textContent = s.name;
      createSubcat.appendChild(opt);
    });
});

// STEP 1: CLICK CREATE → SHOW CONFIRM
createNext.addEventListener('click', () => {
  const catId = parseInt(createCategory.value);
  const subId = parseInt(createSubcat.value);
  const qty = parseInt(createQty.value) || 0;
  const name = createName.value.trim();


  if (!catId || !subId || !name) {
    showToast('Please fill in Category, Subcategory, and Name.', 'error');
    return;
  }

  if (qty <= 0) {
    showToast('Quantity must be greater than 0.', 'error');
    return;
  }

  pendingCreateData = {
    category_id: catId,
    subcategory_id: subId,
    quantity: qty,
    name
  };

  createConfirmModal.classList.remove('hidden');
});

// STEP 2: CONFIRM → CREATE ITEM
createConfirmBtn.addEventListener('click', async () => {
  if (!pendingCreateData) return;

  createConfirmModal.classList.add('hidden');

  try {
    const newItem = await apiFetch('/api/inventory', {
      method: 'POST',
      body: JSON.stringify(pendingCreateData)
    });

    createModal.classList.add('hidden');
    pendingCreateData = null;

    createCategory.value = '';
    createSubcat.innerHTML = '<option value="">Subcategory</option>';
    createQty.value = '';
    createName.value = '';

    await loadItems();
    expandedItemId = newItem.id;
    editingItemId = newItem.id;
    renderTable();

    successTitle.textContent = 'ITEM CREATED!';
    successModal.classList.remove('hidden');
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
});

// CANCEL CONFIRM
createCancelBtn.addEventListener('click', () => {
  createConfirmModal.classList.add('hidden');

// SUCCESS MODAL CONTINUE BUTTON
const successContBtn = document.getElementById('successContinueBtn');

if (successContBtn) {
  successContBtn.onclick = () => {
    successModal.classList.add('hidden');
  };
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
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function showToast(msg, type = '') {
      toast.textContent = msg;
      toast.className = 'toast' + (type ? ' ' + type : '');
      setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    function bindEvents() {
      document.addEventListener('scroll', () => {
        document.querySelectorAll('.kebab-menu').forEach(el => el.remove());
      }, { passive: true });
    }

    // ── Run Init ─────────────────────────────────
    await loadCategories();
    await loadSubcategories();

    // Default to the first category if none active to ensure subcategories are shown
    if (categories.length > 0 && activeCatId === null) {
      activeCatId = categories[0].id;
    }

    renderFilters();
    await loadItems();
    bindEvents();
  };

})();
