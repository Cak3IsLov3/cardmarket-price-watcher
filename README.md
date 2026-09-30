# Cardmarket Price Watcher

Price tracker for Magic: The Gathering cards on Cardmarket. Get a Discord alert when a card drops below your target price.

> Work in progress — Phase 1.

## Data sources

- **Cardmarket price guide** — the official daily JSON feed Cardmarket publishes for all users.
- **Scryfall API** — resolves card name + set to Cardmarket's `idProduct`.

This project started as a web scraper, but Cardmarket's product pages are protected by Cloudflare and their terms prohibit scraping. It now uses the official data feed instead.
