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
    const createStockNumber = document.getElementById('createStockNumber');
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
            <span class="td-qty ${item.quantity < 10 ? 'qty-red' : (item.quantity < 30 ? 'qty-yellow' : 'qty-green')}">${escHtml(item.stock_number || 0)}</span>
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
        { label: 'QUANTITY', key: 'quantity' },
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
              <input class="df-input" data-key="${f.key}" value="${escHtml(String(val))}" ${f.key === 'quantity' ? 'readonly style="background: #f0f0f0; opacity: 0.7;"' : ''} />
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
        const stockInp = tr.querySelector('.df-input[data-key="stock_number"]');
        const qtyInp = tr.querySelector('.df-input[data-key="quantity"]');
        if (stockInp && qtyInp) {
          stockInp.addEventListener('input', () => {
            const val = parseInt(stockInp.value) || 0;
            qtyInp.value = val;
          });
        }

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
        const res = await apiFetch(`/api/inventory/${itemId}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        editingItemId = null;
        expandedItemId = null;

        if (res.pending) {
          successTitle.textContent = 'EDIT REQUEST SUBMITTED!';
          successModal.querySelector('p.pending-note') && successModal.querySelector('p.pending-note').remove();
          const note = document.createElement('p');
          note.className = 'pending-note';
          note.style.cssText = 'color:#f39c12; font-size:0.82rem; font-weight:700; margin-bottom:1rem;';
          note.textContent = 'Awaiting admin approval before changes appear.';
          successModal.querySelector('.modal-content').insertBefore(note, successModal.querySelector('#successContinueBtn'));
        } else {
          successTitle.textContent = 'ITEM EDITED!';
          successModal.querySelectorAll('.pending-note').forEach(el => el.remove());
          await loadItems();
        }
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
        const res = await apiFetch(`/api/inventory/${deleteTargetId}`, { method: 'DELETE', body: JSON.stringify({}) });
        expandedItemId = null;
        editingItemId = null;
        deleteTargetId = null;

        if (res.pending) {
          successTitle.textContent = 'DELETE REQUEST SUBMITTED!';
          successModal.querySelectorAll('.pending-note').forEach(el => el.remove());
          const note = document.createElement('p');
          note.className = 'pending-note';
          note.style.cssText = 'color:#f39c12; font-size:0.82rem; font-weight:700; margin-bottom:1rem;';
          note.textContent = 'Awaiting admin approval before item is removed.';
          successModal.querySelector('.modal-content').insertBefore(note, successModal.querySelector('#successContinueBtn'));
        } else {
          successTitle.textContent = 'ITEM DELETED!';
          successModal.querySelectorAll('.pending-note').forEach(el => el.remove());
          await loadItems();
        }
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
      const catId = createCategory.value;
      createSubcat.innerHTML = '<option value="">Subcategory</option>';
      subcategories
        .filter(s => s.category_id == catId)
        .forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = s.name;
          createSubcat.appendChild(opt);
        });
    });

    // STEP 1: CLICK CREATE → SHOW CONFIRM
    createNext.addEventListener('click', () => {
      const catId = createCategory.value;
      const subId = createSubcat.value;
      const stockNo = createStockNumber.value.trim();
      const name = createName.value.trim();


      if (!catId || !subId || !name || !stockNo) {
        showToast('Please fill in Category, Subcategory, Name, and Stock No.', 'error');
        return;
      }

      pendingCreateData = {
        category_id: catId,
        subcategory_id: subId,
        stock_number: stockNo,
        name
      };

      createConfirmModal.classList.remove('hidden');
    });

    // STEP 2: CONFIRM → CREATE ITEM
    createConfirmBtn.addEventListener('click', async () => {
      if (!pendingCreateData) return;

      createConfirmModal.classList.add('hidden');

      try {
        const res = await apiFetch('/api/inventory', {
          method: 'POST',
          body: JSON.stringify(pendingCreateData)
        });

        createModal.classList.add('hidden');
        pendingCreateData = null;

        createCategory.value = '';
        createSubcat.innerHTML = '<option value="">Subcategory</option>';
        createStockNumber.value = '';
        createName.value = '';

        // ── Pending approval ───────────────────
        if (res.pending) {
          successTitle.textContent = 'CREATE REQUEST SUBMITTED!';

          successModal.querySelectorAll('.pending-note')
            .forEach(el => el.remove());

          const note = document.createElement('p');

          note.className = 'pending-note';
          note.style.cssText =
            'color:#f39c12; font-size:0.82rem; font-weight:700; margin-bottom:1rem;';

          note.textContent =
            'Awaiting admin approval before the item appears in inventory.';

          successModal.querySelector('.modal-content')
            .insertBefore(
              note,
              successModal.querySelector('#successContinueBtn')
            );

          successModal.classList.remove('hidden');
          return;
        }

        // ── Admin immediate apply ──────────────
        await loadItems();

        expandedItemId = res.id;
        editingItemId = res.id;

        renderTable();

        successModal.querySelectorAll('.pending-note')
          .forEach(el => el.remove());

        successTitle.textContent =
          res.updated
            ? 'QUANTITY UPDATED!'
            : 'ITEM CREATED!';

        successModal.classList.remove('hidden');

      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });

    // CANCEL CONFIRM
    createCancelBtn.addEventListener('click', () => {
      createConfirmModal.classList.add('hidden');
    });

    // SUCCESS MODAL CONTINUE BUTTON
    if (successContBtn) {
      successContBtn.onclick = () => {
        successModal.classList.add('hidden');
      };
    }

    // ── Manage Categories Modal ───────────────────────────────────────────
    const manageCatModal = document.getElementById('manageCatModal');
    const btnManageCategories = document.getElementById('btnManageCategories');
    const tabAddCat = document.getElementById('tabAddCat');
    const tabAddSub = document.getElementById('tabAddSub');
    const panelAddCat = document.getElementById('panelAddCat');
    const panelAddSub = document.getElementById('panelAddSub');
    const newCatName = document.getElementById('newCatName');
    const saveCatBtn = document.getElementById('saveCatBtn');
    const manageCatClose = document.getElementById('manageCatClose');
    const subCatParent = document.getElementById('subCatParent');
    const newSubName = document.getElementById('newSubName');
    const saveSubBtn = document.getElementById('saveSubBtn');
    const manageSubClose = document.getElementById('manageSubClose');
    const catListContainer = document.getElementById('catListContainer');
    const subListContainer = document.getElementById('subListContainer');

    // ── Category Result Modal ─────────────────────────────────────────────
    const catResultModal = document.getElementById('catResultModal');
    const catResultIcon = document.getElementById('catResultIcon');
    const catResultTitle = document.getElementById('catResultTitle');
    const catResultMsg = document.getElementById('catResultMsg');
    const catResultContinueBtn = document.getElementById('catResultContinueBtn');

    // ── Category Delete Confirm Modal ─────────────────────────────────────
    const catDeleteModal = document.getElementById('catDeleteModal');
    const catDeleteMsg = document.getElementById('catDeleteMsg');
    const catDeleteCancelBtn = document.getElementById('catDeleteCancelBtn');
    const catDeleteConfirmBtn = document.getElementById('catDeleteConfirmBtn');
    let catDeleteTarget = null; // { type, id, name }

    // ── Helpers ───────────────────────────────────────────────────────────
    const TRASH_SVG = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="3 6 5 6 21 6"></polyline>
      <path d="M19 6l-1 14H6L5 6"></path>
      <path d="M10 11v6M14 11v6"></path>
      <path d="M9 6V4h6v2"></path></svg>`;

    function showCatResult(success, title, message, onContinue) {
      if (success) {
        catResultIcon.style.background = '#e6f9f0';
        catResultIcon.innerHTML = `<svg width="36" height="36" viewBox="0 0 24 24" fill="none"
          stroke="#27ae60" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline></svg>`;
      } else {
        catResultIcon.style.background = '#fde8e8';
        catResultIcon.innerHTML = `<svg width="36" height="36" viewBox="0 0 24 24" fill="none"
          stroke="#e74c3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
      }
      catResultTitle.textContent = title;
      catResultMsg.textContent = message;
      catResultContinueBtn.onclick = () => {
        catResultModal.classList.add('hidden');
        if (onContinue) onContinue();
      };
      manageCatModal.classList.add('hidden');
      catDeleteModal.classList.add('hidden');
      catResultModal.classList.remove('hidden');
    }

    // ── List Rendering ────────────────────────────────────────────────────
    function makeDelBtn(type, id, name) {
      const btn = document.createElement('button');
      btn.innerHTML = TRASH_SVG;
      btn.title = `Delete ${type}`;
      btn.style.cssText = 'background:none;border:none;cursor:pointer;padding:4px;color:#e74c3c;line-height:1;flex-shrink:0;';
      btn.addEventListener('click', () => {
        catDeleteTarget = { type, id, name };
        catDeleteMsg.textContent = `Are you sure you want to delete "${name}"? This cannot be undone.`;
        manageCatModal.classList.add('hidden');
        catDeleteModal.classList.remove('hidden');
      });
      return btn;
    }

    function renderCatList() {
      if (!catListContainer) return;
      catListContainer.innerHTML = '';
      if (!categories.length) {
        catListContainer.innerHTML = '<p style="text-align:center;color:var(--text-muted);font-size:0.82rem;padding:0.75rem;">No categories yet.</p>';
        return;
      }
      categories.forEach(c => {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0.75rem;border-bottom:1px solid #f1f5f9;';
        const label = document.createElement('span');
        label.style.cssText = 'font-size:0.85rem;font-weight:600;color:var(--primary-navy);';
        label.textContent = c.name;
        row.appendChild(label);
        row.appendChild(makeDelBtn('category', c.id, c.name));
        catListContainer.appendChild(row);
      });
    }

    function renderSubList() {
      if (!subListContainer) return;
      const catId = subCatParent.value;
      subListContainer.innerHTML = '';
      if (!catId) {
        subListContainer.innerHTML = '<p style="text-align:center;color:var(--text-muted);font-size:0.82rem;padding:0.75rem;">Select a category above.</p>';
        return;
      }
      const subs = subcategories.filter(s => s.category_id == catId);
      if (!subs.length) {
        subListContainer.innerHTML = '<p style="text-align:center;color:var(--text-muted);font-size:0.82rem;padding:0.75rem;">No subcategories yet.</p>';
        return;
      }
      subs.forEach(s => {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0.75rem;border-bottom:1px solid #f1f5f9;';
        const label = document.createElement('span');
        label.style.cssText = 'font-size:0.85rem;font-weight:600;color:var(--primary-navy);';
        label.textContent = s.name;
        row.appendChild(label);
        row.appendChild(makeDelBtn('subcategory', s.id, s.name));
        subListContainer.appendChild(row);
      });
    }

    // ── Delete Confirm Handlers ───────────────────────────────────────────
    catDeleteCancelBtn.addEventListener('click', () => {
      catDeleteModal.classList.add('hidden');
      catDeleteTarget = null;
      manageCatModal.classList.remove('hidden');
    });

    catDeleteConfirmBtn.addEventListener('click', async () => {
      if (!catDeleteTarget) return;
      const { type, id, name } = catDeleteTarget;
      const url = type === 'category' ? `/api/categories/${id}` : `/api/subcategories/${id}`;
      catDeleteTarget = null;
      catDeleteConfirmBtn.disabled = true;
      try {
        await apiFetch(url, { method: 'DELETE' });
        if (type === 'category') {
          await loadCategories();
          await loadSubcategories();
        } else {
          await loadSubcategories();
        }
        renderFilters();
        showCatResult(true,
          type === 'category' ? 'CATEGORY DELETED!' : 'SUBCATEGORY DELETED!',
          `"${name}" has been removed.`,
          openManageCatModal);
      } catch (e) {
        showCatResult(false, 'CANNOT DELETE', e.message, openManageCatModal);
      } finally {
        catDeleteConfirmBtn.disabled = false;
      }
    });

    // ── Tab + Modal Open ──────────────────────────────────────────────────
    const TAB_ACTIVE_BG = 'var(--primary-navy)';
    const TAB_ACTIVE_COLOR = '#fff';
    const TAB_IDLE_BG = '#f8fafc';
    const TAB_IDLE_COLOR = '#4a5568';

    function applyTabStyles(activeBtn, idleBtn) {
      activeBtn.style.background = TAB_ACTIVE_BG;
      activeBtn.style.color = TAB_ACTIVE_COLOR;
      idleBtn.style.background = TAB_IDLE_BG;
      idleBtn.style.color = TAB_IDLE_COLOR;
    }

    function openManageCatModal() {
      subCatParent.innerHTML = '<option value="">Select Category</option>';
      categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        subCatParent.appendChild(opt);
      });
      panelAddCat.style.display = '';
      panelAddSub.style.display = 'none';
      applyTabStyles(tabAddCat, tabAddSub);
      newCatName.value = '';
      newSubName.value = '';
      subCatParent.value = '';
      renderCatList();
      manageCatModal.classList.remove('hidden');
    }

    tabAddCat.addEventListener('click', () => {
      panelAddCat.style.display = '';
      panelAddSub.style.display = 'none';
      applyTabStyles(tabAddCat, tabAddSub);
      renderCatList();
    });

    tabAddSub.addEventListener('click', () => {
      panelAddCat.style.display = 'none';
      panelAddSub.style.display = '';
      applyTabStyles(tabAddSub, tabAddCat);
      renderSubList();
    });

    subCatParent.addEventListener('change', renderSubList);

    btnManageCategories.addEventListener('click', openManageCatModal);
    manageCatClose.addEventListener('click', () => manageCatModal.classList.add('hidden'));
    manageSubClose.addEventListener('click', () => manageCatModal.classList.add('hidden'));

    saveCatBtn.addEventListener('click', async () => {
      const name = newCatName.value.trim();
      if (!name) { showToast('Please enter a category name.', 'error'); return; }
      if (name.length > 100) { showToast('Category name must be 100 characters or fewer.', 'error'); return; }
      try {
        saveCatBtn.disabled = true;
        const res = await apiFetch('/api/categories', { method: 'POST', body: JSON.stringify({ name }) });
        await loadCategories();
        await loadSubcategories();
        renderFilters();
        newCatName.value = '';
        renderCatList();
        showCatResult(
          res.created, res.created ? 'CATEGORY CREATED!' : 'ALREADY EXISTS',
          res.created ? `"${res.name}" has been added.` : `"${res.name}" already exists.`,
          openManageCatModal);
      } catch (e) {
        showCatResult(false, 'ERROR', e.message, openManageCatModal);
      } finally { saveCatBtn.disabled = false; }
    });

    saveSubBtn.addEventListener('click', async () => {
      const catId = subCatParent.value;
      const name = newSubName.value.trim();
      if (!catId) { showToast('Please select a parent category.', 'error'); return; }
      if (!name) { showToast('Please enter a subcategory name.', 'error'); return; }
      if (name.length > 100) { showToast('Subcategory name must be 100 characters or fewer.', 'error'); return; }
      try {
        saveSubBtn.disabled = true;
        const res = await apiFetch('/api/subcategories', { method: 'POST', body: JSON.stringify({ category_id: catId, name }) });
        await loadSubcategories();
        renderFilters();
        newSubName.value = '';
        renderSubList();
        showCatResult(
          res.created, res.created ? 'SUBCATEGORY CREATED!' : 'ALREADY EXISTS',
          res.created ? `"${res.name}" has been added.` : `"${res.name}" already exists.`,
          openManageCatModal);
      } catch (e) {
        showCatResult(false, 'ERROR', e.message, openManageCatModal);
      } finally { saveSubBtn.disabled = false; }
    });

    // ── Search & Sort ─────────────────────────────────────────────────────
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

    if (categories.length > 0 && activeCatId === null) {
      activeCatId = categories[0].id;
    }

    renderFilters();
    await loadItems();
    bindEvents();
  };

})();
