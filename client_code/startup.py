"""The app starts here (anvil.yaml: startup module). One server call to learn who is signed in (Anvil's loading
spinner, Bea the bubbling beaker, shows meanwhile), the Privacy & Terms kit, then the page for the address."""
import anvil.server

from . import legal, router, state

LEGAL_THEME = {"accent": "#6c4fd8"}  # colours for the Privacy & Terms page (match --as-lav-deep in app.css)

legal.setup(LEGAL_THEME)
state.set_me(state.call("get_me"))
legal.refresh_soon()  # Privacy & Terms: records the sign-up tick, or reminds people to review
router.start()
