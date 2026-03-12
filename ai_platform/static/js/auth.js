/* ── Shared utilities ─────────────────────────────────────────────── */

function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function openModal(id) {
  document.getElementById(id).style.display = 'flex';
}

function closeModal(id) {
  document.getElementById(id).style.display = 'none';
}

/* Close modal on backdrop click */
document.addEventListener('click', function (e) {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.style.display = 'none';
  }
});

/* ── Auth ─────────────────────────────────────────────────────────── */

async function login() {
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';

  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email:    document.getElementById('login-email').value,
      password: document.getElementById('login-password').value,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    errEl.textContent = data.error || 'Login failed.';
    errEl.style.display = 'block';
    return;
  }

  closeModal('login-modal');
  refreshAuthUI();
  // Redirect to dashboard after login
  window.location.href = '/dashboard';
}

async function register() {
  const errEl = document.getElementById('register-error');
  errEl.style.display = 'none';

  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role:     document.getElementById('reg-role').value,
      name:     document.getElementById('reg-name').value,
      email:    document.getElementById('reg-email').value,
      password: document.getElementById('reg-password').value,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    errEl.textContent = data.error || 'Registration failed.';
    errEl.style.display = 'block';
    return;
  }

  closeModal('register-modal');
  refreshAuthUI();
  window.location.href = '/dashboard';
}

async function logout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  refreshAuthUI();
  window.location.href = '/';
}

async function refreshAuthUI() {
  const res = await fetch('/api/auth/me');
  const authEl   = document.getElementById('nav-auth');
  const userEl   = document.getElementById('nav-user');
  const dashEl   = document.getElementById('nav-dashboard');
  const nameEl   = document.getElementById('nav-username');

  if (res.ok) {
    const me = await res.json();
    authEl.style.display  = 'none';
    userEl.style.display  = 'flex';
    dashEl.style.display  = 'inline';
    nameEl.textContent    = me.profile?.name || me.email;
    userEl.style.alignItems = 'center';
    userEl.style.gap = '.75rem';
  } else {
    authEl.style.display  = 'block';
    userEl.style.display  = 'none';
    dashEl.style.display  = 'none';
  }
}

// Run on every page load
refreshAuthUI();
