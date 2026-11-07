/* The Lab Director's desk beyond the main journey: feature / unfeature, take an article down (the note is required)
   and promote / demote a member; a writer can't open the desk. Resolves to {ok, log}. Helpers: tools/ui/lib.js. */
(async function () {
  const { $, $$, until, click, type, page, sleep, vis, text } = T;
  const log = [];
  const ok = (c, m) => { if (!c) throw new Error('FAILED: ' + m); log.push('ok   ' + m); };
  const btn = (re, root) => $$((root ? root + ' ' : '') + '.anvil-role-btn button').find((b) => vis(b) && re.test(b.textContent));
  try {
    await T.director();
    await page('#review', () => $$('.as-tab2').length >= 3);
    await click('.as-tab2', /Published/);
    await until(() => $$('.as-labrow').length && btn(/Take down/), 'published list');
    const rows = () => $$('.as-labrow');
    const n0 = rows().length;
    // feature the last one, then unfeature it
    const last = rows()[n0 - 1], name = text(last.querySelector('h3'));
    last.querySelector('.anvil-role-btn button').click();
    await until(() => { const r = rows().find((x) => text(x.querySelector('h3')) === name); return r && /Featured/.test(r.textContent); }, 'featured');
    ok(true, 'feature: the row says Featured');
    rows().find((x) => text(x.querySelector('h3')) === name).querySelector('.anvil-role-btn button').click();
    await until(() => { const r = rows().find((x) => text(x.querySelector('h3')) === name); return r && /☆ Feature/.test(r.textContent); }, 'unfeatured');
    ok(true, 'unfeature');
    // take it down: the note is required
    $$('.as-labrow').find((x) => text(x.querySelector('h3')) === name).querySelectorAll('.anvil-role-btn button')[1].click();
    await until(() => $('.as-dialog textarea'), 'the take-down dialog');
    btn(/Take down/, '.as-dialog').click();
    await until(() => $$('.as-dialog .anvil-role-msg-error').some(vis), 'note required');
    ok(true, 'take down: a note is required');
    type($('.as-dialog textarea'), 'One claim needs a source, please.');
    btn(/Take down/, '.as-dialog').click();
    await until(() => !$$('.as-dialog').some(vis) && rows().length === n0 - 1, 'taken down', 45000);
    ok(true, 'take down: it leaves the published list');
    // members: promote someone, then demote them again
    await click('.as-tab2', /Lab members/);
    await until(() => $$('.as-labrow').filter((r) => /@/.test(r.textContent)).length >= 2, 'members');  // (not the old list)
    const writerRow = () => $$('.as-labrow').find((r) => /Writer/.test(r.textContent) && /@example\.com/.test(r.textContent) && !/team@/.test(r.textContent));
    const email = (text(writerRow().querySelector('.as-break')).split(' ')[0]);
    writerRow().querySelector('.anvil-role-btn button').click();
    const rowOf = () => $$('.as-labrow').find((r) => r.textContent.includes(email));
    await until(() => /Remove Director/.test(rowOf().textContent), 'promoted');
    ok(true, 'members: Make Lab Director');
    rowOf().querySelector('.anvil-role-btn button').click();
    await until(() => /Make Lab Director/.test(rowOf().textContent), 'demoted');
    ok(true, 'members: Remove Director');
    await T.signOut();
    // a writer is turned away from the desk
    await T.signUp('desk' + Date.now() + '@example.com');
    await page('#review', () => $('.as-empty'));
    ok(/Lab Directors only/.test(text($('.as-empty'))), 'a writer sees "Lab Directors only" on #review');
    await T.signOut();
    log.push('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
