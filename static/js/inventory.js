document.addEventListener('click', function(e) {
    if (!e.target.closest('.action-cell')) {
        document.querySelectorAll('.dot-menu').forEach(function(m) {
            m.style.display = 'none';
        });
    }
});
