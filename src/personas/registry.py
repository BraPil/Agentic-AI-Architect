"""
Persona registry — derives PersonaProfile objects from live ChromaDB metadata.

No static config files required; profiles are computed from what is actually
indexed, so they stay fresh automatically as the corpus grows.
"""

from collections import Counter

from src.personas.models import PersonaProfile


def build_persona_profile(persona_id: str, store) -> PersonaProfile | None:
    """Derive a PersonaProfile from all indexed items for this persona_id.

    Returns None if no items exist for the given persona_id.
    """
    try:
        result = store._collection.get(
            where={"persona_id": persona_id},
            include=["metadatas"],
        )
    except Exception:  # noqa: BLE001
        return None

    ids = result.get("ids", [])
    if not ids:
        return None

    metas = result.get("metadatas", [])
    display_name = persona_id
    content_types: Counter = Counter()
    topics: Counter = Counter()
    tools: Counter = Counter()
    dates: list[str] = []

    for m in metas:
        if not m:
            continue
        if m.get("author"):
            display_name = m["author"]
        if m.get("post_type"):
            content_types[m["post_type"]] += 1
        for t in m.get("topics", "").split(","):
            t = t.strip()
            if t:
                topics[t] += 1
        for t in m.get("mentioned_tools", "").split(","):
            t = t.strip()
            if t:
                tools[t] += 1
        ts = m.get("timestamp") or m.get("scraped_at", "")
        if ts:
            dates.append(ts[:10])

    dates_sorted = sorted(dates)
    return PersonaProfile(
        persona_id=persona_id,
        display_name=display_name,
        item_count=len(ids),
        content_types=[ct for ct, _ in content_types.most_common()],
        top_topics=[t for t, _ in topics.most_common(10)],
        top_tools=[t for t, _ in tools.most_common(10)],
        date_range=(dates_sorted[0] if dates_sorted else "",
                    dates_sorted[-1] if dates_sorted else ""),
    )


def list_persona_profiles(store) -> list[PersonaProfile]:
    """Return a ProfileProfile for every persona_id in the store."""
    raw = store.get_personas()
    profiles = []
    for entry in raw:
        pid = entry if isinstance(entry, str) else entry.get("persona_id", "")
        if not pid:
            continue
        p = build_persona_profile(pid, store)
        if p:
            profiles.append(p)
    return profiles
