# Autonomous Headless Harness Interface Architecture

(what to build)
explains:
    * project~ vision
    * motivation
    * major components
    * responsibilities
    * layering
    * extensibility
    * design ~philosophy


## Design Philosophy

The headless harness is not an agent runtime, an SDK, or a replacement for an existing harness. It is an autonomous controller capable of operating an existing harness through its public API in the same way a skilled human operator would.

The system should remain completely independent of any specific harness implementation. While Chakra is the initial target, every architectural decision should assume that additional harnesses with different APIs, execution models, and capabilities will eventually be supported.

The controller should never contain Chakra-specific logic. Backend-specific behavior must always remain encapsulated within harness adapters.

---

# High-Level Architecture

```
                   Human
                     │
                     ▼
          High-Level Objective
                     │
                     ▼
              Controller LLM
                     │
                     ▼
         Autonomous Conversation Engine
                     │
                     ▼
            Harness Interface Contract
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
 Chakra Harness Adapter      Future Harness Adapter
      │                             │
      ▼                             ▼
   Backend API                 Backend API
      │
      ▼
 Existing Harness Runtime
```

The architecture is divided into independent layers, each with a single responsibility.

---

# System Components

## 1. Controller

The Controller is the only intelligent component within the headless interface.

Its responsibility is not to solve the user's task directly. Instead, it operates the harness until the objective has been completed.

The controller continuously:

- observes backend responses
- understands the current execution state
- determines the next action
- issues instructions through the harness interface
- evaluates completion conditions

The controller should not know anything about Chakra or any future harness.

It interacts only with the abstract harness interface.

---

## 2. Conversation Engine

The conversation engine manages the execution loop between the controller and the backend.

It maintains the interaction lifecycle rather than the reasoning itself.

Its responsibilities include:

- maintaining conversation state
- delivering backend events to the controller
- forwarding controller decisions
- handling streaming responses
- tracking execution progress
- detecting task completion

The controller reasons.

The conversation engine executes.

---

## 3. Harness Interface

The harness interface defines the common contract implemented by every supported harness.

It represents the only API visible to the controller.

No backend-specific behavior should leak through this interface.

Every supported backend should expose equivalent operations even if their internal implementations differ.

Examples include:

- connect
- disconnect
- create session
- resume session
- send message
- receive events
- interrupt execution
- terminate session
- query session status
- configure execution

The interface describes *what* can be done, not *how* it is performed.

---

## 4. Harness Adapters

Each harness implements the common contract independently.

Examples:

- ChakraHarness
- FutureHarness
- AnotherHarness

An adapter translates generic interface operations into backend-specific API requests.

Responsibilities include:

- API communication
- authentication
- request translation
- response translation
- event normalization
- streaming integration

Adapters never contain controller logic.

---

## 5. Backend

The backend remains completely unchanged.

It continues to provide:

- reasoning
- tool execution
- memory
- context management
- streaming
- trace collection
- runtime execution
- agent orchestration

The interface never duplicates backend functionality.

---

# Separation of Responsibilities

```
Controller
    │
    ├── decides
    ├── reasons
    ├── plans
    └── observes

Conversation Engine
    │
    ├── executes loop
    ├── maintains state
    └── routes events

Harness Adapter
    │
    ├── translates requests
    ├── translates responses
    └── communicates with backend

Backend
    │
    ├── executes agents
    ├── calls tools
    ├── manages memory
    ├── generates traces
    └── performs reasoning
```

Each layer owns a single responsibility.

---

# Long-Term Extensibility

The architecture must support harnesses that differ in:

- API style
- streaming protocol
- session model
- execution model
- authentication
- configuration
- supported capabilities

The controller should remain completely unchanged when adding new harnesses.

Only a new adapter should be required.

---

# Capability-Based Design

Instead of assuming every harness behaves identically, the interface should describe capabilities.

Examples include:

- supports sessions
- supports personas
- supports streaming
- supports interruption
- supports resume
- supports artifacts
- supports multiple agents

Adapters advertise supported capabilities.

The controller adapts its behaviour accordingly.

---

# Persona Management

Personas are not implemented by the harness interface.

Instead, persona orchestration is a future controller capability.

The controller should eventually determine:

- whether personas are required
- which persona should be active
- when to switch personas
- what context should be transferred
- when a persona has completed its work

Different harnesses may implement personas differently, or may not support them at all.

The controller must therefore make persona decisions independently of backend implementation details.

---

# Error Handling

Recovery should be controller-driven rather than hardcoded.

When failures occur, the controller analyses backend responses and determines an appropriate recovery strategy.

Possible actions include:

- retry
- resume
- reconnect
- reformulate instructions
- restart execution
- terminate task

The interface simply exposes the available operations.

---

# Documentation Strategy

Every completed milestone produces permanent documentation.

Documentation is divided into two categories.

## Knowledge Base

Permanent technical reference.

Examples:

- backend startup
- API behaviour
- streaming protocol
- session lifecycle
- harness capabilities

## Development Log

Chronological implementation history.

Each milestone documents:

- objective
- implementation
- validation
- observations
- conclusions

The knowledge base explains how the system works.

The development log explains how it was built.

---

# Development Principles

1. Never modify existing harnesses unless absolutely necessary.

2. Communicate exclusively through exposed backend APIs.

3. Keep the controller backend-agnostic.

4. Encapsulate all backend-specific logic inside adapters.

5. Validate every implementation before extending it.

6. Document every completed milestone.

7. Build incrementally, beginning with the smallest working interaction.

8. Prioritize reusable abstractions over backend-specific shortcuts.