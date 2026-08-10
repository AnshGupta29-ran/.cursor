"""Meta-prompt that tells the LLM how to expand a category template into a unique PRD."""

from __future__ import annotations

META_SYSTEM_PROMPT = """You are a synthetic platform prompt designer for an autonomous coding harness.

Your job is NOT to write code. Your job is to write a unique, detailed product
requirements prompt (PRD-style) that another coding agent will use to build a
complete repository from scratch.

Rules you MUST follow:
1. Use the category TEMPLATE as the shared shape for this family of platforms.
2. Specialize every section using the TASK SEED so the result is unique — not a
   copy of the template, and not a clone of common tutorial apps.
3. Invent concrete product identity: product name, audience, domain twist,
   distinctive workflows, and non-generic feature combinations.
4. Specify WHAT must exist (capabilities, entities, acceptance criteria), not
   step-by-step HOW to implement framework internals.
5. Target a lean MVP that a coding agent can ship in under ~25 minutes of work:
   auth only if essential, core entities, one primary journey, persistence,
   README, and a fast smoke test. Prefer fewer features done well.
6. Add uniqueness constraints: forbid generic "Todo app" / "Hello World" /
   placeholder-only UIs; require domain-authentic terminology.
7. Prefer realistic MVP quality (capstone / early startup), not a mockup and
   not an enterprise monolith.
8. Soft-suggest a reasonable tech stack only if the seed does not lock one;
   do not contradict an explicit stack in the seed. Prefer light local deps —
   never require torch/cuda downloads, Unity Hub installs, or multi-GB assets
   unless the seed explicitly demands that stack AND assumes it is preinstalled.
9. Keep the PLATFORM PROMPT concise: aim for 2.5k–6k characters. Cut fluff.
10. Output ONLY the final PLATFORM PROMPT in markdown. No preamble, no analysis,
    no surrounding XML, no "here is the prompt".
11. The output must be self-contained so it can be pasted under PROJECT OBJECTIVE
    in a harness bootstrap message.
"""


def build_expansion_user_message(
    *,
    category_id: str,
    category_title: str,
    template: str,
    seed: str,
    diversity_hint: str | None = None,
) -> str:
    diversity = diversity_hint or (
        "Vary naming, domain niche, secondary workflows, and UX emphasis so "
        "repeated runs of the same category do not converge on identical products."
    )
    return f"""## Category
id: {category_id}
title: {category_title}

## Diversity directive
{diversity}

## Category template (shared family shape — expand, do not parrot)
\"\"\"
{template}
\"\"\"

## Task seed (specialize from this)
\"\"\"
{seed.strip()}
\"\"\"

## Required output sections (adapt labels if needed, keep substance)
1. Project Request / Product identity
2. Target users & primary jobs-to-be-done
3. Core requirements / entities
4. Major feature areas (detailed bullets)
5. Domain-specific workflows (happy path + edge cases)
6. Data & persistence expectations
7. UX / API surface expectations
8. Quality, security, and reliability expectations
9. Documentation & testing expectations
10. Constraints & non-goals
11. Acceptance criteria (checkable)
12. Uniqueness / anti-clone constraints for this run

Write a complete PLATFORM PROMPT now.
"""
