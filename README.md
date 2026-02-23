# Vinted Outfit Match

An AI-powered outfit recommendation prototype built on the Vinted second-hand fashion catalog.

## What it does

- **Browse** 40,000+ fashion items with filters (gender, category, occasion, season)
- **Click any item** to get 6 complementary matches based on colour harmony, occasion, and style
- **Build a complete outfit** — the engine assembles a full look (top, bottom, shoes, accessory) with a total price
- **Upload & Match** — describe an item you own via photo upload, dropdowns, or plain-text AI parsing (powered by Cohere) to find what pairs with it from the catalog

## Tech stack

- **Frontend**: Streamlit (multi-page app)
- **Matching engine**: Rule-based compatibility scoring (colour harmony, occasion, category roles)
- **AI parsing**: Cohere `command-r-plus` to extract structured attributes from natural language
- **Data**: Kaggle Fashion Product Images dataset, augmented with synthetic Vinted-style metadata (https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small?select=styles.csv)

## Project structure
```
Vinted_Outfit_Match/
├── app.py                  # Main page: browse + item detail
├── pages/
│   └── 2_Upload_and_Match.py  # Upload & match page
├── matching_engine.py      # Outfit compatibility logic
├── setup_data.py           # Data preparation script
├── data/
│   └── vinted_catalog.csv  # Processed catalog
│   └── styles.csv          # Unedited dataset
│   └── images/
│       └── All images (1163.jpg, ...)
├── assets/
│   └── vinted_logo.png
├── requirements.txt
├── .gitignore
└── README.md

```

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Assignment notes

This prototype was built for the *Prototyping Products with Data and AI* course at Esade (MIBA 2026). It demonstrates:
- Multi-page Streamlit architecture
- Rule-based AI matching engine
- LLM integration (Cohere) for natural language item parsing
- Product thinking: the "autofill from photo" feature is scaffolded as a v2 roadmap item for assignment 2