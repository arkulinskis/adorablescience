/* For screenshots of member pages: sign in as the Lab Director and leave one article waiting for review (the run's
   flow.js made the rest). Resolves to window.SEED = {review: '#review/<no>', writer: '#writer/<uid>'}. */
(async function () {
  const { $, $$, until, type, page, vis } = T;
  try {
    await T.director();
    await page('#write', () => $('.as-editor'));
    type($('.as-editor-main input'), 'Screenshot: octopuses taste with their arms');
    type($$('.as-editor-main textarea')[0], 'Octopus suckers carry receptors that taste what they touch.');
    type($$('.as-editor-main textarea')[1], 'Octopuses can taste with their arms. Each sucker has chemical receptors, so touching is tasting [1].');
    const s = $$('.as-editor-side select');
    // (Anvil's DropDown option values are its own, not the keys: pick by the visible text)
    const pick = (sel, re) => { sel.value = Array.from(sel.options).find((o) => re.test(o.textContent)).value; sel.dispatchEvent(new Event('change', { bubbles: true })); };
    pick(s[0], /Critters/); pick(s[1], /peer-reviewed/);
    type($('.as-src input[type=url]'), 'https://doi.org/10.1016/j.cell.2020.09.008');
    $$('.anvil-role-btn button').find((b) => vis(b) && /Submit for review/.test(b.textContent)).click();
    await until(() => location.hash === '#lab' && window.UI_READY, 'submitted', 60000);
    const row = $$('.as-labrow').find((r) => /octopuses/.test(r.textContent));
    const no = row.querySelector('a[href^="#article/"]').getAttribute('href').split('/')[1];
    window.SEED = { review: '#review/' + no, writer: $('.as-me').getAttribute('href') };
    return window.SEED;
  } catch (e) {
    return { error: String(e && e.message || e) };
  }
})();
