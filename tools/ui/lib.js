/* Shared helpers for the page scripts (tools/ui_test.py puts this file in front of every script, as window.T).
   T.director() signs in the local Lab Director (director@example.com), creating it if this database is new: on a
   fresh database the first account ever signed up becomes the first Lab Director, and ui_test.py starts every new
   container with a fresh database, so the director is always that first account. T.signUp() makes a new writer. */
window.T = (function () {
  const T = {};
  T.sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  T.$ = (s) => document.querySelector(s);
  T.$$ = (s) => Array.from(document.querySelectorAll(s));
  T.vis = (e) => !!e && e.getBoundingClientRect().width > 0 && !e.closest('[hidden]');
  T.until = async function (fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await T.sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  };
  T.text = (e) => (e ? e.textContent.trim().replace(/\s+/g, ' ') : '');
  T.byText = (sel, re) => T.$$(sel).filter(T.vis).find((e) => (re instanceof RegExp ? re.test(T.text(e)) : T.text(e) === re));
  T.click = async function (sel, re) {
    const el = await T.until(() => (re ? T.byText(sel, re) : T.$$(sel).find(T.vis)), sel + (re ? ' ' + re : ''));
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  };
  T.type = function (input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  };
  T.page = async function (hash, ready, what) {
    if ((location.hash || '#') !== hash) window.UI_READY = false;  // the old page stays until the router runs
    location.hash = hash;
    await T.until(() => window.UI_READY && (location.hash || '#') === hash && (!ready || ready()), what || hash, 60000);
    await T.sleep(400);
  };
  T.PW = 'Hb-local-director-Kq7-2026';
  T.DIRECTOR = 'director@example.com';
  T.fields = () => T.$$('.as-auth-card input[type=email], .as-auth-card input[type=password]').filter(T.vis);
  T.signedIn = () => !!T.$$('.anvil-role-btn button').find((b) => T.vis(b) && /Sign out/.test(b.textContent));
  T.submitJoin = () => T.$$('.as-auth-card .anvil-role-btn-primary button').find(T.vis).click();
  T.signIn = async function (email, pw) {
    await T.page('#join', () => T.fields().length === 2);
    T.type(T.fields()[0], email); T.type(T.fields()[1], pw);
    T.submitJoin();
    for (let i = 0; i < 60; i++) { await T.sleep(250); if (T.signedIn() && window.UI_READY) return true; if (T.$$('.anvil-role-msg-error').some(T.vis)) return false; }
    return T.signedIn();
  };
  T.signUp = async function (email, pw, where) {
    await T.page(where || '#join', () => T.fields().length === 2);
    await T.click('.as-auth-card .as-linkbtn', 'Create an account');
    await T.until(() => T.$('.as-auth-card .as-perks') && T.vis(T.$('.as-auth-card .as-perks')), 'sign-up form');
    T.type(T.fields()[0], email); T.type(T.fields()[1], pw || ('Hb-' + Math.random().toString(36).slice(2) + '-Kq7'));
    const tick = T.$$('.as-auth-card input[type=checkbox]').find(T.vis); if (tick && !tick.checked) tick.click();
    T.submitJoin();
    await T.until(() => T.signedIn() && window.UI_READY, 'signed up', 60000);
    await T.sleep(400);
  };
  T.signOut = async function () {
    if (!T.signedIn()) return;
    await T.click('.anvil-role-btn button', 'Sign out');
    await T.until(() => !T.signedIn() && window.UI_READY, 'signed out');
  };
  T.director = async function () {
    if (!(await T.signIn(T.DIRECTOR, T.PW))) await T.signUp(T.DIRECTOR, T.PW);
    await T.until(() => T.$$('.as-nav a').some((a) => /Review desk/.test(a.textContent)), 'the director has the Review desk tab');
  };
  return T;
})();
