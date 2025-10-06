# app/utils/feed.py

from app.database.models.event import Event
from app.database.models.post import Post
from app.database.models.campaign import Campaign
from app.database.models.event import Event
from app.database.models.post import Post
import unicodedata


def get_feed_items(query=None):
    events = Event.query
    posts = Post.query
    campaigns = Campaign.query

    if query:
        events = events.filter(Event.title.ilike(f'%{query}%'))
        posts = posts.filter(Post.title.ilike(f'%{query}%') | Post.content.ilike(f'%{query}%'))
        campaigns = campaigns.filter(Campaign.title.ilike(f'%{query}%') | Campaign.description.ilike(f'%{query}%'))

    events = events.order_by(Event.date.desc()).all()
    posts = posts.order_by(Post.created_at.desc()).all()
    campaigns = campaigns.order_by(Campaign.created_at.desc()).all()

    feed = []

    feed += [{
        "type": "event",
        "item": e,
        "timestamp": e.date,
        "title": e.title,
        "description": e.description[:160] + "..." if e.description else "",
        "image": None,
        "url": f"/events/{e.id}"
    } for e in events]

    feed += [{
        "type": "post",
        "item": p,
        "timestamp": p.created_at,
        "title": p.title,
        "description": p.content[:160] + "..." if p.content else "",
        "image": None,
        "url": f"/dashboard/post/{p.id}/edit"
    } for p in posts]

    feed += [{
        "type": "campaign",
        "item": c,
        "timestamp": c.created_at,
        "title": c.title,
        "description": c.description[:160] + "..." if c.description else "",
        "image": None,
        "url": f"/campaigns/{c.id}"
    } for c in campaigns]

    feed.sort(key=lambda x: x["timestamp"], reverse=True)
    return feed

def _normalize(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def collect_search_text(obj) -> str:
    """Crea un testo unico per la ricerca full-text su item del feed."""
    parts = []
    for attr in ("title", "name", "description", "content", "location", "address", "city", "category"):
        val = getattr(obj, attr, None)
        if val:
            parts.append(str(val).strip().lower())

    skills = getattr(obj, "skills", None)
    if skills:
        if isinstance(skills, (list, tuple, set)):
            parts.extend(str(s).lower() for s in skills)
        else:
            parts.append(str(skills).lower())

    assoc = getattr(obj, "association", None)
    if assoc and getattr(assoc, "name", None):
        parts.append(assoc.name.strip().lower())

    return _normalize(" ".join(parts))

def matches_query(text: str, q: str) -> bool:
    """Verifica se tutti i token della query compaiono nel testo normalizzato."""
    norm_text = _normalize(text)
    tokens = [_normalize(t) for t in q.split() if t.strip()]
    return all(tok in norm_text for tok in tokens)