// Auto-hide success toast
(function () {
  const toast = document.getElementById('addedToast');
  if (toast) {
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }
})();

// Quantity stepper +/-
document.addEventListener('click', function (e) {
  const btn = e.target.closest('button[data-step]');
  if (!btn) return;

  const group = btn.closest('.qty-stepper');
  const input = group?.querySelector('input[name="quantity"]');
  if (!input) return;

  const direction = btn.getAttribute('data-step');
  let value = parseInt(input.value, 10) || 1;

  value = direction === 'up' ? value + 1 : Math.max(1, value - 1);
  input.value = value;

  // subtle animation
  input.style.transform = 'scale(1.1)';
  setTimeout(() => { input.style.transform = 'scale(1)'; }, 150);
}, false);

// Loading state on add-to-cart submit
document.addEventListener('submit', function(e) {
  const form = e.target;
  try {
    const action = (form.getAttribute('action') || '').toLowerCase();
    if (action.includes('add_to_cart')) {
      const button = form.querySelector('.add-to-cart-btn');
      if (button) {
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang thêm...';
        button.disabled = true;
      }
    }
  } catch (_) {}
});
