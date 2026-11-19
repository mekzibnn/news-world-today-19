[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/mekzibnn/news-world-today-19/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/mekzibnn/news-world-today-19/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

# The World Today — Thursday 19 November 2026

A one-page newspaper front page summing up the world's news of
Thursday 19 November 2026: 44 stories across 7 regions, with the day's
three lead stories (Trump, Xi and Putin meet in Shenzhen; GTA VI launches;
Anthropic debuts in the biggest IPO ever), a "Where it happened" world map
with numbered pins, a UTC timeline, the day in numbers, and a date check
listing the stories that were first reported on 18 November and so were
deliberately left out.

Entry for the [make.fun bounty](https://make.fun/bounty/news-image-20261119)
"Sum up 19 November's world news in one image".

## How the image was built

- `stories.json` — the 46 stories (11 lead stories with drawn panels, 33
  numbered briefs) plus the 10 date-check exclusions. Every lead story was
  checked against at least two independent sources; claims are attributed
  on the page (CONFIRMED / CLAIM / FORECAST tags with the source).
- `render.py` — builds `page.html` from `stories.json` (inline SVG panels,
  system fonts, no network) and screenshots it at exactly 1024×1024 with
  headless Chromium, with an overflow audit. Run it to regenerate
  `entry.png`.
- `main.py` — the entry program: a standard-library-only copy of
  `entry.png` to `/output/entry.png`. Deterministic by construction — two
  runs write identical bytes.

## Files

- `main.py` — entry program (Python 3.13, standard library only)
- `entry.png` — the image (1024×1024, PNG)
- `stories.json` — the news data
- `render.py`, `page.html` — the build pipeline
- `LICENSE` — MIT
