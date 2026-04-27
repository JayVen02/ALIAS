/* ═══════════════════════════════════════════════
   ALIAS – audit.js
   Computes variance for the audit categories page
═══════════════════════════════════════════════ */

(function () {
  'use strict';

  /**
   * Recalculate shortage/overage for a row when the
   * physical-count input changes.
   * @param {HTMLInputElement} inputEl
   */
  function calculateVariance(inputEl) {
    const row = inputEl.closest('tr');
    if (!row) return;

    const systemQtyEl  = row.querySelector('.system-qty');
    const badge        = row.querySelector('.variance-badge');
    const remarksInput = row.querySelector('.remarks-input');

    if (!systemQtyEl || !badge) return;

    const systemQty   = parseInt(systemQtyEl.dataset.qty, 10);
    const physicalQty = parseInt(inputEl.value, 10);

    if (isNaN(physicalQty)) {
      badge.textContent = 'Pending';
      badge.className   = 'variance-badge variance-neutral';
      if (remarksInput) remarksInput.required = false;
      return;
    }

    const variance = physicalQty - systemQty;
    const sign     = variance > 0 ? '+' : '';

    if (variance === 0) {
      badge.textContent = 'Matched (0)';
      badge.className   = 'variance-badge variance-good';
      if (remarksInput) remarksInput.required = false;
    } else {
      badge.textContent = `Discrepancy (${sign}${variance})`;
      badge.className   = 'variance-badge variance-bad';
      if (remarksInput) remarksInput.required = true;
    }
  }

  // Expose for inline oninput handlers in audit templates
  window.calculateVariance = calculateVariance;

})();