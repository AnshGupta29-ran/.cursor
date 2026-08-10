# Category template: IoT / Automation Dashboards

Family shape for device fleets, sensor streams, and rule-based automation. Each run
must invent a concrete environment (home, lab, farm, factory bay) — not a nameless
“Device 1 / Device 2” toy.

## Product family intent

Operators view device state, issue commands, schedule actions, define automation rules,
and inspect historical sensor readings. Devices may be simulated; simulation must behave
like a believable device layer behind REST (or equivalent) APIs.

## Identity & positioning (invent uniquely)

- Product name and environment (apartment, greenhouse, server closet, maker lab)
- Operator persona and urgency (comfort, energy saving, safety, research)
- Device mix that fits the environment (not a random kitchen-sink list)
- One twist (geofenced rules, energy budget, maintenance tickets, multi-zone scenes)

## Required capability areas

### Device inventory
- Register/list devices with type, zone/room, and capabilities
- Online/offline or last_seen semantics
- Readable current state (on/off, setpoint, open/closed, battery, etc.)

### Commands & control
- Explicit command endpoints/UI actions per capability
- Validation against device type (no “set temperature” on a door)
- Command acknowledgment or resulting state change

### Scheduling
- Create/edit/delete schedules (time-based at minimum)
- Enable/disable schedules
- Timezone or local-time policy stated

### Automation rules
- Trigger → condition → action model (keep it understandable)
- Examples tied to the invented environment
- Conflict note when multiple rules fire

### History & visualization
- Persist sensor/history samples
- Charts or tables for recent windows
- Filter by device/zone/time

## UX expectations

- Dashboard overview of zones + critical states
- Device detail page/panel with controls + history
- Rule/schedule editors that are usable without reading source
- Clear simulation vs live labeling if simulated

## Data & APIs

Entities often include: User/Operator, Zone, Device, DeviceState, Command, Schedule,
AutomationRule, SensorReading.
Provide REST (or GraphQL) surface suitable for the frontend; document key routes.

## Quality & reliability

- Backend unit tests for command validation and at least one rule evaluation path
- Idempotent or well-defined repeated commands
- No silent failure on invalid device ids

## Documentation & deliverables

- README with seed devices and how to trigger a rule
- API notes or OpenAPI if backend-first
- Explain simulation strategy

## Constraints & non-goals

- Not a full Matter/Zigbee stack
- Not a mobile native app unless seed requires
- Avoid meaningless random metrics with no operator value

## Acceptance criteria checklist (customize)

- [ ] Operator can view and control multiple device types
- [ ] Schedule changes a device state as designed
- [ ] At least one automation rule is demonstrable end-to-end
- [ ] History visualizations render real stored samples
- [ ] Invalid commands are rejected with clear errors
- [ ] Tests cover device command validation
- [ ] Local demo path is documented

## Variation axes

Environment niche · safety vs comfort · rule complexity · chart density · multi-user
roles · maintenance workflows · energy reports

## Anti-clone rules

Refuse generic “lights fans thermostats” copy-paste. Rename zones, invent plausible
device quirks, and specialize rules so each synthetic platform differs.
