# SDK Explorer Dashboard

An interactive Streamlit app to browse and test all SDK endpoints — no code required.

## Setup

```bash
cd dashboard
pip install -r requirements.txt
```

## Run

```bash
SYNUP_API_KEY=your_api_key streamlit run app.py
```

Opens at [http://localhost:8501](http://localhost:8501).

## Features

- **Browse by category** — Locations, Listings, Reviews, Analytics, Users, etc.
- **Search** — Find any endpoint by name
- **Auto-generated forms** — Input fields are built from method signatures
- **Execute & inspect** — Call any endpoint and see the JSON response
- **Error details** — Full error messages with HTTP status and response body

## Screenshot

After launching, you'll see:

1. **Sidebar** — API key input, category filter, search
2. **Main area** — Select an endpoint, fill in parameters, hit Execute
3. **Response** — JSON result displayed below
