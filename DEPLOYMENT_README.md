# Sports Betting Command Center - Cloud Deployment

1. Commit the contents of this package to the public repository root (app.py at root).
2. In Streamlit Community Cloud, create an app pointing to main / app.py.
3. In the Streamlit app settings > Secrets, add:
   GITHUB_READ_TOKEN = "YOUR_FINE_GRAINED_READ_ONLY_TOKEN"
   Grant the token **Actions: Read-only** and **Metadata: Read-only**, limited to this repository.
4. Restart the Streamlit app. NFL projections load from latest successful unexpired GitHub workflow artifact and cache for 15 minutes.
5. Do NOT paste the token in GitHub code, commits, or ChatGPT. The app is public, so research projections displayed in the UI are public.
6. Existing GitHub Actions workflow remains unchanged and read-only. It does not publish projections into the repository.
7. Public backtest CSV is included because the dashboard requires it. Review it before pushing.

Caveats: GitHub artifacts expire after 30 days. If no valid artifact or secret exists, the panel displays a waiting message.
