from anvil import *

from ._anvil_designer import MascotTemplate

MOUTHS = {"happy": "M53 104 q7 7 14 0", "sad": "M53 108 q7 -6 14 0",
          "wow": "M57 104 a3 4 0 1 0 6 0 a3 4 0 1 0 -6 0"}


class Mascot(MascotTemplate):
    """Bea the Beaker (SVG). mood = happy / sad / wow (the mouth); size = a CSS class (as-brand-mark, as-mascot-sm,
    as-mascot-md, as-mascot-hero). Decorative: hidden from screen readers."""

    def __init__(self, **properties):
        self._mood, self._size, self._ready = "happy", "", False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        self.dom_nodes["svg"].setAttribute("class", ("as-mascot " + (self._size or "")).strip())
        self.dom_nodes["mouth"].setAttribute("d", MOUTHS.get(self._mood, MOUTHS["happy"]))

    @property
    def mood(self):
        return self._mood

    @mood.setter
    def mood(self, value):
        self._mood = value or "happy"
        self._draw()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value or ""
        self._draw()
