# Deploying EcoTrack for free (Hugging Face Spaces, Docker)

Why Spaces: free CPU with 16 GB RAM (PyTorch fits), no 15-minute sleep like Render/Koyeb free tiers
(a Space only pauses after 48 h without visitors), HTTPS included.

1. Create an account at https://huggingface.co and make a token: Settings -> Access Tokens -> *Write*.
2. **New Space** -> name `ecotrack` -> SDK **Docker** (Blank) -> **Public** -> hardware *CPU basic (free)*.
3. In the Space: **Settings -> Variables and secrets -> New secret**
   * `DJANGO_SECRET_KEY` = output of `python -c "import secrets;print(secrets.token_urlsafe(50))"`
   * optional: `OFFICER_USER` and `OFFICER_PASSWORD` (creates your own MC officer if the database has none)
4. From the project folder:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/ecotrack
   git push hf main        # username = your HF username, password = the Write token
   ```
5. Watch the **Logs** tab: the first build takes about 4-6 minutes. The app is live at
   `https://<your-username>-ecotrack.hf.space`

Notes
* The disk of a free Space is temporary: data created on the live site resets when the Space restarts.
  The committed `db.sqlite3` and `media/` are copied in on every start, so the demo data is always there.
* Open the link once ~5 minutes before the presentation so the Space is awake.
* Local development is unchanged (`python manage.py runserver` uses `config.settings`).
