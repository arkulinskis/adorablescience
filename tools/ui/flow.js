/* The main journey, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs:
   a visitor reads the front page and plays the video; a writer joins, drafts an article with a source and a
   citation, previews it, meets the "no sources?" dialog, submits, withdraws and resubmits; the Lab Director sends it
   back with a note, the writer sees the note and resubmits, the Director approves and features it; it leads the
   front page and gets a boop. Resolves to {ok, log}. Keep log lines ASCII. Helpers: tools/ui/lib.js (window.T). */
(async function () {
  const { $, $$, until, click, type, page, sleep, vis, text } = T;
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };
  const btn = (re) => $$('.anvil-role-btn button').find((b) => vis(b) && re.test(b.textContent));
  const dialogBtn = async (re) => { const b = await until(() => $$('.modal-footer button, .anvil-modal-footer button, .anvil-modal-content button').find((x) => vis(x) && re.test(x.textContent)), 'dialog button ' + re); b.click(); };
  const stamp = Date.now();
  const title = 'Flow tardigrades ' + stamp;
  const email = 'flow' + stamp + '@example.com', pw = 'Hb-flow-' + stamp + '-Kq7';
  try {
    // ---- the front page (visitors): the starter articles publish themselves on the first visit
    await page('#', () => $('.as-hero') && $('.as-lead') && vis($('.as-lead')));
    ok($$('.as-filter').length === 10, 'front: Everything + 9 field filters');
    ok($$('.anvil-role-cards .as-card').length >= 4 && /(Featured|Latest) discovery/.test(text($('.as-lead-flag'))), 'front: the starters (a lead story + cards)');
    ok($('.as-footer a[data-prepsto-open][href*="7uhztrz"]') && $('.as-footer [data-lk-open]') && /arkvital\.com/.test(text($('.as-footer'))) && /addanapp\.com/.test(text($('.as-footer'))), 'footer: feedback, Privacy & Terms, arkvital.com, addanapp.com');
    $('.ytf-cover').click();
    await until(() => $('.ytf-frame iframe[src*="youtube-nocookie.com/embed/eoGeoGcAmg8"]'), 'the video player');
    ok(true, 'watch: play swaps the cover for the YouTube player');
    type($('.as-search input'), 'wombat'); btn(/^Search$/).click();
    await until(() => /result/.test(text($('.as-section'))) && !vis($('.as-hero')), 'search results');
    ok($$('.anvil-role-cards .as-card').length >= 1, 'search: finds the wombat starter');
    await page('#topic/space', () => $('.as-filter-on') && /Space/.test(text($('.as-filter-on'))));
    ok(true, 'field filter: #topic/space');

    // ---- the Lab Director account exists (first account on this database)
    await T.director();
    ok(true, 'director: signed in, has the Review desk tab');
    await T.signOut();

    // ---- members-only page asks a visitor to join, then comes back
    window.UI_READY = false; location.hash = '#write';
    await until(() => location.hash === '#join/write' && window.UI_READY && T.fields().length === 2, 'sent to #join/write');
    ok(true, '#write sends visitors to #join/write');
    await T.signUp(email, pw, '#join/write');
    await until(() => location.hash === '#write' && window.UI_READY && $('.as-editor'), 'back on the writing desk', 40000);
    ok(!$$('.as-nav a').some((a) => /Review desk/.test(a.textContent)), 'sign-up: back on #write, a writer (no Review desk)');

    // ---- the writing desk
    const tb = $('.as-editor-main input'), [dek, body] = $$('.as-editor-main textarea');
    type(tb, title);
    ok(!/^0\//.test(text($('.as-field-label i'))), 'editor: the headline counter counts');
    type(dek, 'Water bears shrug off the vacuum of space, and here is the study.');
    type(body, 'Tardigrades are tiny animals that can survive almost anything. Scientists sent them into space and many came back alive. ');
    const selects = $$('.as-editor-side select');
    selects[0].value = selects[0].querySelectorAll('option')[1].value; selects[0].dispatchEvent(new Event('change', { bubbles: true }));
    selects[1].value = selects[1].querySelectorAll('option')[2].value; selects[1].dispatchEvent(new Event('change', { bubbles: true }));
    $$('.as-covers .as-cover')[3].click();
    await until(() => $$('.as-covers .as-cover-on').length === 1, 'cover picked');
    ok($$('.as-covers .as-cover')[3].getAttribute('aria-pressed') === 'true', 'editor: cover critter picked (aria-pressed)');
    ok(/Pure hypothesis/.test(text($('.as-meter-label'))), 'meter: no sources = Pure hypothesis');
    btn(/Submit for review/).click();
    await until(() => $('.as-dialog') && /No sources yet/.test(text($('.as-dialog'))), 'the no-sources dialog');
    ok(true, 'submit without sources: the dialog asks first');
    btn(/Add a source/).click();
    await until(() => !$('.as-dialog') && $$('.as-src').length === 2, 'a second source row');
    ok(true, 'dialog: Add a source adds a row');
    type($$('.as-src input[type=url]')[0], 'https://doi.org/10.1016/j.cub.2008.06.048');
    type($$('.as-src input[type=text]')[0], 'Tardigrades survive exposure to space');
    await until(() => /Single specimen/.test(text($('.as-meter-label'))), 'meter: Single specimen');
    ok(true, 'meter: one source = Single specimen');
    $$('.as-src')[1].querySelector('.anvil-role-iconbtn button').click();
    await until(() => $$('.as-src').length === 1, 'row removed');
    ok(true, 'sources: remove a row');
    body.focus(); body.setSelectionRange(body.value.length, body.value.length);
    btn(/Cite \[1\]/).click();
    await until(() => /\[1\]/.test(body.value), 'citation inserted');
    await until(() => /1 cited inline/.test(text($('.as-meter-count'))), 'meter counts the citation');
    ok(true, 'cite [1]: inserted and counted');
    $$('.as-fmt')[0].click();
    ok(/\*\*important words\*\*/.test(body.value), 'format: Bold wraps a placeholder');
    await click('.as-tab2', /Preview/);
    await until(() => vis($('.as-preview')) && $('.as-preview strong') && $('.as-preview .as-cite a'), 'the preview');
    ok(true, 'preview: rendered by the server with the citation link');
    await click('.as-tab2', /Write/);
    btn(/Save draft/).click();
    await until(() => /^#write\/\d+$/.test(location.hash) && /Editing specimen/.test(text($('.as-pagehead h1'))), 'saved as a draft');
    const no = location.hash.split('/')[1];
    ok(true, 'save draft: the address becomes #write/' + no);
    btn(/Submit for review/).click();
    await until(() => location.hash === '#lab' && window.UI_READY && /Under the microscope/.test(text($('.as-main'))), 'on My lab');
    ok($$('.as-labrow').some((r) => r.textContent.includes(title)), 'submit: the article waits under the microscope on My lab');
    btn(/Withdraw/).click();
    await dialogBtn(/Withdraw/);
    await until(() => /In the Petri dish/.test(text($('.as-main'))) && !btn(/Withdraw/), 'withdrawn');
    ok(true, 'withdraw: back in the Petri dish');
    await page('#write/' + no, () => $('.as-editor'));
    btn(/Submit for review/).click();
    await until(() => location.hash === '#lab' && window.UI_READY && btn(/Withdraw/), 'resubmitted');
    await T.signOut();

    // ---- the Lab Director sends it back
    await T.director();
    ok(/\d/.test(text($('.as-nav .as-badge'))), 'header: the Review desk tab counts what is waiting');
    await page('#review', () => $$('.as-labrow').length);
    ok($$('.as-labrow').some((r) => r.textContent.includes(title)), 'review desk: the article is in the queue');
    await page('#review/' + no, () => $('.as-decide') && vis($('.as-decide')));
    ok($$('.as-check-row').length === 7 && /Single specimen/.test(text($('.as-meter-label'))), 'review: checklist (7) + meter');
    btn(/Send back/).click();
    await sleep(800);
    ok(location.hash === '#review/' + no, 'send back without a note is refused');
    type($('.as-decide textarea'), 'Lovely! Could you add a second source?');
    btn(/Send back/).click();
    await until(() => location.hash === '#review' && window.UI_READY, 'back on the desk');
    await T.signOut();

    // ---- the writer sees the note and resubmits; a wrong password first
    ok(!(await T.signIn(email, 'wrong-password-1')) && $$('.anvil-role-msg-error').some(vis), 'sign in with a wrong password shows the error');
    ok(await T.signIn(email, pw), 'the writer signs in again');
    await page('#lab', () => $('.as-labrow'));
    ok(/Needs more data/.test(text($('.as-main'))) && /second source/.test(text($('.as-labrow .as-reviewnote'))), 'my lab: sent back, with the reviewer note');
    await page('#write/' + no, () => $('.as-editor'));
    ok(vis($('.as-reviewnote')) && /Resubmit/.test(btn(/submit for review/i).textContent), 'editor: the note + Resubmit');
    btn(/Resubmit/).click();
    await until(() => location.hash === '#lab' && window.UI_READY, 'resubmitted');
    await T.signOut();

    // ---- the Director approves and features it
    await T.director();
    await page('#review/' + no, () => $('.as-decide') && vis($('.as-decide')));
    ok(vis($('.as-notebook')) && /Sent back/.test(text($('.as-notebook'))), 'review: the lab notebook shows the history');
    $('.anvil-role-as-check input').click();
    btn(/Approve/).click();
    await until(() => location.hash === '#review' && window.UI_READY, 'approved');
    ok(true, 'approve with Feature ticked');
    await page('#', () => $('.as-lead') && vis($('.as-lead')));
    ok(text($('.as-lead h2')) === title && /Featured/.test(text($('.as-lead-flag'))), 'front: the approved article leads, featured');

    // ---- reading it: boop; the desk's other lists; writers
    await page('#article/' + no, () => $('.as-boop'));
    ok(/Copy link/.test(btn(/Copy link/).textContent) && vis($('.as-refs')), 'article: sources list + copy link');
    $('.as-boop').click();
    await until(() => $('.as-boop').getAttribute('aria-pressed') === 'true' && text($('.as-boop b')) === '1', 'booped');
    ok(true, 'boop: counted and pressed');
    await page('#review', () => $$('.as-tab2').length >= 3);
    await click('.as-tab2', /Published/);
    await until(() => btn(/Featured/), 'the published list');
    ok(true, 'review desk: published list with the featured article');
    await click('.as-tab2', /Lab members/);
    await until(() => $$('.as-labrow').some((r) => r.textContent.includes(email)), 'members');
    ok(true, 'review desk: members list shows emails to Directors');
    await page('#writers', () => $$('.as-wcard').length);
    ok($$('.as-wcard').some((c) => c.textContent.includes('published')), 'writers: the roster');
    await T.signOut();
    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
