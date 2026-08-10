# ClerkLens

Cited extractive Q&A over municipal meeting packets (agenda / minutes / ordinance).

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5055/ → **Load Riverbend sample corpus** → **Ask**.

No scikit-learn (pure-Python TF-IDF). Flask only.

## Limitations
Stub LLM is extractive only; English tokenization; scanned PDFs unsupported; lexical TF-IDF ≠ semantic search; single-user local tool.
