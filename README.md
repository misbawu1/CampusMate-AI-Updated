# CampusMate

A beginner-friendly campus guide with a browser resource search, an optional Gemini AI question box, and a small Python command-line version.

## Open the browser app

1. Open this folder in VS Code.
2. Choose **Terminal → New Terminal**.
3. Install the browser AI dependency by running `python -m pip install -r requirements.txt`.
4. Run `python server.py`.
5. CampusMate opens in your browser at `http://127.0.0.1:8000`.
6. Keep the terminal open while you use the site. Press **Ctrl+C** there when you are finished.

If Windows does not recognize `python` in an already-open terminal, open a new terminal or restart VS Code. As a fallback, run `& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" -m pip install -r requirements.txt` and then `& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" server.py` in PowerShell.

## Publish the browser app on Render

The repository includes a `render.yaml` Blueprint. In Render, create a Blueprint from the `misbawu1/CampusMate-AI-Updated` repository and follow the prompts. When asked for `GEMINI_API_KEY`, enter it in Render's secure environment-variable form; never add it to GitHub or this file. The Blueprint uses Render's free web-service plan for this learning project.

Render's free web services sleep after 15 minutes without traffic and can take about a minute to wake up. Free services are intended for testing and hobby projects, not production use.

## Ask CampusMate with Gemini

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
2. Add it to Windows as a user environment variable named `GEMINI_API_KEY`. Do not put the key in `app.js` or share it.
3. Close and reopen VS Code so the server can read the new variable.
4. Install the dependency and start `server.py` using the steps above.

Before calling Gemini, the Python server searches `knowledge.json` locally using the question's meaningful words. It sends up to three matching resources along with the question in one Gemini request. This keeps campus answers grounded in the resource list while avoiding an extra Gemini round trip. If no campus resource matches, CampusMate says it could not find that information; general questions can still be answered normally.

The AI response streams as Gemini generates it using the low-latency `gemini-3.5-flash-lite` model with minimal thinking. Each API request has a 30-second timeout so a stalled request returns an error instead of waiting indefinitely. The request uses `store=False`, so the question is not saved in the API's interaction history. The regular browser keyword search works separately. Gemini API usage may be subject to account limits and billing.

The browser search and command-line version use the same `knowledge.json` campus information. The browser AI feature uses Google's `google-genai` Python package; the command-line search still uses only the Python standard library.

## How it is organized

- `index.html` provides the page structure.
- `styles.css` controls the colors, layout, and responsive appearance.
- `app.js` loads campus data, filters results, and sends AI questions to the Python server.
- `server.py` serves the browser files and sends AI questions to Gemini.
- `main.py` remains a simple command-line version for practicing Python.
- `tools.py` contains reusable functions for loading and searching information, including the AI question search.
- `knowledge.json` stores campus resources separately from the code.
- `requirements.txt` records the Gemini SDK needed for the browser AI feature.
