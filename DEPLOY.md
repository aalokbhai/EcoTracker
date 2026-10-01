# Deploy EcoTrack for free on Render

The AI photo check calls the **Google Gemini API**, so the server stays tiny (no PyTorch) and fits Render's
free 512 MB web service easily.

## 1. Push the code to GitHub
```bash
git add . && git commit -m "Add Render deployment" && git push origin main
```

## 2. Create the web service  (render.com -> sign up with GitHub -> New + -> **Web Service**)
Pick the `EcoTracker` repo (use *Web Service*, not *Blueprint*), then:

| Setting | Value |
|---|---|
| Language | Python 3 |
| Branch | main |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start Command | `sh start.sh` |
| Instance Type | **Free** |
| Health Check Path (Advanced) | `/healthz` |

**Environment variables**

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` (Django 6.1 needs Python 3.12+, Render's default is older) |
| `DJANGO_SETTINGS_MODULE` | `config.settings_prod` |
| `DJANGO_SECRET_KEY` | output of `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `GEMINI_API_KEY` | your free key from aistudio.google.com (**never** commit it to GitHub - `.env` is in `.gitignore`) |
| `GEMINI_API_KEYS` | optional back-up keys, comma separated (used automatically when the first key is over its quota) |
| `OFFICER_USER` / `OFFICER_PASSWORD` | optional - only used if the database has no MC officer |

Click **Create Web Service**. First build takes ~3-5 minutes. Live at `https://<name>.onrender.com`.

## 3. Keep it awake (free services sleep after 15 idle minutes and take ~1 minute to wake)
Make a free account on uptimerobot.com -> *Add New Monitor* -> type **HTTP(s)**, URL
`https://<name>.onrender.com/healthz`, interval 5 minutes. One always-on service uses ~744 of the
750 free hours per month, so keep this as your only Render service.

## Notes
* Disk is temporary: data created on the live site is lost on redeploy/restart. The committed `db.sqlite3`
  and `media/` come back every time, so the demo data is always there.
* Free Gemini keys have a small daily quota per model. `complaints/ai.py` tries several models in order and,
  if none can answer, the complaint is still saved as "Not checked" for the MC office. Check your quota at
  https://aistudio.google.com/rate-limit before the demo.
* Local development is unchanged: `python manage.py runserver` (uses `config.settings` and your `.env`).
