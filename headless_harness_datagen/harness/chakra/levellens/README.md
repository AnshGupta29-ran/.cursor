# LevelLens

Engineering resume signal & IC leveling analyzer (FastAPI + Canvas UI).

```powershell
cd headless_harness_datagen/harness/chakra/levellens
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8000/ → **Load demo** or upload a resume + JD.

Match formula: `0.55*tfidf_cosine + 0.45*skill_coverage` (pure Python TF-IDF).
Seniority: weighted impacts + scope verbs + leadership + years → IC3–IC7.
