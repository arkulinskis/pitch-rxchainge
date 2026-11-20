/* For screenshots of member pages: sign up a fresh account and add one item. Resolves to window.SEED.
   Extend it so every member page has something to show (the app's own main objects). */
(async function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  try {
    if (location.hash !== '#auth/signup') window.UI_READY = false;
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]');
    type(inputs[0], 'Sam Rivera'); type(inputs[1], 'shots' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#studio' && window.UI_READY, 'home', 60000);
    await until(() => document.querySelector('.ac'), 'demo agents');
    const demo = document.querySelector('.ac').getAttribute('href');
    // an agent of their own from a template, with a long name (worst-case data)
    Array.from(document.querySelectorAll('button')).find((b) => b.textContent.trim() === 'New agent').click();
    await until(() => $('.na-dialog input'), 'new agent dialog');
    type($('.na-dialog input'), 'Maximilienne-Antoinette Guide Gourmand');
    Array.from(document.querySelectorAll('.na-dialog button')).find((b) => /Create agent/.test(b.textContent)).click();
    await until(() => /^#agent\//.test(location.hash) && window.UI_READY && $('.ag-head'), 'own agent', 60000);
    window.SEED = { studio: '#studio', demo: demo, agent: location.hash.split('/').slice(0, 2).join('/') };
    return window.SEED;
  } catch (e) {
    return { error: String(e && e.message || e) };
  }
})();
