"""LLM expansion of category template + task seed → unique platform prompt."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from prompt_forge.categories import CATEGORIES, Category
from prompt_forge.classifier import ClassificationResult, classify
from prompt_forge.meta_prompt import META_SYSTEM_PROMPT, build_expansion_user_message
from prompt_forge.templates import load_template


@dataclass
class GeneratedPlatformPrompt:
    category: Category
    classification: ClassificationResult
    seed: str
    template_used: str
    platform_prompt: str
    model_notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "classification": {
                "category": self.classification.category.value,
                "confidence": self.classification.confidence,
                "method": self.classification.method,
                "scores": self.classification.scores,
            },
            "seed": self.seed,
            "template_used": self.template_used,
            "platform_prompt": self.platform_prompt,
            "model_notes": self.model_notes,
        }


def generate_platform_prompt(
    seed: str,
    llm,
    *,
    category: Category | str | None = None,
    use_llm_classifier: bool = False,
    diversity_hint: str | None = None,
    temperature: float = 1.0,
) -> GeneratedPlatformPrompt:
    """
    Produce a unique platform add-on prompt for one task seed.

    `llm` must implement `.complete(messages, temperature=...) -> str`
    (same contract as controller.OpenAICompatibleClient).
    """
    classification = classify(
        seed,
        category=category,
        llm=llm if use_llm_classifier else None,
        use_llm=use_llm_classifier,
    )
    cat = classification.category
    info = CATEGORIES[cat]
    template = load_template(cat)
    user = build_expansion_user_message(
        category_id=cat.value,
        category_title=info.title,
        template=template,
        seed=seed,
        diversity_hint=diversity_hint,
    )
    raw = llm.complete(
        [
            {"role": "system", "content": META_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    platform_prompt = _strip_wrapping(raw)
    if len(platform_prompt) < 600:
        raise ValueError(
            "Forged platform prompt is unexpectedly short; "
            "refusing to send a weak add-on to the harness."
        )
    return GeneratedPlatformPrompt(
        category=cat,
        classification=classification,
        seed=seed.strip(),
        template_used=cat.value,
        platform_prompt=platform_prompt,
    )


def _strip_wrapping(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# re-export for typing convenience
__all__ = ["GeneratedPlatformPrompt", "generate_platform_prompt", "asdict"]
