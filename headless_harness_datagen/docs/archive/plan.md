# Autonomous Headless Harness Interface

## Project Overview

The goal of this project is to build an autonomous, programmable headless interface capable of interacting with existing agent harness backends entirely through their exposed APIs. The first target backend is Chakra, although the long-term objective is to support multiple agent harnesses through the same abstraction.

Unlike traditional SDKs or API wrappers, this project does not expose backend operations directly to the user. Instead, the interface itself is driven by a Large Language Model that behaves as an intelligent human operator. Once given a high-level objective, the LLM is responsible for conducting the entire interaction with the backend until the task is complete.

The backend remains responsible for all agent execution, tool orchestration, memory management, trace collection, conversation management, streaming, and runtime behavior. The headless interface never replaces or duplicates these responsibilities. Instead, it becomes an intelligent front-end capable of communicating with the backend exactly as a human would, but automatically.

The overall architecture therefore becomes:

```text
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
          Harness Interface
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  Chakra Harness      Future Harness
        │                   │
        ▼                   ▼
     Backend API       Backend API
        │
        ▼
     Chakra Backend
        │
        ▼
QueryEngine → LLM → Tools → Trace Collection
```

The LLM never communicates with the backend directly. Every interaction passes through the harness interface, which abstracts backend-specific APIs while allowing the controller LLM to operate independently of any particular implementation.

---

# Motivation

Current agent harnesses are primarily designed for direct human interaction through command-line interfaces or graphical interfaces. A human creates sessions, configures agents, responds to questions, manages personas, handles errors, resumes conversations, and decides what message should be sent next.

This project removes the human from the operational loop.

Instead of manually driving the conversation, an LLM assumes the role of the human operator. The LLM receives only the overall objective and is expected to independently determine every intermediate action required to accomplish that objective.

The human therefore interacts only once:

> "Generate a complete software repository."

Everything after this point is handled autonomously by the controller.

The controller decides when to create sessions, when to switch personas, when to answer backend questions, when to continue conversations, when to retry operations, and when the task has been completed.

---

# What This Project Does Not Do

It is important to distinguish this project from an agent runtime.

The Chakra backend already provides:

- agent execution
- tool orchestration
- conversation management
- streaming
- context management
- trace collection
- memory
- reasoning
- execution loop
- tool execution

None of these responsibilities belong to the headless interface.

The interface never executes tools.

The interface never manages reasoning inside the backend.

The interface never performs repository generation.

The interface never collects traces.

The interface simply communicates with the backend.

---

# The Controller LLM

The controller LLM is the central intelligence of the entire system.

Rather than being responsible for solving the user's original task, it is responsible for operating the harness exactly as a skilled human operator would.

Its job is to continuously observe backend responses, understand the current conversation state, determine the appropriate next action, and communicate with the backend until the objective has been achieved.

The controller is therefore not implementing software engineering tasks itself.

Instead, it is orchestrating the interaction between itself and the backend.

For example, if the backend asks for clarification, the controller decides how to respond.

If the backend requests confirmation before continuing, the controller provides it.

If a session terminates unexpectedly, the controller determines whether to retry, resume, or begin a new session.

If multiple personas are required, the controller determines when each persona should be invoked and what information should be communicated to them.

This makes the controller resemble an autonomous operator rather than a conventional prompt-response model.

---

# Conversation Engine

At the heart of the interface is an autonomous conversation engine.

This component continuously executes the following cycle:

```text
Receive backend response
        │
        ▼
Update conversation state
        │
        ▼
Controller LLM reasons
        │
        ▼
Determine next action
        │
        ▼
Send request to backend
        │
        ▼
Receive next response
```

Unlike a conventional chat client, the conversation engine does not simply relay messages.

Instead, it continuously decides what should happen next.

The backend is therefore viewed as an environment with which the controller interacts rather than a passive API.

---

# Harness Interface

The harness interface provides a backend-independent contract.

The controller should never know that Chakra exists.

Instead, it interacts only with a generic interface capable of performing operations such as:

- establishing connections
- creating sessions
- restoring sessions
- sending messages
- receiving streamed events
- querying session state
- terminating execution
- configuring personas
- configuring execution parameters

Each backend implements these operations differently, but the controller always interacts with the same abstract interface.

This separation allows new harnesses to be introduced without modifying the controller.

---

# Harness Adapters

Every supported backend implements the common harness contract.

For example:

```text
Harness Interface
        │
        ├──────────────┐
        ▼              ▼
 ChakraHarness    FutureHarness
        │              │
        ▼              ▼
 Chakra API      Other Backend API
```

Each adapter is responsible only for translating generic operations into backend-specific API requests.

The controller never sees backend-specific endpoints, payload formats, authentication mechanisms, or streaming implementations.

---

# Persona Management

Persona management is also delegated to the controller.

The controller receives only the overall objective.

It independently determines:

- whether multiple personas are required
- which persona should execute next
- what information should be communicated
- when a persona has completed its work
- whether another persona should be started

The backend remains responsible for executing each persona.

The controller remains responsible for deciding which persona should be active at any point during execution.

This allows different workflows to emerge dynamically rather than being hardcoded into the interface.

---

# Autonomous Decision Making

The interface should never encode fixed workflows such as:

- always create an Architect first
- always continue after completion
- always switch to Testing
- always answer "Continue"

Every interaction should instead be determined by the controller after observing the current backend state.

The controller therefore performs continuous reasoning over the conversation rather than executing predefined scripts.

This enables the interface to adapt naturally to different harnesses, domains, workflows, and execution models.

---

# Error Handling

Errors should also be handled autonomously.

If the backend returns an error, requests clarification, temporarily fails, or produces unexpected responses, the controller should analyse the situation and determine the most appropriate recovery strategy.

Possible actions may include retrying a request, reformulating instructions, restoring a previous session, switching personas, or requesting additional information from the backend.

Recovery logic therefore emerges from the controller's reasoning rather than from manually written recovery code.

---

# Why This Is Different From an SDK

A traditional SDK exposes backend functionality directly to application developers.

For example:

```python
session.create()

session.send()

session.continue()

session.resume()
```

The application developer must explicitly decide every operation.

The proposed interface removes this responsibility entirely.

The developer provides only a high-level objective.

The controller LLM determines every subsequent interaction required to achieve that objective.

The interface therefore behaves less like a client library and more like an autonomous operator capable of independently driving an existing agent harness.

---

# Long-Term Vision

Although Chakra is the initial backend, the architecture is intentionally backend-independent.

Future harnesses may expose completely different APIs, execution models, persona systems, streaming mechanisms, or memory architectures.

Because the controller interacts only with the abstract harness interface, these differences remain encapsulated inside individual adapters.

The same autonomous controller should therefore be capable of operating any supported harness without changing its own reasoning process.

This transforms the project from a Chakra automation tool into a general-purpose autonomous interface capable of operating multiple agent harnesses across different domains through a single consistent abstraction.