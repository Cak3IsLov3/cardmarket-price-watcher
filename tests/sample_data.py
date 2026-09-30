"""Real API responses captured during the spikes, shared by all tests."""

# Scryfall /cards/named response for Sol Ring (Commander Masters), trimmed to the fields we use
SOL_RING = {
    "object": "card",
    "id": "46ca0b66-a000-4483-b916-f5b89e710244",
    "name": "Sol Ring",
    "set": "cmm",
    "set_name": "Commander Masters",
    "cardmarket_id": 721733,
}

# Real entry for Sol Ring (Commander Masters) from the spike
SOL_RING_ENTRY = {
    "idProduct": 721733,
    "idCategory": 1,
    "avg": 1.04,
    "low": 0.48,
    "trend": 0.92,
    "avg1": 0.75,
    "avg7": 1.01,
    "avg30": 1.04,
    "avg-foil": 3.53,
    "low-foil": 1.8,
    "trend-foil": 3.28,
    "avg1-foil": 2.99,
    "avg7-foil": 3.71,
    "avg30-foil": 2.97,
}

# Constructed (not real) second printing, cheaper than Commander Masters, for "any printing" tests
SOL_RING_OTHER = {
    "object": "card",
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "Sol Ring",
    "set": "c21",
    "set_name": "Commander 2021",
    "cardmarket_id": 555555,
}
SOL_RING_OTHER_ENTRY = {
    "idProduct": 555555,
    "idCategory": 1,
    "low": 0.30,
    "trend": 0.55,
    "avg30": 0.60,
}

# Digital-only printing: Scryfall has no cardmarket_id for these
SOL_RING_DIGITAL = {
    "object": "card",
    "id": "00000000-0000-0000-0000-000000000002",
    "name": "Sol Ring",
    "set": "vma",
    "set_name": "Vintage Masters",
    "digital": True,
}

SAMPLE_GUIDE = {
    "version": 1,
    "createdAt": "2026-09-30T09:54:57+0200",
    "priceGuides": [SOL_RING_ENTRY, SOL_RING_OTHER_ENTRY, {"idProduct": 1, "low": 0.02}],
}
