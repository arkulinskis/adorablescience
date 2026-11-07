/* Phone-width check (run at 390 px wide by tools/ui_test.py): every page loads without errors and without sideways
   scrolling, signed out, then as the Lab Director (who sees every page). Resolves to {ok, log}. */
(async function () {
  const { $, $$, until, page, sleep } = T;
  const log = [], bad = [];
  async function check(hash, ready) {
    await page(hash, ready);
    await sleep(300);
    const w = document.documentElement.scrollWidth, vw = screen.width || window.innerWidth;
    const wide = $$('body *').filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > vw + 1; })
      .slice(0, 3).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ').slice(0, 2).join('.'));
    if (w > vw + 1) bad.push(hash + ' scrolls sideways (' + w + ' > ' + vw + ') ' + wide.join(' '));
    log.push((w > vw + 1 ? 'WIDE ' : 'ok   ') + hash + ' (' + w + ')');
  }
  try {
    await check('#', () => $('.as-hero'));
    await check('#topic/critters');
    await check('#writers');
    await check('#join', () => T.fields().length === 2);
    const card = $('.as-card .as-stretch') || $('.as-lead .as-stretch');
    if (card) await check(card.getAttribute('href'), () => $('.as-article'));
    await T.director();
    await check('#write', () => $('.as-editor'));
    await check('#lab');
    await check('#review');
    const q = $$('a[href^="#review/"]')[0];
    if (q) await check(q.getAttribute('href'), () => $('.as-editor'));
    await check('#me', () => $('.as-covers'));
    const me = $('.as-me');
    if (me) await check(me.getAttribute('href'), () => $('.as-profile'));
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
