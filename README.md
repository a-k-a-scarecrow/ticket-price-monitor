# Ticket Price Monitor

Scans Ticketmaster and SeatGeek every hour for concerts on your watchlist
and pings you on Discord the moment a price drops to (or below) what
you're willing to pay. Runs entirely free on GitHub Actions — no server,
no always-on computer.

**StubHub is not automatically scanned.** Its search endpoints are
protected by AWS WAF bot-detection (verified while building this — plain
requests get an immediate blocked response), and defeating that
deliberately isn't something this tool does. Instead, every notification
includes a direct StubHub search link so you can check it yourself in one
tap.

## How it works

1. **`config/watchlist.yaml`** — you list the concerts you care about:
   artist, city, date, and your max price.
2. **GitHub Actions** runs `python -m ticket_monitor.main` every hour
   (`.github/workflows/ticket_monitor.yml`), pulling API keys from repo
   Secrets.
3. The script queries the **Ticketmaster** and **SeatGeek** APIs for each
   watchlist entry, and if any listing's price is at or under your max, it
   posts to your **Discord webhook** with the site, price, ticket link, and
   quantity available (when the API reports one).
4. **`state.json`** remembers the last price it alerted you about per
   (event, site), so you get pinged again only when the price actually
   changes — not every hour it stays the same. The workflow commits this
   file back to the repo after each run.

## One-time setup

### 1. Get a free Ticketmaster API key
Go to https://developer.ticketmaster.com/ → sign up → create an app. You
get an API key instantly (Consumer Key). Free tier: 5,000 calls/day, plenty
for hourly scans of a personal watchlist.

### 2. Get a free SeatGeek client ID
Go to https://seatgeek.com/account/develop → register an app. You get a
`client_id` instantly — no approval wait, no client_secret needed for this
tool (it only does read-only searches).

### 3. Create a Discord webhook
1. In Discord, go to the server/channel you want alerts in → channel
   Settings → **Integrations** → **Webhooks** → **New Webhook**.
2. Name it (e.g. "Ticket Alerts"), copy the **Webhook URL**.
3. Make sure you have the Discord app installed on your phone and/or
   laptop with notifications enabled for that channel, so you actually see
   the push.

### 4. Push this project to GitHub
This folder is a plain directory, not yet a git repo connected to GitHub.
From inside `ticket-price-monitor/`:

```bash
git init
git add .
git commit -m "Initial commit: ticket price monitor"
gh repo create ticket-price-monitor --private --source=. --remote=origin --push
```

(Or create the repo manually on GitHub and `git remote add origin <url>`
then `git push -u origin main`.) **Make it a private repo** — your
watchlist doesn't need to be public, and this keeps the Actions bot's
commits out of view of anyone else.

### 5. Add your secrets to GitHub
In the GitHub repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add:

| Name | Value |
|---|---|
| `TICKETMASTER_API_KEY` | from step 1 |
| `SEATGEEK_CLIENT_ID` | from step 2 |
| `DISCORD_WEBHOOK_URL` | from step 3 |

### 6. Edit your watchlist
Edit `config/watchlist.yaml` with the concerts you want tracked, commit,
and push:

```yaml
- artist: "Chappell Roan"
  city: "Los Angeles"
  date: "2026-09-12"
  max_price: 150.00
```

Push the change — the next hourly run (or a manual trigger, see below)
picks it up automatically.

## Running it

- **Automatically**: once pushed to GitHub with secrets set, it runs every
  hour on its own via the `schedule` trigger in the workflow. No further
  action needed.
- **Manually, from GitHub**: repo → **Actions** tab → "Ticket Price
  Monitor" → **Run workflow**.
- **Manually, locally** (useful for testing before you push):
  ```bash
  cd ticket-price-monitor
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  export TICKETMASTER_API_KEY=your_key
  export SEATGEEK_CLIENT_ID=your_id
  export DISCORD_WEBHOOK_URL=your_webhook_url
  PYTHONPATH=src python -m ticket_monitor.main
  ```

## Notes and limits

- Ticketmaster's API returns a price *range* for an event, not individual
  listings, so "quantity available" is only reported for SeatGeek results.
- Matching is by artist keyword + city + exact date. If an artist plays
  multiple venues in the same city on the same day, you may get alerts for
  more than one.
- Re-notification happens only when the alerting price changes for a given
  (event, site) pair — you won't get spammed hourly for the same price.
- GitHub Actions free tier includes 2,000 minutes/month for private repos;
  an hourly run that takes under a minute uses well under that.
