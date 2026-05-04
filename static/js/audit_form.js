(function () {
    'use strict';

    window.initAuditForm = function () {
        const modal = document.getElementById('createModal');
        const openModalBtn = document.getElementById('openModalBtn');
        const modalBackBtn = document.getElementById('modalBackBtn');
        const modalCreateBtn = document.getElementById('modalCreateBtn');
        const modalError = document.getElementById('modalError');

        if (!modal) return;

        window.calculateShortage = function(inputEl) {
            const row = inputEl.closest('.audit-data-row');
            const propQtyEl = row.querySelector('.prop-card-qty');
            const unitValEl = row.querySelector('.unit-val-cell');
            const sQtyEl = row.querySelector('.shortage-qty');
            const sValEl = row.querySelector('.shortage-val');
            const remarkEl = row.querySelector('.remarks-input');
            if (!propQtyEl || !sQtyEl || !sValEl) return;
            const propQty = parseFloat(propQtyEl.dataset.qty) || 0;
            const unitVal = parseFloat(unitValEl.dataset.val) || 0;
            const physical = parseFloat(inputEl.value);
            if (isNaN(physical)) {
                sQtyEl.textContent = '—'; sValEl.textContent = '—';
                sQtyEl.className = 'shortage-qty shortage-neutral';
                sValEl.className = 'shortage-val shortage-neutral';
                if (remarkEl) remarkEl.required = false;
                return;
            }
            const diff = physical - propQty;
            const val = diff * unitVal;
            const sign = diff > 0 ? '+' : '';
            const cls = diff === 0 ? 'shortage-neutral' : diff > 0 ? 'shortage-over' : 'shortage-short';
            sQtyEl.textContent = diff === 0 ? '0' : `${sign}${diff}`;
            sQtyEl.className = `shortage-qty ${cls}`;
            sValEl.textContent = diff === 0 ? '0.00' : `${sign}${val.toFixed(2)}`;
            sValEl.className = `shortage-val ${cls}`;
            if (remarkEl) remarkEl.required = diff !== 0;
        }

        function escHtml(str) {
            return String(str)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }

        function positionDropdown(btn, dropdown) {
            const rect = btn.getBoundingClientRect();
            dropdown.style.top = (rect.bottom + window.scrollY + 4) + 'px';
            setTimeout(() => {
                let left = rect.right + window.scrollX - dropdown.offsetWidth;
                if (left < 8) left = 8;
                dropdown.style.left = left + 'px';
            }, 0);
        }

        function attachRowEvents(tr, expandTr) {
            tr.querySelector('.expand-btn').addEventListener('click', () => {
                expandTr.classList.toggle('open');
                tr.querySelector('.expand-btn').style.transform =
                    expandTr.classList.contains('open') ? 'rotate(180deg)' : 'rotate(0deg)';
            });

            const menuBtn = tr.querySelector('.menu-btn');
            const dropdown = tr.querySelector('.dropdown-menu');

            menuBtn.addEventListener('click', e => {
                e.stopPropagation();
                document.querySelectorAll('.dropdown-menu.open').forEach(m => { if (m !== dropdown) m.classList.remove('open'); });
                dropdown.classList.toggle('open');
                if (dropdown.classList.contains('open')) positionDropdown(menuBtn, dropdown);
            });

            tr.querySelector('.delete-btn').addEventListener('click', e => {
                e.preventDefault();
                tr.remove(); expandTr.remove();
            });

            tr.querySelector('.edit-btn').addEventListener('click', e => {
                e.preventDefault();
                dropdown.classList.remove('open');
                document.getElementById('mi-article').value = tr.dataset.article || '';
                document.getElementById('mi-desc').value = tr.dataset.desc || '';
                document.getElementById('mi-propno').value = tr.dataset.propno || '';
                document.getElementById('mi-unit').value = tr.dataset.unit || '';
                document.getElementById('mi-unitval').value = tr.dataset.unitval || '';
                document.getElementById('mi-propcard').value = tr.dataset.propcard || '';
                modalCreateBtn.dataset.editRow = 'true';
                tr.dataset.editing = 'true';
                modal.classList.add('open');
                modalError.textContent = '';
            });
        }

        function buildRow(article, desc, propno, unit, unitval, propcard) {
            const safeId = article.replace(/[^a-zA-Z0-9\-_]/g, '_');
            const uv = parseFloat(unitval) || 0;
            const tr = document.createElement('tr');
            tr.className = 'audit-data-row';
            Object.assign(tr.dataset, { article, desc, propno, unit, unitval, propcard });
            tr.innerHTML = `
                <td>${escHtml(article)}</td>
                <td>${escHtml(desc)}</td>
                <td>${escHtml(propno)}</td>
                <td>${escHtml(unit || '—')}</td>
                <td class="unit-val-cell" data-val="${escHtml(unitval)}">${uv > 0 ? uv.toFixed(2) : '—'}</td>
                <td class="prop-card-qty" data-qty="${escHtml(propcard)}">${escHtml(propcard)}</td>
                <td><input type="number" name="physical_${escHtml(safeId)}" class="audit-input physical-input" oninput="calculateShortage(this)" placeholder="0" required></td>
                <td><span class="shortage-qty shortage-neutral">—</span></td>
                <td><span class="shortage-val shortage-neutral">—</span></td>
                <td><input type="text" name="remarks_${escHtml(safeId)}" class="remarks-input" placeholder="Add remark…"></td>
                <td>
                    <div class="row-actions">
                        <button type="button" class="icon-btn expand-btn" title="Expand">&#8964;</button>
                        <div class="row-menu">
                            <button type="button" class="icon-btn menu-btn" title="Options">&#8942;</button>
                            <div class="dropdown-menu">
                                <a href="#" class="edit-btn">Edit Item</a>
                                <a href="#" class="danger delete-btn">Delete Item</a>
                            </div>
                        </div>
                    </div>
                </td>`;
            const expandTr = document.createElement('tr');
            expandTr.className = 'expand-row';
            expandTr.innerHTML = `<td colspan="11"><strong>Article:</strong> ${escHtml(article)} &nbsp;|&nbsp; <strong>Property No.:</strong> ${escHtml(propno)} &nbsp;|&nbsp; <strong>Unit Value:</strong> ${uv > 0 ? uv.toFixed(2) : '—'}</td>`;
            attachRowEvents(tr, expandTr);
            return [tr, expandTr];
        }

        document.querySelectorAll('.audit-data-row').forEach(tr => attachRowEvents(tr, tr.nextElementSibling));

        function closeModal() {
            modal.classList.remove('open');
            modalError.textContent = '';
            delete modalCreateBtn.dataset.editRow;
            document.querySelectorAll('.audit-data-row[data-editing]').forEach(r => delete r.dataset.editing);
            ['mi-article', 'mi-desc', 'mi-propno', 'mi-unit', 'mi-unitval', 'mi-propcard']
                .forEach(id => document.getElementById(id).value = '');
        }

        openModalBtn.addEventListener('click', () => { modal.classList.add('open'); modalError.textContent = ''; });
        modalBackBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

        modalCreateBtn.addEventListener('click', () => {
            const article = document.getElementById('mi-article').value.trim();
            const desc = document.getElementById('mi-desc').value.trim();
            const propno = document.getElementById('mi-propno').value.trim();
            const unit = document.getElementById('mi-unit').value.trim();
            const unitval = document.getElementById('mi-unitval').value.trim();
            const propcard = document.getElementById('mi-propcard').value.trim();
            if (!article || !desc || !propcard) {
                modalError.textContent = 'Article, Description, and Qty per Property Card are required.';
                return;
            }
            if (modalCreateBtn.dataset.editRow === 'true') {
                const editingRow = document.querySelector('.audit-data-row[data-editing="true"]');
                if (editingRow) {
                    const uv = parseFloat(unitval) || 0;
                    editingRow.cells[0].textContent = article;
                    editingRow.cells[1].textContent = desc;
                    editingRow.cells[2].textContent = propno;
                    editingRow.cells[3].textContent = unit || '—';
                    editingRow.cells[4].textContent = uv > 0 ? uv.toFixed(2) : '—';
                    editingRow.cells[4].dataset.val = unitval;
                    editingRow.querySelector('.prop-card-qty').textContent = propcard;
                    editingRow.querySelector('.prop-card-qty').dataset.qty = propcard;
                    Object.assign(editingRow.dataset, { article, desc, propno, unit, unitval, propcard });
                    const ph = editingRow.querySelector('.physical-input');
                    if (ph.value) calculateShortage(ph);
                    delete editingRow.dataset.editing;
                }
            } else {
                const emptyRow = document.getElementById('emptyRow');
                if (emptyRow) emptyRow.remove();
                const [newTr, newExpand] = buildRow(article, desc, propno, unit, unitval, propcard);
                document.getElementById('auditTbody').append(newTr, newExpand);
            }
            closeModal();
        });

        const pdfModal = document.getElementById('pdfModal');
        const openPdfBtn = document.getElementById('openPdfBtn');
        const pdfModalBack = document.getElementById('pdfModalBackBtn');
        const pdfHidden = document.getElementById('pdfHiddenFields');

        function collectRowsIntoHiddenFields() {
            pdfHidden.innerHTML = '';
            document.querySelectorAll('#auditTbody .audit-data-row').forEach(tr => {
                const physInput = tr.querySelector('.physical-input');
                const remInput = tr.querySelector('.remarks-input');
                const f = (name, val) => {
                    const inp = document.createElement('input');
                    inp.type = 'hidden'; inp.name = name; inp.value = val || '';
                    pdfHidden.appendChild(inp);
                };
                f('pdf_article[]', tr.dataset.article || tr.cells[0].textContent.trim());
                f('pdf_desc[]', tr.dataset.desc || tr.cells[1].textContent.trim());
                f('pdf_propno[]', tr.dataset.propno || tr.cells[2].textContent.trim());
                f('pdf_unit[]', tr.dataset.unit || tr.cells[3].textContent.trim());
                f('pdf_unitval[]', tr.dataset.unitval || '');
                f('pdf_qtycard[]', tr.dataset.propcard || tr.querySelector('.prop-card-qty').dataset.qty || '');
                f('pdf_qtyphys[]', physInput ? physInput.value : '');
                f('pdf_remarks[]', remInput ? remInput.value : '');
            });
        }

        openPdfBtn.addEventListener('click', () => {
            collectRowsIntoHiddenFields();
            pdfModal.classList.add('open');
        });

        pdfModalBack.addEventListener('click', () => pdfModal.classList.remove('open'));
        pdfModal.addEventListener('click', e => { if (e.target === pdfModal) pdfModal.classList.remove('open'); });

        document.addEventListener('click', () => {
            document.querySelectorAll('.dropdown-menu.open').forEach(m => m.classList.remove('open'));
        });
    }
})();
