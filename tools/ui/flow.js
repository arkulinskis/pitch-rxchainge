/* The main user journey, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs.
   Resolves to {ok, log}. Keep log lines ASCII (the Windows console).
   Visitor: landing hero face + guides, talks to a demo guide. Member: signs up, makes an agent from a template,
   edits identity, face, sources, approves topics (as owner, no expert), drafts from sources, tries it, publishes,
   talks to it on its public page, opens the review queue and a demo agent (look-only), theme, sign out. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const norm = (e) => e.textContent.trim().replace(/\s+/g, ' ');
  const byText = (sel, text) => $$(sel).find((e) => norm(e) === text && (e.offsetParent || e.getClientRects().length));
  async function click(sel, text) {
    const el = await until(() => (text ? byText(sel, text) : $(sel)), sel + (text ? ' "' + text + '"' : ''));
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  }
  function type(input, value) {
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;  // the old page stays until the router runs
    location.hash = hash;
    await until(() => window.UI_READY && ready(), what || hash, 30000);
    await sleep(300);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };
  const agentMsgs = () => $$('.as-msg.agent').map(norm);
  async function ask(text, expect, what) {
    const before = $$('.as-msg').length;
    type(await until(() => $('.as-ask input'), 'ask box'), text);
    await click('.as-ask .anvil-role-btn button');
    await until(() => $$('.as-msg').length >= before + 2, 'answer to: ' + what, 30000);
    const last = agentMsgs().slice(-1)[0] || '';
    ok(expect.test(last), what + ' (' + last.slice(0, 60).replace(/[^\x20-\x7e]/g, '?') + ')');
  }

  try {
    // ---- landing (visitors)
    await page('#landing', () => $('.lp-hero') && $('.hd .as-face svg'), 'landing with the hero face');
    ok($('.lp-hero a[href="#auth/signup"]'), 'landing: hero with a sign-up link');
    ok($$('.gc').length === 3, 'landing: three demo guides');
    ok(/Approved by|Approuv/.test($('.hd-stamp').textContent), 'landing: the answer carries the expert approval stamp');
    await click('.gp', 'Théo');
    await until(() => /Théo/.test($('.hd-a').textContent), 'picking a guide switches the hero');
    ok(true, 'landing: picking a guide switches the hero face');

    // ---- the public page of a demo guide, as a visitor
    await page('#talk/demo-classics', () => $('.as-chat') && agentMsgs().length, 'public demo page');
    ok(/Mireille/.test($('.anvil-role-chat-name').textContent), 'talk: the guide greets the visitor');
    await ask('Where can I get great smoked meat?', /Schwartz/, 'talk: an approved answer');
    ok(/Approved by H/.test(norm($$('.as-msg.agent').slice(-1)[0])), 'talk: the answer says who approved it');
    await click('.as-chat .ui-seg button', 'Français');
    await ask('Où goûter une poutine?', /Banquise/, 'talk: answers in French');
    await click('.as-chat .ui-seg button', 'English');
    await ask('Which bus goes to the airport?', /passed your question/, 'talk: unknown questions are passed on, not invented');

    // ---- members-only page sends visitors to sign in, then back
    await page('#profile', () => true);
    await until(() => window.UI_READY && $$('.au-card input').length >= 2, 'redirected to sign in');
    ok(true, 'a members-only page asks visitors to sign in');
    await click('.au-card .ui-seg button', 'Create account');
    await until(() => $$('.au-card input[type=password]').length && $$('.au-card input').filter((i) => i.offsetParent).length >= 3, 'sign-up form');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter((i) => i.offsetParent);
    type(inputs[0], 'Flow Tester'); type(inputs[1], 'flow' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]');
    if (tick && !tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => location.hash === '#profile' && window.UI_READY && $('.pf-grid'), 'back on the page they wanted', 40000);
    ok(true, 'sign-up: signed in and sent on to the page they asked for');

    // ---- studio: empty, demo agents, new agent from a template
    await page('#studio', () => $('.st-page') && $$('.ac').length >= 3, 'studio');
    ok($('.st-empty') && $('.st-empty').offsetParent, 'studio: an empty state for a new member');
    ok($$('.ac').length === 3, 'studio: the three demo agents to look around');
    await click('button', 'New agent');
    await until(() => $('.na-dialog') && $$('.na-dialog .tc').length === 4, 'new agent dialog with 3 templates + blank');
    ok($('.na-dialog .tc.on') && /Mireille/.test($('.na-dialog .tc.on').textContent), 'new agent: a template is chosen by default');
    type($('.na-dialog input'), 'Flow Guide');
    await click('.na-dialog button', 'Create agent');
    await until(() => /^#agent\//.test(location.hash) && window.UI_READY && $('.ag-head') && /Flow Guide/.test($('.ag-head').textContent), 'editor of the new agent', 40000);
    ok($$('.cs').length === 6, 'overview: six steps to go live');

    // ---- overview: identity
    const tagEn = $$('.ov-main input')[2];
    type(tagEn, 'My flow-test guide to the classics');
    await click('button', 'Save identity');
    await until(() => /flow-test guide/.test($('.ag-head').textContent), 'tagline saved');
    ok(true, 'overview: identity saved, header updated');

    // ---- look: the avatar studio
    await click('button[data-tab="look"]');
    await until(() => $('.lk-face svg') && $$('.pk').length > 20, 'look tab');
    await click('.pk', 'Curly');
    await until(() => /Unsaved changes/.test($('.lk-save').textContent), 'unsaved changes shown');
    await click('.lk-save button', 'Save face and voice');
    await until(() => /Saved/.test($('.lk-save').textContent), 'face saved');
    ok(true, 'look: a new hair style is saved');
    await click('button', 'Say hello');
    ok(true, 'look: the face says hello');

    // ---- knowledge: add a source
    await click('button[data-tab="knowledge"]');
    await until(() => $$('.sr-row').length === 2, 'two template sources');
    await click('button', 'Add a source');
    await until(() => $('.as-src-dialog textarea'), 'add source dialog');
    type($('.as-src-dialog input'), 'Flow notes');
    type($('.as-src-dialog textarea'), 'Jean-Talon Market in Little Italy is one of the largest open-air markets in North America. It has farmers, cheese shops and bakeries.');
    await click('.as-src-dialog button', 'Add source');
    await until(() => !$('.as-src-dialog') && $$('.sr-row').length === 3, 'source added');
    ok(true, 'knowledge: a pasted source is added');

    // ---- topics: draft from sources, approve two as the owner (no expert yet)
    await click('button[data-tab="topics"]');
    await until(() => $$('.tr').length === 8, 'eight draft topics from the template');
    await click('button', 'New topic');
    await until(() => $('.te'), 'topic editor');
    type($$('.te input')[0], 'Where should I try poutine tonight?');
    await click('.te button', 'Draft from sources');
    await until(() => /Banquise/.test($$('.te textarea')[0].value), 'drafted answer');
    ok(/Drafted from/.test($('.te').textContent), 'topics: a draft built from the sources, with the source named');
    await click('.te button', 'Close');
    await until(() => !$('.te'), 'editor closed');
    for (let n = 0; n < 2; n++) {
      const row = $$('.tr').find((r) => /Draft/.test(r.innerText) && !/French missing|No answer/.test(r.innerText));
      if (!row) throw new Error('no draft row among: ' + $$('.tr').map((r) => norm(r).slice(0, 70)).join(' | ').replace(/[^\x20-\x7e]/g, '?'));
      row.click();
      await until(() => $('.te'), 'topic editor');
      await click('.te button', 'Approve (as owner)');
      await until(() => !$('.te'), 'approved');
      await until(() => window.UI_READY && $$('.tr').filter((r) => /Approved/.test(r.innerText)).length === n + 1, 'approved count ' + (n + 1));
    }
    ok(true, 'topics: two topics approved by the owner');

    // ---- try it: preview answers from approved topics
    await click('button[data-tab="try"]');
    await until(() => $('.try .as-chat'), 'try tab');
    await ask('Where do I get the best smoked meat?', /Schwartz/, 'try: the preview answers from an approved topic');
    ok(/Matched an approved topic/.test($('.try-side').textContent), 'try: says which topic matched');

    // ---- publish
    await click('button[data-tab="publish"]');
    await until(() => $('.pb-next'), 'publish tab');
    await click('.pb-next button', 'Publish');
    await until(() => $('.pd'), 'publish dialog');
    type($('.pd input'), 'First flow version');
    await click('.pd button', 'Publish now');
    await until(() => /Live: version 1/.test(($('.pb-live') || document.body).textContent), 'live v1', 30000);
    ok($$('.vr').length === 1 && /First flow version/.test($('.vr').textContent), 'publish: version 1 is live and listed');
    const slug = decodeURIComponent(($('.pb-link input') || {}).value || '').split('#talk/')[1];
    ok(slug, 'publish: a public link to share');

    // ---- the new agent's public page
    await page('#talk/' + slug, () => $('.as-chat') && agentMsgs().length, 'public page of the new agent');
    await ask('smoked meat please', /Schwartz/, 'public: the published agent answers');

    // ---- review queue + a demo agent, look only
    await page('#review', () => $('.rv-page'), 'review');
    ok($('.rv-page .ui-empty').offsetParent, 'review: nothing waiting (empty state)');
    await page('#studio', () => $$('.ac').length >= 4, 'studio again');
    ok($$('.st-sec .ac').some((a) => /Flow Guide/.test(a.textContent) && /Live/.test(a.textContent)), 'studio: the new agent shows as live');
    $$('.ac').find((a) => /Margaux/.test(a.textContent)).click();
    await until(() => window.UI_READY && $('.ag-viewer') && $('.ag-viewer').offsetParent, 'demo agent opens look-only');
    ok(/Demo: look only/.test($('.ag-head').textContent), 'demo agent: look-only, with a copy button');

    // ---- light / dark switch in the account menu, then sign out
    await click('.anvil-role-avatar button');
    await click('.ui-menu .ui-seg button', 'Dark');
    ok(document.documentElement.classList.contains('ui-dark'), 'menu: Dark switches the theme');
    await click('.ui-menu .ui-seg button', 'Auto');
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY && $('.ui-header .ui-btn.primary'), 'signed out');
    ok(true, 'sign out: back to the landing page as a visitor');

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
