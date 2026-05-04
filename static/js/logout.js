document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  const logoutModal = document.getElementById('logoutModal');
  const logoutConfirm = document.getElementById('logoutConfirm');
  const logoutCancel = document.getElementById('logoutCancel');
  const logoutForm = document.getElementById('logoutForm');

  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logoutModal.classList.remove('hidden');
    });
  }

  if (logoutCancel) {
    logoutCancel.addEventListener('click', () => {
      logoutModal.classList.add('hidden');
    });
  }

  if (logoutConfirm) {
    logoutConfirm.addEventListener('click', () => {
      logoutForm.submit();
    });
  }
});