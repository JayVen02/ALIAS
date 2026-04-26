function calculateVariance(inputElement) {
    const row = inputElement.closest('tr');

    const systemQtyElement = row.querySelector('.system-qty');
    if (!systemQtyElement) return;

    const systemQty = parseInt(systemQtyElement.getAttribute('data-qty'), 10);
    const physicalQty = parseInt(inputElement.value, 10);

    const badge = row.querySelector('.variance-badge');
    const remarksInput = row.querySelector('.remarks-input');

    if (isNaN(physicalQty)) {
        badge.textContent = "Pending";
        badge.className = "variance-badge variance-neutral";
        if (remarksInput) remarksInput.required = false;
        return;
    }

    const variance = physicalQty - systemQty;

    if (variance === 0) {
        badge.textContent = "Matched (0)";
        badge.className = "variance-badge variance-good";
        if (remarksInput) remarksInput.required = false;
    } else {
        const sign = variance > 0 ? "+" : "";
        badge.textContent = `Discrepancy (${sign}${variance})`;
        badge.className = "variance-badge variance-bad";
        if (remarksInput) remarksInput.required = true;
    }
}
}