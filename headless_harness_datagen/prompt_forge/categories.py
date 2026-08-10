"""Platform categories for synthetic prompt diversity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    COLLABORATIVE_REALTIME = "collaborative_realtime"
    STORAGE_FILES = "storage_files"
    IOT_AUTOMATION = "iot_automation"
    AI_ML = "ai_ml"
    CMS_CONTENT = "cms_content"
    SECURITY_PRIVACY = "security_privacy"
    ECOMMERCE = "ecommerce"
    MONITORING_OPS = "monitoring_ops"
    GAMES = "games"
    DISTRIBUTED_SYSTEMS = "distributed_systems"
    DEVOPS_INFRA = "devops_infra"
    FINANCE_PRODUCTIVITY = "finance_productivity"
    GENERIC_FULLSTACK = "generic_fullstack"


@dataclass(frozen=True)
class CategoryInfo:
    id: Category
    title: str
    description: str
    keywords: tuple[str, ...]
    example_seeds: tuple[str, ...]


CATEGORIES: dict[Category, CategoryInfo] = {
    Category.COLLABORATIVE_REALTIME: CategoryInfo(
        id=Category.COLLABORATIVE_REALTIME,
        title="Collaborative / Real-time Platforms",
        description=(
            "Multi-user products with live sync: whiteboards, chat, rooms, "
            "presence, shared canvases, and soft real-time collaboration."
        ),
        keywords=(
            "collaborative",
            "realtime",
            "real-time",
            "websocket",
            "socket",
            "whiteboard",
            "chat",
            "slack",
            "presence",
            "multiplayer",
            "room",
            "live",
        ),
        example_seeds=(
            "Collaborative whiteboard with rooms and shared drawing",
            "Team chat with channels and DMs",
        ),
    ),
    Category.STORAGE_FILES: CategoryInfo(
        id=Category.STORAGE_FILES,
        title="File Storage / Document Platforms",
        description=(
            "Upload, organize, search, and share files or documents with "
            "quotas, folders, previews, and access control."
        ),
        keywords=(
            "storage",
            "upload",
            "download",
            "file",
            "folder",
            "drive",
            "s3",
            "document",
            "blob",
            "media library",
        ),
        example_seeds=(
            "Mini cloud storage with folders and sharing",
            "Team document vault with preview",
        ),
    ),
    Category.IOT_AUTOMATION: CategoryInfo(
        id=Category.IOT_AUTOMATION,
        title="IoT / Automation Dashboards",
        description=(
            "Device control, schedules, automation rules, sensor history, "
            "and operator dashboards for simulated or real device fleets."
        ),
        keywords=(
            "iot",
            "smart home",
            "device",
            "sensor",
            "thermostat",
            "automation",
            "schedule",
            "mqtt",
            "actuator",
        ),
        example_seeds=(
            "Smart home dashboard with device simulation",
            "Greenhouse sensor automation console",
        ),
    ),
    Category.AI_ML: CategoryInfo(
        id=Category.AI_ML,
        title="AI / ML Application Platforms",
        description=(
            "Products centered on models: classification, NLP extraction, "
            "resume matching, embeddings, inference APIs, and analysis UIs."
        ),
        keywords=(
            "ai",
            "ml",
            "model",
            "nlp",
            "transformers",
            "pytorch",
            "classification",
            "embedding",
            "inference",
            "resume",
            "llm",
            "huggingface",
        ),
        example_seeds=(
            "Resume analyzer against a job description",
            "Image classification REST API",
        ),
    ),
    Category.CMS_CONTENT: CategoryInfo(
        id=Category.CMS_CONTENT,
        title="CMS / Content / Catalog Platforms",
        description=(
            "Libraries, blogs, catalogs, publishing workflows, roles, "
            "search, and content lifecycle management."
        ),
        keywords=(
            "cms",
            "blog",
            "library",
            "catalog",
            "publish",
            "article",
            "book",
            "content",
            "editorial",
            "markdown",
        ),
        example_seeds=(
            "Digital library with borrow/return workflows",
            "Multi-author blog with moderation",
        ),
    ),
    Category.SECURITY_PRIVACY: CategoryInfo(
        id=Category.SECURITY_PRIVACY,
        title="Security / Privacy Tools",
        description=(
            "Vaults, credential managers, encryption, secure clipboard, "
            "audit trails, and privacy-sensitive local or desktop tools."
        ),
        keywords=(
            "password",
            "vault",
            "encrypt",
            "aes",
            "security",
            "privacy",
            "secrets",
            "keystore",
            "2fa",
            "master password",
        ),
        example_seeds=(
            "Encrypted password manager desktop app",
            "Local secrets vault with audit log",
        ),
    ),
    Category.ECOMMERCE: CategoryInfo(
        id=Category.ECOMMERCE,
        title="E-commerce / Inventory / Orders",
        description=(
            "Catalogs, carts, inventory, suppliers, orders, fulfillment, "
            "and merchant analytics dashboards."
        ),
        keywords=(
            "ecommerce",
            "e-commerce",
            "inventory",
            "order",
            "cart",
            "sku",
            "supplier",
            "checkout",
            "product",
            "warehouse",
        ),
        example_seeds=(
            "Inventory and order management for a small shop",
            "Merchant catalog with low-stock alerts",
        ),
    ),
    Category.MONITORING_OPS: CategoryInfo(
        id=Category.MONITORING_OPS,
        title="Monitoring / Observability Platforms",
        description=(
            "Uptime checks, latency graphs, incident history, health "
            "dashboards, and operational alerting surfaces."
        ),
        keywords=(
            "monitoring",
            "uptime",
            "latency",
            "ping",
            "metrics",
            "observability",
            "dashboard",
            "alert",
            "outage",
            "health",
        ),
        example_seeds=(
            "Network host monitoring with latency charts",
            "Service health board with downtime history",
        ),
    ),
    Category.GAMES: CategoryInfo(
        id=Category.GAMES,
        title="Games / Interactive Simulations",
        description=(
            "2D/3D games, AI opponents, waves, scoring, save/load, and "
            "interactive simulation loops."
        ),
        keywords=(
            "game",
            "unity",
            "pygame",
            "tower defense",
            "snake",
            "score",
            "level",
            "enemy",
            "player",
            "simulation",
        ),
        example_seeds=(
            "Tower defense with wave progression",
            "Snake game with A* AI mode",
        ),
    ),
    Category.DISTRIBUTED_SYSTEMS: CategoryInfo(
        id=Category.DISTRIBUTED_SYSTEMS,
        title="Distributed Systems / Queues / Workers",
        description=(
            "Schedulers, workers, retries, heartbeats, job APIs, and "
            "concurrency-heavy backend frameworks."
        ),
        keywords=(
            "queue",
            "worker",
            "scheduler",
            "distributed",
            "job",
            "retry",
            "heartbeat",
            "goroutine",
            "broker",
            "task queue",
        ),
        example_seeds=(
            "Distributed task queue with worker heartbeats",
            "Job scheduler with priority and retries",
        ),
    ),
    Category.DEVOPS_INFRA: CategoryInfo(
        id=Category.DEVOPS_INFRA,
        title="DevOps / Infrastructure Consoles",
        description=(
            "Docker/K8s dashboards, container ops, cluster views, logs, "
            "and infrastructure control planes for local demos."
        ),
        keywords=(
            "docker",
            "kubernetes",
            "k8s",
            "container",
            "cluster",
            "pod",
            "deployment",
            "infra",
            "devops",
            "ci",
        ),
        example_seeds=(
            "Docker container management dashboard",
            "Kubernetes cluster visualization UI",
        ),
    ),
    Category.FINANCE_PRODUCTIVITY: CategoryInfo(
        id=Category.FINANCE_PRODUCTIVITY,
        title="Finance / Productivity Apps",
        description=(
            "Personal finance, budgeting, habit trackers, productivity "
            "dashboards, and personal data tools with charts."
        ),
        keywords=(
            "finance",
            "budget",
            "expense",
            "income",
            "habit",
            "tracker",
            "todo",
            "productivity",
            "ledger",
            "wallet",
        ),
        example_seeds=(
            "Personal finance tracker with charts",
            "Habit tracker with streaks and reminders",
        ),
    ),
    Category.GENERIC_FULLSTACK: CategoryInfo(
        id=Category.GENERIC_FULLSTACK,
        title="Generic Full-stack Platforms",
        description=(
            "Fallback category for complete web/apps that do not clearly "
            "fit a specialized family — still requires a unique PRD shape."
        ),
        keywords=("web app", "full stack", "fullstack", "saas", "platform", "dashboard"),
        example_seeds=(
            "Small SaaS with auth and a domain dashboard",
            "Internal ops console for a niche workflow",
        ),
    ),
}


def resolve_category(value: str | Category | None) -> Category | None:
    """Resolve a category id string, or return None if unset/unknown."""
    if value is None:
        return None
    if isinstance(value, Category):
        return value
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    for cat in Category:
        if cat.value == key:
            return cat
    return None


def all_category_ids() -> list[str]:
    return [c.value for c in Category]
