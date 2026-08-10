# Prompt Forge

Mid-layer between **task seeds** and the **Chakra harness**.

```text
task seed  →  classify category  →  load template  →  LLM expands unique PRD
                                                      ↓
                         original harness bootstrap (sandbox + lifecycle)
                                                      ↓
                              composed objective → ConversationRunner / Chakra
```

The forged **PLATFORM ADD-ON** specializes the product for synthetic diversity.
Harness lifecycle / sandbox rules stay intact and still win on execution policy.

## Layout

| Path | Role |
|------|------|
| `categories.py` | Category enum + keyword metadata |
| `templates/*.md` | Durable per-family templates (not short stubs) |
| `classifier.py` | Heuristic / optional LLM classification |
| `meta_prompt.py` | Instructions for the expansion LLM |
| `generator.py` | Calls LLM → unique platform prompt |
| `composer.py` | Merges add-on into `build_unified_pipeline_objective` |
| `cli.py` | `python -m prompt_forge ...` |

## Quick start

```bash
# From headless_harness_datagen/ with .env loaded (OPENAI_*)
python -m prompt_forge list
python -m prompt_forge show-template ecommerce
python -m prompt_forge classify "Build a network monitoring dashboard with latency charts"
python -m prompt_forge forge "Collaborative whiteboard for architecture studios" --out artifacts/forge_demo --print
```

Full harness composition:

```bash
python -m prompt_forge forge "Mini cloud storage for clinics" ^
  --compose --repo-path experiments/clinic_drive --out artifacts/forge_demo
```

Through `main.py`:

```bash
python main.py "Smart home dashboard with schedules" --forge-prompt
python main.py "Inventory system for a bike shop" --forge-prompt --forge-category ecommerce
```

Artifacts written under the run log (`logs/<run-id>/prompt_forge/`) when `--forge-prompt` is set:
`platform_prompt.md`, `platform_addon.md`, `forge_meta.json`, `composed_objective.md`.

## Backend usage

```python
from controller import OpenAICompatibleClient
from prompt_forge import compose_harness_objective

llm = OpenAICompatibleClient.from_env()
result = compose_harness_objective(
    repo_path=str(repo_dir),
    seed="Team chat for incident responders",
    llm=llm,
)
# result.composed_objective  → send to ConversationRunner
# result.platform_prompt     → unique PRD only
```

Or add-on only:

```python
from prompt_forge import forge_platform_prompt
generated = forge_platform_prompt(seed, llm, category="collaborative_realtime")
```

## Categories

`collaborative_realtime`, `storage_files`, `iot_automation`, `ai_ml`, `cms_content`,
`security_privacy`, `ecommerce`, `monitoring_ops`, `games`, `distributed_systems`,
`devops_infra`, `finance_productivity`, `generic_fullstack`.
