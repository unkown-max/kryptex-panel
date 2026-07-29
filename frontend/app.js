// Small shared helpers used by both dashboards.

async function apiFetch(url, options = {}) {
  const res = await fetch(url, { credentials: 'include', ...options });
  if (res.status === 401) {
    window.location.href = 'login.html';
    throw new Error('Oturum sona erdi');
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `İstek başarısız (${res.status})`);
  }
  return data;
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return '—';
  if (bytes === 0) return '0 GB';
  const gb = bytes / (1024 ** 3);
  if (gb < 1) return (bytes / (1024 ** 2)).toFixed(0) + ' MB';
  return gb.toFixed(1) + ' GB';
}

function formatExpire(expireTimestamp) {
  if (!expireTimestamp) return 'Süresiz';
  try {
    const d = new Date(expireTimestamp * 1000);
    return d.toLocaleDateString('tr-TR');
  } catch {
    return String(expireTimestamp);
  }
}

async function logout() {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  window.location.href = 'index.html';
}
