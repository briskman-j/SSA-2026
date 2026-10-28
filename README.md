# The Alliance Dispatch — Super Smash Alliance 10.0 (`SSA-2026`)

Official static sports broadsheet, 15-year franchise lore archive (2012–2026), and weekly roast site for **The Super Smash Alliance 10.0** (ESPN League `1000567`).

**Live Site:** https://briskman-j.github.io/SSA-2026/

## Shareable Per-Edition Group-Chat Links
Every edition has its own dedicated URL and custom OpenGraph iMessage / WhatsApp preview card:
- **Midseason State of the Alliance Roast (Weeks 1–7 + 15-Year Team Names vs. Rings Chart):** https://briskman-j.github.io/SSA-2026/recaps/midseason/
- **Week 7 Recap:** https://briskman-j.github.io/SSA-2026/recaps/week-7/
- **Weeks 1–6 Archive:** `/recaps/week-1/` through `/recaps/week-6/`
- **Direct Friend Roast Deep-Link:** append `?team=<TEAM_ID>` (e.g. `https://briskman-j.github.io/SSA-2026/recaps/midseason/?team=1` for Kyle Feeney)

## Automated & Manual Weekly Updates
1. **Zero-Touch GitHub Action (Every Tuesday Morning):**
   `.github/workflows/weekly-espn-sync.yml` runs automatically every Tuesday at 9:15 AM ET (or on-demand via **Actions → Weekly ESPN Recap Sync → Run workflow**) to pull live ESPN scores and publish `/recaps/week-8/`, `/recaps/week-9/`, etc.
2. **Local CLI Update (with Custom Weekly Roast Headlines):**
   Edit `WEEKLY_EDITORIALS` or `TEAM_ROASTS` in `build_alliance_site.py`, then run:
   ```bash
   python3 build_alliance_site.py --fetch
   git add -A && git commit -m "Publish weekly roast" && git push
   ```
