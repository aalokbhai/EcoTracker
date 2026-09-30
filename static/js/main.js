document.addEventListener('DOMContentLoaded', () => {
  // Navbar shadow on scroll
  const nav = document.getElementById('mainNav');
  const onScroll = () => nav && nav.classList.toggle('scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll);

  // Count-up animation
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10) || 0;
    const duration = 900;
    const start = performance.now();
    const tick = now => {
      const p = Math.min((now - start) / duration, 1);
      el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target;
    };
    requestAnimationFrame(tick);
  });

  // Image preview on the complaint form
  const input = document.getElementById('id_image');
  const preview = document.getElementById('imagePreview');
  const label = document.getElementById('dropLabel');
  if (input && preview) {
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (!file) return;
      preview.src = URL.createObjectURL(file);
      preview.classList.remove('d-none');
      if (label) label.textContent = file.name;
    });
  }

  // Auto-dismiss alerts
  document.querySelectorAll('.alert.auto-dismiss').forEach(a => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(a).close(), 5000);
  });
});