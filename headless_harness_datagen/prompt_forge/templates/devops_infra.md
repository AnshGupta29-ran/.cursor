# Category template: DevOps / Infrastructure Consoles

Family shape for Docker/Kubernetes/local infra control planes. Each prompt should
target a concrete operator workflow against APIs that can be mocked or local.

## Product family intent

Operators inspect and act on infrastructure objects (containers, images, pods,
deployments, services) through a dashboard that reflects live or simulated cluster/
engine state. Actions must map to real API calls or a faithful simulator with clear labeling.

## Identity & positioning (invent uniquely)

- Operator persona (solo indie, classroom lab, platform team lite)
- Scope (Docker Engine only, K8s namespace-scoped, mixed)
- Safety posture (confirm destructive actions, read-only mode toggle)
- One twist (cost-ish resource meters, log tail viewer, restart storms detector, YAML apply box)

## Required capability areas

### Inventory views
- List objects with status, age, basic resource fields
- Detail drawer/page with metadata and recent events/logs snippet
- Filtering/search by name/label/status

### Actions
- Start/stop/restart or scale/delete as appropriate to object type
- Confirmations for destructive actions
- Error surfacing when engine/API rejects

### Logs & diagnostics
- Stream or refresh logs for a selected object
- Health summary widgets

### Auth / access
- Local admin auth OR explicit trusted-local mode (must be stated)
- Optional read-only role

### Simulator vs live
- If live Docker/K8s required, document prerequisites
- If simulated, provide rich fixture cluster that still exercises UI/actions

## UX expectations

- Ops-dense tables with sensible defaults
- Color/status semantics documented
- Empty state when engine unavailable with fix hints

## Data & persistence

Prefer live API as source of truth; local DB only for favorites, notes, audit of actions.
AuditAction entity recommended for mutate operations.

## Quality & reliability

- Tests for action authorization and API client error handling with mocks
- UI should not freeze entirely when one log stream fails
- Clear timeout behavior

## Documentation & deliverables

- README prerequisites (Docker socket, kubeconfig, or simulator mode)
- Demo script of inspect → act → verify
- Safety notes

## Constraints & non-goals

- Not a full Lens/Rancher replacement
- Not cluster provisioning from zero
- Avoid shelling out unsafely to random commands without allowlist

## Acceptance criteria checklist (customize)

- [ ] Inventory views populate from API/simulator
- [ ] At least three mutating or diagnostic actions work
- [ ] Destructive actions require confirmation
- [ ] Logs/details view works for a selected object
- [ ] Engine-down state is handled cleanly
- [ ] Client/handler tests with mocks pass
- [ ] README demo succeeds in documented mode

## Variation axes

Docker vs K8s · read-only default · log UX · apply/YAML · multi-context · audit trail depth

## Anti-clone rules

Specialize object focus and safety workflows. Do not emit identical “Docker dashboard”
feature lists every run.
