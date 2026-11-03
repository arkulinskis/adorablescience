# Starters: five short, sourced articles a Lab Director can publish into an empty lab, so the front page isn't bare
# on launch day. They're bylined "Adorable Science team" (an account nobody can sign in to) and say so in a lab note.
# Every study was checked against its DOI record (Crossref) on 2026-11-03; keep claims to what the papers report.
from anvil.tables import app_tables

from .Lab import api, Oops, me, now, log, next_specimen_no, _rand_uid
from . import lab_config as C

TEAM_EMAIL = "team@adorablescience.invalid"  # .invalid: never a real inbox, and no password, so no one can sign in
TEAM = dict(display_name="Adorable Science team", avatar="🦉", specialty="The lab's own writers",
            bio="Starter articles from the people who run Adorable Science, drafted with AI help and checked against "
                "the original studies. Spot a mistake? Use Submit feedback at the bottom of any page.")
NOTE = ("\n\n!! A starter article from the Adorable Science team, here so the lab isn't empty on day one. "
        "Got a better story? Write one: every article is reviewed by a Lab Director before it goes live.")

STARTERS = [
    dict(
        title="Why wombat poop comes out in cubes",
        dek="Wombats are the only animals known to make cube-shaped droppings. Engineers worked out how a soft, "
            "round gut manages it.",
        category="critters", evidence="peer", cover="🧪",
        body="""Bare-nosed wombats leave neat little cubes of poop on rocks and logs, and for a long time nobody knew how a round, squishy intestine could make corners.

## Stiff bits and soft bits
A team led by Patricia Yang and David Hu studied the intestines of wombats that had died in road accidents. They found that the wall of the intestine isn't equally stretchy all the way round: some bands are stiffer and some are softer. As the gut squeezes the drying poop along, the stiff and soft bands push on it differently, and that difference carves flat sides and sharp corners [1].

## A prize for the poop
Earlier work by the same group won the 2019 Ig Nobel Prize in Physics, the award for research that "makes people laugh, then think" [2]. The researchers suggest the trick could even inspire new ways of making shapes in factories, without moulds or cutting [1].

## Why cubes?
Wombats use their droppings to mark their patch, often on raised spots. Cubes are less likely to roll away than balls, which is one idea for why the shape stuck, though the study itself is about *how*, not *why* [1].""",
        sources=[
            dict(url="https://doi.org/10.1039/D0SM01230K", kind="journal", publisher="Soft Matter (2021)",
                 title="Intestines of non-uniform stiffness mold the corners of wombat feces"),
            dict(url="https://improbable.com/ig/winners/#ig2019", kind="other", publisher="Improbable Research",
                 title="Ig Nobel Prize winners, 2019 (Physics)"),
        ]),
    dict(
        title="Dogs grew a special muscle for puppy-dog eyes",
        dek="A tiny eyebrow muscle that wolves mostly lack lets dogs make the face that melts us. Shelter dogs that "
            "use it more get adopted faster.",
        category="critters", evidence="peer", cover="🧬",
        body="""You know the look: eyebrows up, eyes big and sad. It turns out dogs have the anatomy for it and their wild cousins mostly don't.

## The eyebrow muscle
Juliane Kaminski and colleagues compared the faces of dogs and grey wolves. Dogs had a well-formed muscle that lifts the inner eyebrow (its name is *levator anguli oculi medialis*). In wolves, the same muscle was absent or only a thin scattering of fibres [1]. The team thinks people, perhaps without meaning to, favoured dogs that could make this expressive face during thousands of years of living together.

## It pays off at the shelter
An earlier study filmed dogs in rescue shelters meeting a stranger. The dogs that raised their inner eyebrows more often were rehomed sooner, while wagging and other behaviours made little difference [2].

!! Raising the inner eyebrow makes eyes look bigger and a bit sad, a bit like a human baby's face. That's thought to be part of why it works on us [1].""",
        sources=[
            dict(url="https://doi.org/10.1073/pnas.1820653116", kind="journal", publisher="PNAS (2019)",
                 title="Evolution of facial muscle anatomy in dogs"),
            dict(url="https://doi.org/10.1371/journal.pone.0082686", kind="journal", publisher="PLoS ONE (2013)",
                 title="Paedomorphic facial expressions give dogs a selective advantage"),
        ]),
    dict(
        title="Water bears went to space and lived",
        dek="Dried-out tardigrades rode outside a spacecraft for ten days in orbit. Many came home and laid eggs.",
        category="space", evidence="established", cover="🛰️",
        body="""Tardigrades, or water bears, are eight-legged animals smaller than a grain of sand. When their home dries out they curl up into a dry 'tun' and wait, sometimes for years.

## The experiment
In 2007 a team led by Ingemar Jönsson sent dried tardigrades into low Earth orbit on the European FOTON-M3 mission. For ten days some were exposed to the vacuum of space, and some to vacuum plus the Sun's ultraviolet light [1].

## What happened
- **Vacuum alone** barely bothered them: after being rehydrated back on Earth, they survived about as well as tardigrades that stayed home [1].
- **Vacuum plus full sunlight** was much harder: most died, but a few animals of one species (*Milnesium tardigradum*) survived even that [1].
- Animals that had been through the vacuum went on to lay eggs that hatched normally [1].

It was the first time any animal was shown to survive the combined vacuum and radiation of open space [1].""",
        sources=[
            dict(url="https://doi.org/10.1016/j.cub.2008.06.048", kind="journal", publisher="Current Biology (2008)",
                 title="Tardigrades survive exposure to space in low Earth orbit"),
        ]),
    dict(
        title="Rats giggle when tickled, and their brains show it",
        dek="Tickled rats squeak in ultrasound and chase the tickling hand. Neuroscientists found the brain cells "
            "behind it.",
        category="brain", evidence="peer", cover="🧠",
        body="""Rats can't laugh the way we do, but when you tickle them they make fast, high squeaks, around 50 kHz, far too high for us to hear without a bat detector.

## Inside a ticklish brain
Shimpei Ishiyama and Michael Brecht tickled rats on the back and belly and recorded neurons in the part of the brain that handles touch (the somatosensory cortex). Many of those cells fired strongly during tickling and even during play, when the rats chased the researcher's hand. Gently stimulating the same area with electricity made the rats squeak on their own [1].

## Mood matters
Rats that were anxious, for example placed on a raised platform under bright light, squeaked far less when tickled, and their 'tickle' neurons were quieter too. It's a lot like people: you're only ticklish when you feel safe [1].

!! Tickled rats often come back for more: in the study they chased the researcher's hand to be tickled again [1].""",
        sources=[
            dict(url="https://doi.org/10.1126/science.aah5114", kind="journal", publisher="Science (2016)",
                 title="Neural correlates of ticklishness in the rat somatosensory cortex"),
        ]),
    dict(
        title="Bumblebees roll tiny balls just for fun",
        dek="With no food on offer, bumblebees kept rolling little wooden balls around. Researchers say it ticks "
            "every box for play.",
        category="critters", evidence="peer", cover="🐝",
        body="""Play is easy to spot in puppies and kittens. But insects? A study from Queen Mary University of London says bumblebees do it too.

## The ball pit
Samadi Galpayage Dona and colleagues set up an arena where bumblebees could walk to a feeder. Off to the side were small wooden balls. Many bees went out of their way to roll the balls, again and again, even though rolling them earned no food and the path to the feeder was clear [1].

## Does it count as play?
Scientists use a checklist for play: it isn't needed for survival, it's done for its own sake, it's repeated, it happens when the animal is relaxed and well fed, and it's different from serious behaviour. The ball rolling met all of these [1].
- **Young bees** rolled more balls than older ones, like young mammals that play more [1].
- In another test, bees preferred a coloured room where they had found balls before, over one that had been empty [1].

!! The researchers think play may point to positive emotional states in bees. Nobody is saying bees feel joy exactly the way we do, but their inner lives may be richer than we thought [1].""",
        sources=[
            dict(url="https://doi.org/10.1016/j.anbehav.2022.08.013", kind="journal", publisher="Animal Behaviour (2022)",
                 title="Do bumble bees play?"),
        ]),
]


def _team():
    u = app_tables.users.get(email=TEAM_EMAIL)
    if u is None:
        u = app_tables.users.add_row(email=TEAM_EMAIL, enabled=False, signed_up=now(), uid=_rand_uid(), is_admin=False,
                                     website="", **TEAM)
    return u


@api(admin=True)
def load_starter_articles():
    """Publish the starter articles, only while the front page is empty. Returns how many were added."""
    if len(app_tables.articles.search(status="published")):
        raise Oops("The front page already has articles, so the starters aren't needed.")
    return {"made": _publish(me())}


def ensure_starters():
    """The user asked for the starters to go live without a click (Nov 3 2026): the first front-page visit to an empty
    lab publishes them, once. Once the team account exists this never runs again, even if they're all taken down."""
    if len(app_tables.articles.search(status="published")) or app_tables.users.get(email=TEAM_EMAIL) is not None:
        return 0
    return _publish(None)


def _publish(reviewer):
    team = _team()
    have = {a["title"] for a in app_tables.articles.search(author=team)}
    made = 0
    for i, s in enumerate(STARTERS):
        if s["title"] in have:
            continue
        body = s["body"] + NOTE
        cited = [n for n in C.cited_numbers(body) if 1 <= n <= len(s["sources"])]
        a = app_tables.articles.add_row(
            specimen_no=next_specimen_no(), author=team, created=now(), updated=now(), submitted_at=now(),
            published_at=now(), status="published", reviewer=reviewer, review_note="Starter article", featured=(i == 0),
            boops=0, title=s["title"], dek=s["dek"], body=body, category=s["category"], evidence=s["evidence"],
            cover=s["cover"], n_sources=len(s["sources"]), n_cited=len(cited),
            reading_min=max(1, int(round(len(body.split()) / 200.0))))
        for k, src in enumerate(s["sources"]):
            app_tables.sources.add_row(article=a, position=k, **src)
        log(a, "approved", "Starter article")
        made += 1
    return made
