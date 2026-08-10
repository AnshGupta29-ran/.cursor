client/
├── __init__.py
├── config.py
├── chakra_client.py
├── mock_server.py
├── session.py
└── generated/
    ├── chakra_pb2.py
    └── chakra_pb2_grpc.py

scripts/
├── verify_chakra.py
├── test_connectivity.py
├── test_session.py
├── generate_proto.py
├── start_chakra.sh
└── test_minimal_chat.py




----



# File: `client/__init__.py`

## Purpose

This file defines the public interface of the Python Chakra client package.

Instead of requiring users to import classes from multiple internal modules, this file exposes the commonly used classes through a single import point.

Example:

```python
from client import ChakraClient, ChakraSession, load_config
```

instead of

```python
from client.chakra_client import ChakraClient
from client.session import ChakraSession
from client.config import load_config
```

This makes the package cleaner and hides its internal directory structure.

---

# Role in Architecture

```
scripts/
        │
        ▼
client (package)
        │
        ▼
__init__.py
        │
        ├── ChakraClient
        ├── ChakraSession
        ├── ChakraConfig
        ├── ServerEvent
        └── load_config()
```

This file acts only as the package entry point.

It contains **no business logic**.

---

# Imports

```python
from client.chakra_client import ChakraClient, ServerEvent
```

Imports the primary gRPC client implementation along with the normalized event model.

---

```python
from client.config import ChakraConfig, load_config
```

Imports configuration utilities used for locating and connecting to the Chakra backend.

---

```python
from client.session import ChakraSession
```

Imports the session abstraction.

Although the current Phase 1 tests barely use it, future milestones will use this object for maintaining persistent conversations.

---

# Public API

The package exposes the following symbols:

| Name | Purpose |
|-------|----------|
| `ChakraClient` | Main Python gRPC client |
| `ChakraConfig` | Configuration object |
| `ChakraSession` | Session abstraction |
| `ServerEvent` | Normalized event object returned from Chakra |
| `load_config()` | Loads configuration from `config/chakra.yaml` |

---

# __all__

```python
__all__ = [
    "ChakraClient",
    "ChakraConfig",
    "ChakraSession",
    "ServerEvent",
    "load_config",
]
```

`__all__` explicitly declares which objects are considered part of the package's public interface.

This affects imports such as:

```python
from client import *
```

Only the listed symbols will be imported.

It also documents the intended API surface for developers.

---

# Responsibilities

- Acts as the package entry point.
- Re-exports important classes.
- Hides internal module organization.
- Defines the supported public API.

---

# Dependencies

### Internal

- `client.chakra_client`
- `client.config`
- `client.session`

### External

None.

---

# Used By

Any script that imports the package directly.

Example:

```python
from client import ChakraClient
```

Current project scripts generally import modules directly, but future code can rely on this simplified interface.

---

# Data Flow

```
Developer

      │

import client

      │

__init__.py

      │

Returns

• ChakraClient
• ChakraSession
• ChakraConfig
• ServerEvent
• load_config()
```

---

# Key Observations

- Contains no executable logic.
- Contains no networking.
- Contains no gRPC code.
- Contains no configuration parsing.
- Exists purely to provide a clean package interface.

---

# Future Evolution

This file will naturally grow as additional abstractions are added during later phases.

Possible future exports include:

- Harness interface
- Event classes
- Conversation engine
- Controller
- Adapter implementations

The goal is that external users interact primarily with the package through this single entry point rather than importing internal modules directly.



----



# File: `client/config.py`

## Purpose

This file is responsible for loading and resolving all configuration required for the Python client to communicate with the Chakra backend.

Rather than hardcoding paths, ports, and service names throughout the codebase, this module centralizes all configuration loading into a single location.

Every component that needs to connect to Chakra depends on this file.

---

# Role in Architecture

```
config/chakra.yaml
        │
        ▼
client/config.py
        │
        ▼
ChakraConfig
        │
        ▼
ChakraClient
        │
        ▼
gRPC Server
```

This module forms the configuration layer between the project files and the runtime client.

---

# Responsibilities

The module is responsible for:

- Loading the YAML configuration file.
- Resolving repository-relative paths.
- Resolving absolute paths.
- Reading runtime environment variable overrides.
- Producing a single immutable configuration object.
- Providing configuration to the rest of the application.

---

# Imports

### Standard Library

```python
import os
```

Used for reading environment variable overrides.

---

```python
from dataclasses import dataclass
```

Creates an immutable configuration object.

---

```python
from pathlib import Path
```

Provides platform-independent filesystem path handling.

---

### Third-party

```python
import yaml
```

Reads the configuration stored in `config/chakra.yaml`.

---

# Module Constants

## `_REPO_ROOT`

```python
_REPO_ROOT = Path(__file__).resolve().parent.parent
```

Automatically determines the repository root.

Example:

```
headless_harness/
    client/
        config.py
```

This resolves to

```
headless_harness/
```

Every relative path inside the project is resolved from this location.

---

## `_DEFAULT_CONFIG`

```python
_DEFAULT_CONFIG = _REPO_ROOT / "config" / "chakra.yaml"
```

Specifies the default configuration file used by the client.

Unless another configuration file is supplied, every client loads this YAML.

---

# ChakraConfig Dataclass

```python
@dataclass(frozen=True)
class ChakraConfig
```

Represents the fully resolved runtime configuration.

It is immutable (`frozen=True`), ensuring that configuration cannot accidentally change after loading.

---

## Fields

### repo_root

Absolute path to the project root.

Example

```
.../headless_harness/
```

---

### chakra_root

Location of the Chakra backend checkout.

Example

```
harness/chakra/
```

---

### grpc_host

Hostname of the running gRPC server.

Example

```
localhost
```

---

### grpc_port

TCP port on which the Chakra server is listening.

Example

```
50051
```

---

### proto_path

Location of the local protobuf definition.

Example

```
client/proto/chakra.proto
```

---

### service_name

Fully-qualified gRPC service name.

Example

```
chakra.v1.AgentService
```

---

### method_name

RPC method exposed by the service.

Example

```
Chat
```

---

# Computed Property

```python
@property
def address(self):
```

Returns

```
host:port
```

Example

```
localhost:50051
```

Every gRPC connection uses this property.

---

# load_config()

## Purpose

This function loads the YAML configuration, resolves all paths, applies environment variable overrides, and returns a `ChakraConfig` object.

Every client begins by calling this function.

---

## Step 1

Determine which configuration file to load.

```python
path = config_path or _DEFAULT_CONFIG
```

Normally this becomes

```
config/chakra.yaml
```

---

## Step 2

Read the YAML file.

```python
yaml.safe_load()
```

Result:

```yaml
chakra:
    root:
    grpc:
    proto:
```

This is converted into a Python dictionary.

---

## Step 3

Resolve repository paths.

For example,

```
harness/chakra
```

becomes

```
/Users/.../headless_harness/harness/chakra
```

Similarly,

```
client/proto/chakra.proto
```

becomes its absolute path.

This guarantees that every later module works with absolute paths rather than fragile relative ones.

---

## Step 4

Apply environment variable overrides.

```python
CHAKRA_GRPC_HOST
```

overrides

```yaml
grpc.host
```

---

```python
CHAKRA_GRPC_PORT
```

overrides

```yaml
grpc.port
```

This allows changing the server location without modifying the YAML file.

Priority becomes:

```
Environment Variables

        │

        ▼

config/chakra.yaml
```

---

## Step 5

Construct the configuration object.

```python
return ChakraConfig(...)
```

Every future module now works with a single configuration object rather than repeatedly parsing YAML.

---

# Configuration Flow

```
config/chakra.yaml

        │

yaml.safe_load()

        │

Dictionary

        │

Resolve Paths

        │

Apply Environment Variables

        │

Create ChakraConfig

        │

Return to Client
```

---

# Used By

Primary consumers include:

- `client.chakra_client`
- `scripts/test_connectivity.py`
- `scripts/test_minimal_chat.py`
- `scripts/test_session.py`
- `scripts/verify_chakra.py`

Every script starts by loading configuration through this module.

---

# Dependencies

## Internal

None.

This is the foundational module.

---

## External

- `yaml`
- `os`
- `pathlib`
- `dataclasses`

---

# Key Design Decisions

### Single Source of Truth

All connection details exist in one location rather than being duplicated across scripts.

---

### Immutable Configuration

Using a frozen dataclass prevents accidental runtime modification.

---

### Environment Variable Override

Supports temporary runtime changes without editing project files.

Priority:

```
Environment Variables

        │

        ▼

YAML Configuration

        │

        ▼

Default Values
```

---

### Automatic Path Resolution

Every relative path is converted into an absolute path immediately after loading.

This prevents path-related bugs when scripts are executed from different working directories.

---

# Data Flow

```
config/chakra.yaml

        │

client/config.py

        │

ChakraConfig

        │

ChakraClient

        │

gRPC Connection
```

---

# Key Observations

- This module performs no networking.
- It does not create any gRPC connections.
- It does not parse protobuf messages.
- It contains no business logic.
- Its only responsibility is configuration loading and normalization.

---

# Future Evolution

As the project grows, additional configuration fields are expected to be added here, such as:

- Default LLM provider
- Model selection
- Authentication settings
- TLS configuration
- Request timeouts
- Retry policies
- Logging configuration
- Multiple backend configurations

The rest of the project should continue to obtain all runtime configuration exclusively through `ChakraConfig`, preserving this module as the single source of truth for application configuration.



----



# File: `client/chakra_client.py`

## Purpose

This file implements the complete Python client for communicating with the Chakra backend over gRPC.

It acts as a thin communication layer between Python applications and the Chakra `AgentService.Chat` streaming API.

Its responsibilities include:

- Establishing a gRPC connection.
- Opening and closing chat streams.
- Sending chat requests.
- Receiving streaming events.
- Converting protobuf messages into Python objects.
- Handling tool approval requests.
- Supporting conversation sessions.
- Providing both low-level and high-level chat APIs.

This is the core implementation file of the Phase 1 client.

---

# Role in Architecture

```
Application / Test Script
            │
            ▼
      ChakraClient
            │
            ▼
      gRPC Channel
            │
            ▼
AgentService.Chat
            │
            ▼
      Chakra Backend
            │
            ▼
      LLM Provider
```

Every interaction with Chakra passes through this class.

---

# Responsibilities

The client is responsible for:

- Creating the gRPC channel.
- Managing the bidirectional stream.
- Sending protobuf requests.
- Receiving protobuf responses.
- Converting protobuf into Python event objects.
- Handling interruptions.
- Handling permission requests.
- Returning final responses.

It deliberately avoids implementing conversation logic or controller behavior.

---

# Major Components

The file is composed of five major sections:

```
EventType Enum
        │
        ▼
ServerEvent Dataclass
        │
        ▼
ActionHandler Type
        │
        ▼
ChakraClient
        │
        ├── Connection Management
        ├── Stream Management
        ├── Message Sending
        ├── Event Processing
        ├── High-Level Chat API
        └── Service Inspection
```

---

# EventType Enum

```
class EventType(Enum)
```

Defines every event the Python client understands.

Current event types are:

```
TEXT_CHUNK
TOOL_START
TOOL_RESULT
ACTION_REQUIRED
DONE
ERROR
STREAM_END
```

Instead of exposing protobuf message names everywhere, the rest of the client works with this standardized enum.

---

# ServerEvent Dataclass

```
@dataclass
class ServerEvent
```

Represents a normalized event received from Chakra.

Instead of exposing raw protobuf objects, every incoming message is converted into this structure.

This provides a stable interface for the rest of the Python code.

---

## Fields

### Streaming

```
text
```

Incremental streamed text.

---

### Tool Execution

```
tool_name
arguments_json
tool_use_id
output
is_error
```

Represent tool execution lifecycle.

---

### Permission Requests

```
prompt_id
question
action_type
```

Used when Chakra pauses execution and waits for user approval.

---

### Completion

```
full_text
prompt_tokens
completion_tokens
```

Provided when the model finishes generation.

---

### Error

```
error_message
error_code
```

Returned when Chakra reports an error.

---

### Raw Message

```
raw
```

Stores the original protobuf object for debugging.

---

# ServerEvent.from_server_message()

This is one of the most important functions in the file.

Purpose:

Convert

```
protobuf
```

↓

into

```
ServerEvent
```

Internally it checks

```
msg.WhichOneof("event")
```

and dispatches accordingly.

Example:

```
TextChunk protobuf
        │
        ▼
ServerEvent(TEXT_CHUNK)
```

```
ToolStart protobuf
        │
        ▼
ServerEvent(TOOL_START)
```

This completely hides protobuf details from higher-level code.

---

# ChakraClient

This class implements the complete communication lifecycle.

It can be divided into six logical subsystems.

---

# 1. Connection Management

Functions:

```
connect()
disconnect()
is_connected()
```

Responsibilities:

- Open gRPC channel.
- Create stub.
- Close channel.
- Verify connectivity.

Flow:

```
Python

    │

grpc.insecure_channel()

    │

AgentServiceStub()

    │

Connected
```

---

# 2. Stream Management

Functions:

```
open_stream()

close_stream()
```

Unlike HTTP, Chakra uses a bidirectional stream.

Opening a stream creates:

```
Queue

↓

Request Iterator

↓

gRPC Stream

↓

Background Reader Thread
```

Closing the stream:

- Stops the iterator.
- Joins the reader thread.
- Releases resources.

---

# Why a Queue?

The queue decouples message production from network transmission.

```
Application

      │

put()

      │

Queue

      │

yield

      │

gRPC
```

The application never writes directly to the socket.

---

# 3. Sending Messages

Functions:

```
_write()

send_chat_request()

send_user_input()

send_cancel()
```

These correspond exactly to the protobuf messages.

---

## ChatRequest

Starts a new conversation.

Contains:

- message
- session_id
- model
- working_directory

---

## UserInput

Replies to

```
ACTION_REQUIRED
```

events.

Used for confirmations like:

```
Run command?

yes
```

---

## CancelSignal

Interrupts the current generation.

Equivalent to pressing Stop in a chat interface.

---

# 4. Reading Events

The background thread runs

```
_read_loop()
```

Flow:

```
Server

↓

protobuf message

↓

ServerEvent

↓

Append to event list
```

The thread continuously reads until:

```
DONE

or

ERROR
```

This keeps reading asynchronous and prevents blocking the main thread.

---

# 5. iter_events()

This is the primary consumer API.

Instead of exposing protobuf streaming,

the client provides

```
for event in client.iter_events():
```

Internally it:

- waits for new events
- yields them one by one
- handles timeout
- exits after DONE or ERROR

This creates a clean Python iterator abstraction.

---

# 6. chat()

This is the highest-level API.

Instead of manually calling

```
connect()

open_stream()

send()

iterate()

close()
```

the user simply writes

```python
client.chat("Hello")
```

Internally it performs:

```
Open Stream

↓

Send Request

↓

Receive Events

↓

Handle Tool Requests

↓

Collect Text

↓

Return Final Response

↓

Close Stream
```

This is the API that most applications will eventually use.

---

# Threading Model

The client uses two concurrent execution paths.

```
Main Thread

        │

send requests

iterate events

        │

----------------------------

Background Thread

        │

receive gRPC messages

convert protobuf

append events
```

This prevents incoming network traffic from blocking the application.

---

# Internal State

The client maintains several important objects.

```
_channel
```

Current gRPC channel.

---

```
_stub
```

Generated gRPC client stub.

---

```
_request_queue
```

Outgoing message queue.

---

```
_events
```

Received normalized events.

---

```
_stream_error
```

Stores any background exceptions.

---

```
_stream_closed
```

Synchronization event indicating stream termination.

---

# Service Inspection

```
inspect_service()
```

Returns static metadata describing the connected service.

Example:

```
Address

Service Name

RPC Method

Proto File

Transport

Supported Client Messages

Supported Server Events
```

Used by the connectivity validation scripts.

---

# Dependencies

## Internal

```
client.config

client.generated.chakra_pb2

client.generated.chakra_pb2_grpc
```

---

## External

```
grpc

threading

queue

logging

time

dataclasses

typing
```

---

# Used By

Current consumers include:

- `scripts/test_connectivity.py`
- `scripts/test_minimal_chat.py`
- `scripts/test_session.py`

Future consumers will include:

- Harness Adapter
- Conversation Engine
- Controller

---

# Data Flow

```
Application

      │

client.chat()

      │

open_stream()

      │

send_chat_request()

      │

Queue

      │

gRPC

      │

Chakra Backend

      │

LLM

      │

Streaming Events

      │

ServerEvent

      │

iter_events()

      │

Application
```

---

# Key Design Decisions

### Event Normalization

Protobuf messages are immediately converted into Python-native objects.

This prevents protobuf types from leaking into the rest of the project.

---

### Background Reader Thread

Reading is asynchronous.

The application never blocks while waiting for network messages.

---

### Queue-Based Writing

Outgoing messages are buffered before transmission.

This simplifies synchronization.

---

### Layered API

The client supports both:

Low-level interface

```
open_stream()

send_chat_request()

iter_events()
```

and

High-level interface

```
client.chat(...)
```

allowing advanced users to manage streams manually while providing a simple API for common use cases.

---

# Current Limitations

- Only supports insecure gRPC connections.
- No automatic reconnection.
- No retry mechanism.
- No authentication layer.
- No session persistence abstraction beyond raw session IDs.
- No conversation state management.

These responsibilities will be introduced in later project phases.

---

# Future Evolution

This class will remain the transport layer of the system.

As the project progresses, higher-level abstractions such as the Harness Interface, Chakra Adapter, Conversation Engine, and Controller will be built on top of this client without exposing its internal gRPC implementation.

Its responsibility should remain focused solely on communication with the Chakra backend.




----



# File: `client/mock_server.py`

## Purpose

This file implements a lightweight mock version of the Chakra gRPC server.

Instead of requiring the real Chakra backend and an LLM provider, this server mimics the expected gRPC behavior and allows the Python client to be developed and tested completely offline.

It is primarily intended for development, debugging, and unit testing.

---

# Role in Architecture

```
Python Client
      │
      ▼
gRPC
      │
      ▼
MockAgentServicer
      │
      ▼
Fake Responses
```

Instead of communicating with the real Chakra backend, the client talks to this mock implementation.

---

# Responsibilities

The mock server is responsible for:

- Starting a local gRPC server.
- Implementing the `AgentService.Chat` RPC.
- Receiving client requests.
- Returning fake streaming responses.
- Simulating session handling.
- Supporting cancellation.
- Providing a predictable environment for testing.

It does **not** communicate with an actual LLM.

---

# Imports

## Standard Library

```python
logging
threading
concurrent.futures
```

Used for logging and running the gRPC server with worker threads.

---

## Third-party

```python
grpc
```

Creates the gRPC server.

---

## Internal

```python
client.generated.chakra_pb2
client.generated.chakra_pb2_grpc
```

Provide the generated protobuf message classes and service definitions.

---

# Main Components

The file contains three major components:

```
MockAgentServicer
        │
        ▼
serve()
        │
        ▼
main()
```

---

# MockAgentServicer

```python
class MockAgentServicer(...)
```

Implements the generated

```
AgentServiceServicer
```

base class.

This class behaves like a fake Chakra backend.

---

# Internal State

```python
self._sessions
```

Stores conversation history.

Structure:

```python
{
    session_id:
        [
            message1,
            message2,
            ...
        ]
}
```

This allows the mock server to simulate persistent sessions.

---

# Chat()

This function implements the gRPC

```
AgentService.Chat
```

RPC.

Signature:

```
Client Stream
      │
      ▼
Server Stream
```

Unlike REST, both client and server continuously exchange messages over a single connection.

---

## Processing Flow

```
Receive ClientMessage

        │

Determine Payload Type

        │

Generate Fake Response

        │

Stream Text Chunks

        │

Send FinalResponse
```

---

# Handling ChatRequest

When the client sends

```
ChatRequest
```

the mock server:

1. Extracts the user message.
2. Reads the session ID.
3. Looks up previous history.
4. Creates an echo response.
5. Streams the response word by word.
6. Sends a final completion event.

Example

User sends

```
Hello
```

Mock server returns

```
Echo:
Hello
```

instead of querying an LLM.

---

# Session Simulation

If a session ID exists:

```python
history = self._sessions.get(session_id)
```

the mock server appends the current message to the stored history.

Future requests can therefore indicate:

```
prior turns: 3
```

This mimics conversational memory without implementing real reasoning.

---

# Streaming Simulation

Instead of sending one complete response,

the server streams:

```
Echo:

↓

Echo:

↓

Hello

↓

World

↓

Done
```

Each word becomes a separate

```
TextChunk
```

protobuf message.

This closely resembles how real LLM providers stream tokens.

---

# FinalResponse

After all chunks have been sent,

the server emits

```
FinalResponse
```

containing:

- complete text
- prompt token count
- completion token count

This matches the behavior of the real Chakra backend.

---

# UserInput Handling

If the client sends

```
UserInput
```

the mock server simply returns

```
(ack)
```

This allows developers to verify that permission workflows function correctly.

No real action is performed.

---

# Cancel Handling

If the client sends

```
CancelSignal
```

the server executes

```python
context.cancel()
```

which immediately terminates the stream.

This simulates a user stopping generation.

---

# serve()

Purpose:

Create and start the mock gRPC server.

Internally it performs:

```
Create Thread Pool

        │

Register MockAgentServicer

        │

Bind localhost:50051

        │

Start Server

        │

Return Server Object
```

---

# Worker Threads

```python
ThreadPoolExecutor(max_workers=4)
```

Allows multiple client requests to be processed concurrently.

Although the mock server is simple, it follows the same concurrency model as a real gRPC server.

---

# main()

Acts as the executable entry point.

Flow:

```
Configure Logging

        │

Start Server

        │

Wait Forever

        │

Ctrl+C

        │

Shutdown Gracefully
```

Running

```bash
python -m client.mock_server
```

starts this server.

---

# Used By

Typical usage:

```
scripts/test_minimal_chat.py --mock
```

or

```
python -m client.mock_server
```

followed by any client script.

This allows all client functionality to be tested without the actual Chakra backend.

---

# Dependencies

## Internal

```
chakra_pb2
chakra_pb2_grpc
```

---

## External

```
grpc
logging
threading
concurrent.futures
```

---

# Data Flow

```
Python Client

      │

ChatRequest

      │

MockAgentServicer

      │

Generate Echo Response

      │

TextChunk

      │

TextChunk

      │

FinalResponse

      │

Python Client
```

---

# Key Design Decisions

### Offline Development

Developers can build and debug the Python client without installing or starting Chakra.

---

### Streaming Simulation

Responses are intentionally streamed word by word to emulate real LLM token streaming.

---

### Session Support

The mock server stores minimal conversation history, allowing session-related functionality to be tested.

---

### Protocol Compatibility

The mock server uses the exact same protobuf messages and gRPC service definitions as the real backend.

This ensures that the client interacts with it exactly as it would with Chakra.

---

# Current Limitations

The mock server intentionally omits many real backend capabilities.

It does not:

- Call an LLM.
- Execute tools.
- Request user permissions.
- Perform reasoning.
- Maintain rich conversation state.
- Return realistic token counts.
- Execute shell commands.

Its sole purpose is validating client-side communication and protocol handling.

---

# Future Evolution

As the project grows, the mock server can be extended to simulate more advanced behaviors, including:

- Tool execution events.
- Permission requests (`ActionRequired`).
- Tool results.
- Error responses.
- Long-running streams.
- Multi-turn conversations.
- Failure scenarios.

Maintaining feature parity with the Chakra protocol will make it a valuable testing utility even after the full headless harness is implemented.



----


# `client/session.py`

## Purpose

`session.py` provides a higher-level abstraction over `ChakraClient` for managing **multi-turn conversations**.

While `ChakraClient` is responsible for sending a single chat request over a gRPC stream, `ChakraSession` maintains a persistent `session_id` so multiple user messages belong to the same conversation.

It also records every conversation turn, stores all streamed events, and exposes session metadata.

---

# File Location

```text
client/
└── session.py
```

---

# Responsibility

This file is responsible for:

- Managing persistent conversation sessions.
- Generating and maintaining a unique `session_id`.
- Handling multiple chat turns.
- Recording conversation history locally.
- Collecting all streaming events for every turn.
- Automatically reopening and closing a gRPC stream for each message.
- Returning the assistant's final response.

It does **not**:

- Handle low-level gRPC communication.
- Parse protobuf messages.
- Manage connection setup.
- Implement business logic inside Chakra.

Those responsibilities remain inside `chakra_client.py`.

---

# Why This File Exists

Although Chakra supports persistent conversations, each user message still requires a **new gRPC Chat stream**.

Without this file, every caller would have to manually:

- remember the session ID,
- reopen streams,
- resend the session ID,
- collect events,
- maintain history.

`ChakraSession` encapsulates all of this into a reusable interface.

---

# High-Level Architecture

```text
Application
      │
      ▼
ChakraSession
      │
      ▼
ChakraClient
      │
      ▼
gRPC Stream
      │
      ▼
Chakra Backend
```

The application interacts only with `ChakraSession`, while the session internally delegates communication to `ChakraClient`.

---

# Main Components

## 1. `TurnRecord`

```python
@dataclass
class TurnRecord
```

Represents a single conversation turn.

Each turn stores:

- user's message,
- assistant's final reply,
- all streamed events,
- start timestamp,
- end timestamp.

Structure:

```text
TurnRecord
├── user_message
├── assistant_text
├── events
├── started_at
└── ended_at
```

This provides a complete local record of every interaction.

---

## 2. `ChakraSession`

```python
@dataclass
class ChakraSession
```

The main class that manages an entire conversation.

It owns:

```text
client
session_id
working_directory
model
turns
closed
```

A random UUID is automatically generated when a new session is created.

Example:

```text
4a15d2b4-f1d8-44dd-b770-...
```

This identifier is sent with every `ChatRequest`, allowing Chakra to restore conversation history.

---

# Core Workflow

## `send_message()`

This is the primary API exposed by the session.

Execution flow:

```text
User Message
      │
      ▼
Create TurnRecord
      │
      ▼
Open gRPC Stream
      │
      ▼
Send ChatRequest
      │
      ▼
Receive Stream Events
      │
      ▼
Record Every Event
      │
      ▼
Collect Final Response
      │
      ▼
Close Stream
      │
      ▼
Return Assistant Reply
```

Although a new stream is created for every message, the same `session_id` is reused, allowing the backend to preserve context.

---

# Event Handling

During streaming, every received event is appended to the current `TurnRecord`.

Handled events include:

### Text Chunk

```text
TEXT_CHUNK
```

- Appended to streamed response.
- Stored in the turn's event list.

---

### Action Required

```text
ACTION_REQUIRED
```

If automatic approval is enabled:

```python
reply = "yes"
```

is sent back to Chakra.

Otherwise:

```python
RuntimeError
```

is raised so the caller can decide how to proceed.

---

### Done

```text
DONE
```

Marks the end of generation.

Stores the assistant's final response.

Updates:

```text
assistant_text
ended_at
```

---

### Error

```text
ERROR
```

Stops execution immediately and raises an exception.

---

# Session Lifecycle

A session progresses through the following stages:

```text
Create Session
      │
      ▼
Generate session_id
      │
      ▼
Send Message
      │
      ▼
Open Stream
      │
      ▼
Receive Response
      │
      ▼
Close Stream
      │
      ▼
Repeat
      │
      ▼
Close Session
```

Only the logical session remains active between turns; each underlying gRPC stream is temporary.

---

# `close()`

Marks the session as closed.

After calling:

```python
session.close()
```

future calls to:

```python
send_message()
```

raise an exception.

Note that this only closes the logical session. Disconnecting from the gRPC server is handled separately by `ChakraClient`.

---

# `summary()`

Returns lightweight metadata describing the session.

Example:

```python
{
    "session_id": "...",
    "turn_count": 2,
    "closed": True,
    "working_directory": "...",
    "model": None
}
```

This is mainly used by testing scripts for logging and validation.

---

# Dependencies

Imports:

```text
client.chakra_client
uuid
datetime
logging
dataclasses
```

Uses:

- `ChakraClient`
- `ServerEvent`
- `EventType`

---

# Interaction with Other Files

```text
test_session.py
      │
      ▼
ChakraSession
      │
      ▼
ChakraClient
      │
      ▼
gRPC Chat Stream
      │
      ▼
Chakra Backend
```

`test_session.py` creates a `ChakraSession` and repeatedly calls `send_message()` to verify that conversation state is preserved across multiple turns.

---

# Inputs

Receives:

- User message.
- Optional model.
- Working directory.
- Session ID (generated automatically if not provided).

---

# Outputs

Returns:

- Final assistant response.

Internally records:

- Complete event stream.
- Conversation history.
- Timing information.
- Session metadata.

---

# Design Decisions

- One logical session can span many independent gRPC streams.
- Conversation history is stored by Chakra using `session_id`.
- Every turn is fully recorded for debugging and replay.
- Stream management is hidden from higher-level code.
- Separates conversation lifecycle management from transport logic.

---

# Current Limitations

- No support for branching or parallel conversations within a session.
- No persistence of session history to disk.
- Automatic tool approval is limited to a simple `"yes"` response.
- Session state exists only in memory for the lifetime of the Python process.

---

# Key Takeaways

- Provides a high-level abstraction for multi-turn conversations.
- Maintains a persistent `session_id` across multiple chat requests.
- Automatically opens and closes a new gRPC stream for each turn.
- Records complete conversation history and all streamed events.
- Builds on top of `ChakraClient`, separating session management from low-level communication.



----



# File: `client/generated/chakra_pb2.py`

## Purpose

This file is automatically generated by the Protocol Buffer compiler (`protoc`) from the Chakra protocol definition:

```
client/proto/chakra.proto
```

It contains the Python classes representing every protobuf message exchanged between the Python client and the Chakra backend.

The client never manually serializes or deserializes data. Instead, it constructs and consumes these generated classes.

**This file should never be modified manually.**

---

# Role in Architecture

```
chakra.proto
      │
      ▼
protoc
      │
      ▼
chakra_pb2.py
      │
      ▼
Python Message Classes
      │
      ▼
ChakraClient
      │
      ▼
gRPC
```

This file provides the data model used by the client.

---

# Responsibilities

This generated file is responsible for:

- Defining all protobuf message classes.
- Defining protobuf enums.
- Providing serialization methods.
- Providing deserialization methods.
- Registering protobuf descriptors.

It does **not** contain networking logic.

---

# Generation Process

The file is generated from

```
client/proto/chakra.proto
```

using the Protocol Buffer compiler.

Conceptually:

```
chakra.proto

        │

protoc

        │

chakra_pb2.py
```

Every time the protocol changes, this file must be regenerated.

---

# Major Message Types

The generated classes correspond directly to the protobuf definitions.

---

## ClientMessage

Represents every message sent **from the Python client** to Chakra.

It contains a `oneof` payload.

Possible payloads are:

```
ChatRequest

UserInput

CancelSignal
```

Only one can exist at a time.

---

## ChatRequest

Starts a conversation.

Fields include:

- message
- working_directory
- model
- session_id

This is the first message sent after opening a stream.

---

## UserInput

Represents user responses to an

```
ActionRequired
```

event.

Example:

```
Run command?

↓

yes
```

---

## CancelSignal

Requests cancellation of the running task.

Equivalent to pressing Stop in a chat interface.

---

## ServerMessage

Represents every message received from Chakra.

Like `ClientMessage`, it contains a protobuf `oneof`.

Possible events are:

```
TextChunk

ToolCallStart

ToolCallResult

ActionRequired

FinalResponse

ErrorResponse
```

Every streamed event from Chakra is wrapped in this message.

---

## TextChunk

Represents incremental streamed text.

Example:

```
Hello

↓

World

↓

!
```

The client receives many of these before generation completes.

---

## ToolCallStart

Indicates that Chakra has started executing a tool.

Contains information such as:

- tool name
- arguments
- tool ID

---

## ToolCallResult

Represents the completion of a tool.

Contains:

- tool output
- error flag
- tool ID

---

## ActionRequired

Indicates that Chakra requires user input before continuing.

Examples include:

- permission requests
- confirmations
- additional user information

---

## FinalResponse

Sent once generation has completed.

Contains:

- complete response
- prompt token count
- completion token count

This is the final event of a successful stream.

---

## ErrorResponse

Represents a server-side failure.

Contains:

- error message
- error code

---

# Service Definition

The file also contains the protobuf description of

```
AgentService
```

which defines the

```
Chat
```

bidirectional streaming RPC.

This service description is used by the generated gRPC client.

---

# Serialization

Every generated message includes methods similar to:

```
SerializeToString()

FromString()
```

These convert between Python objects and the binary protobuf format transmitted over gRPC.

The application code never implements serialization manually.

---

# Relationship with ChakraClient

The client constructs these generated objects whenever it communicates with Chakra.

Examples:

Sending a request:

```python
chakra_pb2.ChatRequest(...)
```

Receiving a response:

```python
chakra_pb2.ServerMessage(...)
```

The `ChakraClient` then converts these protobuf messages into higher-level `ServerEvent` objects.

---

# Used By

Primary consumers:

- `client/chakra_client.py`
- `client/mock_server.py`
- `client/generated/chakra_pb2_grpc.py`

Every request and response in the system relies on these message definitions.

---

# Dependencies

## Generated From

```
client/proto/chakra.proto
```

---

## External

```
google.protobuf
```

---

# Data Flow

```
Application

      │

ChakraClient

      │

ChatRequest()

      │

SerializeToString()

      │

gRPC

      │

Server

      │

ServerMessage

      │

FromString()

      │

ChakraClient

      │

ServerEvent
```

---

# Key Design Decisions

### Single Source of Truth

All message formats originate from a single protobuf specification (`chakra.proto`).

---

### Language Independence

Because protobuf is language-neutral, the same protocol can be used by:

- Python
- TypeScript
- Go
- Java
- C++
- Rust

Every language generates equivalent classes from the same `.proto` file.

---

### Strong Typing

Each message has fixed fields and types defined by the protocol.

This eliminates ambiguity during communication between client and server.

---

# Current Limitations

This file should **never** be edited manually.

Any modifications will be overwritten the next time the protobuf compiler is executed.

Protocol changes must always be made in:

```
client/proto/chakra.proto
```

followed by regenerating this file.

---

# Future Evolution

As Chakra introduces new protocol features (additional events, messages, or RPC methods), those changes will first appear in `chakra.proto`.

Regenerating this file will automatically expose the new message classes to the Python client without requiring manual implementation.



----



# File: `client/generated/chakra_pb2_grpc.py`

## Purpose

This file is automatically generated by the gRPC Python code generator from the Chakra protocol definition.

While `chakra_pb2.py` defines the protobuf message classes, this file defines the **gRPC networking layer** that enables the Python client and server to communicate using those messages.

It provides:

- Client stub
- Server base class
- Service registration functions
- Experimental direct RPC interface

**This file should never be modified manually.**

---

# Role in Architecture

```
chakra.proto
      │
      ▼
protoc + grpc_python_plugin
      │
      ▼
chakra_pb2_grpc.py
      │
      ├── AgentServiceStub
      ├── AgentServiceServicer
      ├── add_AgentServiceServicer_to_server()
      └── AgentService (Experimental)
```

This file is responsible for the communication layer, whereas `chakra_pb2.py` is responsible for the data model.

---

# Responsibilities

This generated module is responsible for:

- Creating the Python gRPC client stub.
- Defining the server interface.
- Registering service implementations.
- Connecting protobuf serialization with gRPC networking.
- Performing gRPC version compatibility checks.

It does **not** implement any application logic.

---

# Generation Process

Generated from

```
client/proto/chakra.proto
```

using

```
grpc_tools.protoc
```

Conceptually:

```
chakra.proto

        │

grpc plugin

        │

chakra_pb2_grpc.py
```

Whenever the proto changes, this file must also be regenerated.

---

# Version Compatibility Check

At the beginning of the file:

```python
GRPC_GENERATED_VERSION
GRPC_VERSION
```

are compared.

Purpose:

Ensure that the installed

```
grpcio
```

package is compatible with the generated code.

If the versions do not match,

```
RuntimeError
```

is raised.

This prevents subtle runtime incompatibilities.

---

# AgentServiceStub

```python
class AgentServiceStub
```

This is the **client-side proxy** for the Chakra service.

It exposes the remote RPC methods as if they were local Python methods.

Current RPC:

```
Chat()
```

When `ChakraClient` executes

```python
stub.Chat(...)
```

it is actually sending requests across the network to the Chakra backend.

---

## Chat RPC

Configured as

```python
channel.stream_stream(...)
```

Meaning:

```
Client
      ⇄
Server
```

Both sides can continuously send messages.

This is a **bidirectional streaming RPC**.

Unlike REST,

there is no request-response limitation.

---

# AgentServiceServicer

```python
class AgentServiceServicer
```

Represents the **server-side abstract interface**.

It declares:

```python
def Chat(...)
```

but does not implement it.

Instead, it raises

```
NotImplementedError
```

This class exists so that developers can inherit from it and implement the actual server behavior.

Example:

```python
class MockAgentServicer(AgentServiceServicer):
    ...
```

The real Chakra backend also implements this interface in TypeScript.

---

# add_AgentServiceServicer_to_server()

Purpose:

Registers a service implementation with a running gRPC server.

Flow:

```
Your Server Class

        │

Register Methods

        │

gRPC Server

        │

Incoming RPC

        │

Your Implementation
```

Example usage:

```python
server = grpc.server(...)

add_AgentServiceServicer_to_server(
    MockAgentServicer(),
    server
)
```

Without this registration, the server would expose no RPC methods.

---

# AgentService (Experimental)

The file also generates

```python
class AgentService
```

This provides an alternative low-level interface for making RPC calls without creating a stub.

Example:

```python
AgentService.Chat(...)
```

This interface is marked **experimental** and is rarely used.

The project instead uses

```
AgentServiceStub
```

which is the recommended approach.

---

# Relationship with chakra_pb2.py

These two generated files work together.

```
chakra_pb2.py

↓

Defines messages

↓

ChatRequest

ServerMessage

FinalResponse

...
```

```
chakra_pb2_grpc.py

↓

Defines communication

↓

AgentServiceStub

AgentServiceServicer

Chat()
```

One defines **what** is sent.

The other defines **how** it is sent.

---

# Relationship with ChakraClient

Inside

```
client/chakra_client.py
```

connection creation looks like:

```python
grpc.insecure_channel(...)

↓

AgentServiceStub(channel)

↓

stub.Chat(...)
```

This stub originates from this generated file.

Without it,

the Python client would have no way to communicate with Chakra.

---

# Relationship with Mock Server

Inside

```
client/mock_server.py
```

the mock server inherits

```python
AgentServiceServicer
```

and registers itself using

```python
add_AgentServiceServicer_to_server(...)
```

Both of these are defined in this file.

---

# Dependencies

## Internal

```
chakra_pb2.py
```

Provides the message classes used by the RPC.

---

## External

```
grpc
```

Provides all networking functionality.

---

# Used By

Primary consumers:

- `client/chakra_client.py`
- `client/mock_server.py`

The rest of the project never interacts with this file directly.

---

# Data Flow

```
Client

      │

AgentServiceStub

      │

Serialize Message

      │

gRPC Channel

      │

Network

      │

Server

      │

AgentServiceServicer

      │

Process Request
```

---

# Key Classes

## AgentServiceStub

Client-side RPC interface.

Used to call:

```
Chat()
```

---

## AgentServiceServicer

Server-side abstract base class.

Implemented by:

```
MockAgentServicer
```

and the real Chakra backend.

---

## add_AgentServiceServicer_to_server()

Registers server implementations with the gRPC runtime.

---

## AgentService

Experimental static interface for direct RPC calls.

Not used by this project.

---

# Key Design Decisions

### Generated Code

This file is generated entirely from the protocol definition.

No manual editing should ever occur.

---

### Strong Client/Server Separation

The generated code cleanly separates:

- Client proxy (`Stub`)
- Server interface (`Servicer`)

Both use the exact same protocol specification.

---

### Bidirectional Streaming

The generated RPC is configured as

```
stream_stream
```

allowing:

- Multiple client messages.
- Multiple server messages.
- Continuous communication over a single connection.

This matches Chakra's conversational architecture.

---

# Current Limitations

This module contains **no application logic**.

It does not:

- Interpret messages.
- Manage sessions.
- Handle conversations.
- Process events.
- Execute tools.

Its sole responsibility is exposing the protocol over gRPC.

---

# Future Evolution

Whenever new RPC methods are added to `chakra.proto`, regenerating this file will automatically create new client stubs and server interfaces.

For example, future protocol additions such as:

- Health checks
- Session management
- File transfer
- Authentication RPCs

would automatically appear here after regeneration, without requiring manual implementation.



----


# File: `scripts/test_minimal_chat.py`

## Purpose

This script performs the first real end-to-end validation of the Python client.

Unlike the connectivity tests, which only verify that the gRPC server is reachable, this script sends an actual prompt to the Chakra backend, receives the streamed response, and verifies that the complete communication pipeline functions correctly.

It is essentially an integration test for the entire Phase 1 implementation.

---

# Role in Architecture

```
User

    │

python scripts/test_minimal_chat.py

    │

ChakraClient

    │

gRPC

    │

Chakra Backend

    │

LLM Provider

    │

Streaming Response

    │

Python Client

    │

Console + JSON Log
```

This script exercises almost every component developed during Phase 1.

---

# Responsibilities

The script is responsible for:

- Loading configuration.
- Creating the Chakra client.
- Connecting to the backend.
- Opening a chat stream.
- Sending a prompt.
- Receiving streamed events.
- Printing streamed text.
- Handling tool approval requests.
- Recording all received events.
- Writing a structured JSON log.
- Reporting success or failure.

It contains **no reusable client logic**. Instead, it demonstrates how to use the client library.

---

# Imports

## Standard Library

```
argparse
```

Parses command-line arguments.

---

```
json
```

Writes structured log files.

---

```
logging
```

Displays runtime information.

---

```
datetime
```

Creates timestamps for log files.

---

```
pathlib
```

Constructs log file paths.

---

## Internal

```
client.chakra_client
```

Provides the `ChakraClient` and `EventType`.

---

```
client.config
```

Loads the Chakra configuration.

---

# Global Constant

```
LOG_DIR
```

Points to

```
logs/
```

Every execution generates a timestamped JSON log inside this directory.

Example:

```
logs/
    minimal_chat_20260702T055850Z.json
```

---

# Program Flow

The execution can be summarized as:

```
Parse Arguments

        │

Load Configuration

        │

Create ChakraClient

        │

Connect

        │

Open Stream

        │

Send Prompt

        │

Receive Streaming Events

        │

Print Response

        │

Write Log File

        │

Disconnect
```

---

# Step 1 — Parse Command-Line Arguments

The script supports three parameters.

---

## --message

Specifies the prompt sent to Chakra.

Example:

```bash
python scripts/test_minimal_chat.py \
    --message "Explain FastAPI."
```

If omitted, the default message in the script is used.

---

## --timeout

Maximum time to wait for the response.

Default:

```
120 seconds
```

---

## --mock

Indicates that the client is communicating with the mock server.

This changes the success criteria because the mock server behaves differently from the real backend.

---

# Step 2 — Configure Logging

```
logging.basicConfig(...)
```

Creates console output such as

```
INFO Connected

INFO Received event

INFO Done
```

This helps developers observe execution in real time.

---

# Step 3 — Load Configuration

```
config = load_config()
```

Loads

```
config/chakra.yaml
```

and constructs a `ChakraConfig` object.

---

# Step 4 — Create Client

```
client = ChakraClient(config)
```

Creates the communication object.

No network connection is established yet.

---

# Step 5 — Initialize Result Structure

The script prepares a dictionary that will later be written as JSON.

Fields include:

- timestamp
- milestone
- prompt
- address
- success
- final response
- event types
- errors

This makes every execution reproducible and easy to inspect.

---

# Step 6 — Connect to Chakra

```
client.connect()
```

Creates the gRPC channel and verifies the server is reachable.

At this point:

```
Python

↓

gRPC

↓

Chakra
```

is connected.

---

# Step 7 — Open Chat Stream

```
client.open_stream()
```

Creates the bidirectional gRPC stream.

No prompt has been sent yet.

---

# Step 8 — Send Chat Request

```
client.send_chat_request(...)
```

Creates a protobuf

```
ChatRequest
```

containing:

- message
- working directory
- session ID

and sends it to Chakra.

---

# Step 9 — Receive Streaming Events

The script iterates over

```
client.iter_events()
```

Every event is processed individually.

```
TextChunk

↓

append text

↓

print immediately
```

```
ToolStart

↓

log tool
```

```
ActionRequired

↓

reply "yes"
```

```
Done

↓

save final response
```

```
Error

↓

raise exception
```

This demonstrates the complete streaming interface.

---

# Streaming Output

Every incoming

```
TextChunk
```

is immediately printed.

Example:

```
For

building

web

applications

...
```

This reproduces the streaming behavior seen in ChatGPT or Claude.

---

# Tool Approval

If Chakra requests permission:

```
ACTION_REQUIRED
```

the script automatically replies

```
yes
```

using

```
send_user_input()
```

This allows simple tool workflows to continue without manual intervention.

---

# Completion

When

```
DONE
```

arrives:

The script records:

- final text
- token counts
- success status

This marks the end of the conversation.

---

# Error Handling

If an

```
ERROR
```

event arrives,

or any exception occurs,

execution enters the

```
except
```

block.

The error is recorded in the JSON log before cleanup occurs.

---

# Cleanup

Regardless of success or failure,

the script always executes:

```
close_stream()

disconnect()
```

This guarantees that:

- threads terminate
- sockets close
- resources are released

---

# Log Generation

After execution,

the script writes

```
logs/minimal_chat_<timestamp>.json
```

The log contains:

- prompt
- streamed events
- final response
- event sequence
- success flag
- errors

This creates a permanent record of every test execution.

---

# Data Flow

```
User Prompt

      │

ChatRequest

      │

ChakraClient

      │

gRPC

      │

Chakra

      │

LLM

      │

TextChunk

      │

TextChunk

      │

Done

      │

Console Output

      │

JSON Log
```

---

# Dependencies

## Internal

```
client.config

client.chakra_client
```

---

## External

```
argparse

json

logging

datetime

pathlib
```

---

# Used By

Executed manually during Phase 1 validation.

Typical command:

```bash
python scripts/test_minimal_chat.py
```

or

```bash
python scripts/test_minimal_chat.py \
    --message "Explain FastAPI."
```

---

# Relationship with Other Components

```
config.py

        │

↓

chakra_client.py

        │

↓

test_minimal_chat.py

        │

↓

Chakra Backend
```

This script is effectively the first consumer of the reusable client library.

---

# Key Design Decisions

### End-to-End Validation

Unlike unit tests,

this script verifies the complete communication chain:

```
Python

↓

gRPC

↓

Chakra

↓

LLM

↓

Streaming Response

↓

Python
```

---

### Streaming Demonstration

The script intentionally prints each incoming `TextChunk` immediately, allowing developers to observe real-time token streaming.

---

### Automatic Logging

Every execution produces a structured JSON log.

This makes debugging much easier than relying solely on console output.

---

### Safe Cleanup

Streams and network connections are always closed, even if an exception occurs.

This prevents orphaned threads and hanging sockets.

---

# Current Limitations

This script is intentionally simple.

It does not:

- Maintain multi-turn conversations.
- Resume sessions.
- Manage conversation history.
- Execute autonomous workflows.
- Handle complex tool interactions.
- Retry failed requests.

Its sole purpose is validating that the Python client can successfully communicate with the Chakra backend.

---

# Future Evolution

Although this script will continue to serve as a regression test, later phases of the project will build significantly higher-level abstractions.

Future components such as the Harness Adapter, Conversation Engine, and Controller will internally use the same `ChakraClient`, while this script remains a lightweight integration test to verify that the communication layer continues to function correctly.

---- 

# `scripts/verify_chakra.py`

## Purpose

`verify_chakra.py` is the very first validation script of the project.

Its responsibility is **not to communicate with Chakra**, but to verify that the entire local development environment is correctly configured before attempting any gRPC communication.

This corresponds to **Milestone 1.1 – Environment Verification**.

If this script passes, it guarantees that all required files, tools, and directories needed for the remainder of Phase 1 exist and are correctly configured.

---

# File Location

```text
scripts/
└── verify_chakra.py
```

---

# Responsibility

This script validates:

- Repository layout
- Chakra checkout
- Proto availability
- Python version
- Bun installation
- Node version
- npm availability
- Chakra dependencies
- Generated proto location

It does **not**:

- Start Chakra
- Open a gRPC connection
- Communicate with any LLM
- Make any network requests

It performs only local validation.

---

# Execution Flow

```text
Start
   │
   ▼
Load project configuration
   │
   ▼
Locate Chakra repository
   │
   ▼
Run environment checks
   │
   ▼
Record PASS / FAIL
   │
   ▼
Write JSON report
   │
   ▼
Return success/failure
```

---

# Imports

```python
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from client.config import load_config
```

### Purpose of Imports

| Import | Purpose |
|---------|----------|
| `json` | Write verification report |
| `logging` | Console logging |
| `shutil` | Detect installed executables |
| `subprocess` | Query Node version |
| `sys` | Check Python version |
| `datetime` | Timestamp log files |
| `Path` | Filesystem operations |
| `load_config()` | Load Chakra configuration |

---

# Main Components

## 1. `_log_path()`

Creates a timestamped log filename.

Example:

```text
logs/
└── verify_chakra_20260701T153717Z.json
```

Every execution creates a new verification report.

---

## 2. `main()`

Acts as the complete verification pipeline.

Responsibilities:

- Load project configuration
- Run all environment checks
- Record PASS / FAIL
- Save results to JSON
- Return success or failure

---

## 3. `check()`

Helper function used for every validation.

Instead of repeatedly writing:

```python
if condition:
    ...
```

every validation becomes:

```python
check(
    name,
    passed,
    details
)
```

Internally it records:

```json
{
    "ok": true,
    "detail": "..."
}
```

This makes the verification logic much cleaner.

---

# Validation Checks

## 1. Chakra Repository

Checks:

```python
config.chakra_root.is_dir()
```

Purpose:

Verifies that the Chakra repository exists.

---

## 2. Proto Source

Checks:

```text
harness/chakra/src/proto/chakra.proto
```

Purpose:

Ensures the original protobuf definition exists.

This file is later used to generate Python gRPC stubs.

---

## 3. gRPC Server

Checks:

```text
harness/chakra/src/grpc/server.ts
```

Purpose:

Confirms that Chakra exposes a gRPC server implementation.

---

## 4. Local Proto Copy

Checks:

```text
client/proto/chakra.proto
```

Purpose:

Ensures the Python client has its own copy of the protobuf specification.

The client intentionally does not import files directly from Chakra.

---

## 5. Python Version

Checks:

```text
Python >= 3.10
```

Purpose:

Ensures required language features are available.

---

## 6. Bun Installation

Uses:

```python
shutil.which("bun")
```

Purpose:

Checks whether Bun is installed.

Bun is required to launch the Chakra backend.

---

## 7. Node Version

Runs:

```bash
node --version
```

Purpose:

Ensures:

```text
Node >= 20
```

The script also checks:

```text
/opt/homebrew/bin/node
```

to help users who have multiple Node installations.

---

## 8. npm

Checks:

```text
npm
```

Purpose:

Verifies npm is available.

---

## 9. package.json

Checks:

```text
harness/chakra/package.json
```

Purpose:

Confirms the Chakra repository is complete.

---

## 10. node_modules

Checks:

```text
harness/chakra/node_modules
```

Purpose:

Ensures Chakra dependencies have already been installed.

---

# Output

Produces:

```text
logs/
└── verify_chakra_<timestamp>.json
```

Example:

```json
{
    "milestone": "1.1",
    "checks": {
        ...
    }
}
```

This becomes a permanent environment verification record.

---

# Dependencies

Depends only on:

```text
client/config.py
```

which provides:

- Repository root
- Chakra location
- Proto location

No networking is performed.

---

# Interaction with Other Files

```text
verify_chakra.py
        │
        ▼
client/config.py
        │
        ▼
config/chakra.yaml
        │
        ▼
Filesystem
```

There is **no communication** with:

- gRPC
- Chakra server
- TensorStudio
- Any LLM

---

# Inputs

None.

Everything is automatically discovered from the repository configuration.

---

# Outputs

### Console

Displays PASS / FAIL logs.

Example:

```text
[PASS] python_version
[PASS] node_version
[PASS] bun_available
```

### JSON Report

Stored under:

```text
logs/
```

### Exit Code

```text
0 → Success

1 → Failure
```

---

# Why This File Exists

Without this script, developers would need to manually verify:

- Repository structure
- Bun installation
- Node version
- Python version
- Proto files
- Chakra dependencies

`verify_chakra.py` automates all of these checks and provides a single diagnostic report before any networking or gRPC communication begins.

---

# Key Takeaways

- Implements **Milestone 1.1 – Environment Verification**.
- Performs only local validation; no network communication occurs.
- Verifies repository structure, required tools, runtime versions, and Chakra dependencies.
- Produces a timestamped JSON report for diagnostics.
- Serves as the prerequisite for all later milestones (connectivity, chat, sessions, and streaming).


----



# `scripts/test_connectivity.py`

## Purpose

`test_connectivity.py` is the second validation script in Phase 1.

Its responsibility is to verify that the Python client can successfully establish a **gRPC connection** with the running Chakra backend.

Unlike `verify_chakra.py`, which only validates the local environment, this script performs the first actual network communication with Chakra.

This corresponds to **Milestone 1.2 – Connectivity Validation**.

A successful execution proves that:

- Chakra is running.
- The gRPC server is reachable.
- The Python client can establish a channel.
- The generated protobuf stubs are correct.
- The configured service exists.

It does **not** send any chat messages.

---

# File Location

```text
scripts/
└── test_connectivity.py
```

---

# Responsibility

This script performs the following tasks:

- Load project configuration
- Create a Chakra client
- Open a gRPC channel
- Verify the server is reachable
- Inspect the configured service metadata
- Write a connectivity report

It does **not**:

- Start a chat session
- Send prompts to an LLM
- Stream responses
- Manage sessions

---

# Execution Flow

```text
Start
   │
   ▼
Load configuration
   │
   ▼
Create ChakraClient
   │
   ▼
Connect to gRPC server
   │
   ▼
Inspect service metadata
   │
   ▼
Disconnect
   │
   ▼
Write JSON report
```

---

# Imports

```python
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from client.chakra_client import ChakraClient
from client.config import load_config
```

### Purpose of Imports

| Import | Purpose |
|---------|----------|
| `argparse` | Parse timeout argument |
| `json` | Save connectivity report |
| `logging` | Console logging |
| `datetime` | Timestamp reports |
| `Path` | Log directory management |
| `ChakraClient` | gRPC client implementation |
| `load_config()` | Load Chakra configuration |

---

# Main Components

## 1. Argument Parser

Accepts one optional argument:

```bash
--timeout
```

Example:

```bash
python scripts/test_connectivity.py --timeout 10
```

Default:

```text
5 seconds
```

---

## 2. Configuration Loading

```python
config = load_config()
```

Loads:

- gRPC host
- gRPC port
- proto path
- service name

from

```text
config/chakra.yaml
```

---

## 3. Client Creation

```python
client = ChakraClient(config)
```

Creates the Python gRPC client but does **not** connect yet.

---

## 4. Connection Test

```python
client.connect()
```

Internally this performs:

```text
Python
    │
grpc.insecure_channel()
    │
    ▼
localhost:50051
    │
    ▼
Chakra Server
```

If the channel becomes ready before the timeout, the connection is considered successful.

---

## 5. Service Inspection

After connecting, the script calls:

```python
client.inspect_service()
```

This returns static metadata describing the configured service.

Example:

```json
{
    "service": "chakra.v1.AgentService",
    "method": "Chat",
    "transport": "gRPC bidirectional streaming"
}
```

This confirms the client is targeting the expected API.

---

## 6. Disconnect

```python
client.disconnect()
```

Closes the gRPC channel cleanly.

---

# Output

Produces:

```text
logs/
└── connectivity_<timestamp>.json
```

Example:

```json
{
    "milestone": "1.2",
    "connected": true,
    "service_inspection": {
        ...
    }
}
```

---

# Dependencies

Uses:

```text
client/config.py
```

for configuration and

```text
client/chakra_client.py
```

for all gRPC communication.

---

# Interaction with Other Files

```text
test_connectivity.py
        │
        ▼
client/config.py
        │
        ▼
client/chakra_client.py
        │
        ▼
grpc.Channel
        │
        ▼
Chakra Server
```

Unlike `verify_chakra.py`, this script performs actual network communication.

---

# Inputs

Optional command-line argument:

```bash
--timeout
```

Example:

```bash
python scripts/test_connectivity.py --timeout 10
```

---

# Outputs

### Console

Displays connection status.

Example:

```text
Successfully connected to localhost:50051
```

---

### JSON Report

Saved in:

```text
logs/
```

---

### Exit Code

```text
0 → Connected successfully

1 → Connection failed
```

---

# Why This File Exists

This script verifies the first real communication path between the Python client and Chakra.

It ensures that:

- the server is running,
- the gRPC endpoint is reachable,
- the protobuf definitions are compatible,
- and the client can successfully establish a communication channel.

Without this validation, later chat and session tests would fail without clearly identifying whether the issue lies in connectivity or higher-level logic.

---

# Relationship to Other Milestones

```text
Milestone 1.1
verify_chakra.py
(Environment Verification)
        │
        ▼
Milestone 1.2
test_connectivity.py
(gRPC Connection Verification)
        │
        ▼
Milestone 1.3
test_minimal_chat.py
(Chat Communication)
```

This script bridges the gap between local environment validation and actual chat interactions.

---

# Key Takeaways

- Implements **Milestone 1.2 – Connectivity Validation**.
- Establishes the first real gRPC connection to the Chakra backend.
- Confirms that the configured service is reachable and correctly exposed.
- Does not send prompts or interact with an LLM.
- Produces a timestamped connectivity report for debugging and verification.



----


# `scripts/test_session.py`

## Purpose

`test_session.py` validates that Chakra correctly maintains conversation state across multiple turns using the same `session_id`.

Unlike `test_minimal_chat.py`, which sends a single independent request, this script verifies that multiple messages belong to the same conversation and that the backend remembers previous interactions.

This corresponds to **Milestone 1.4 – Session Validation**.

A successful execution proves that:

- Sessions can be created.
- A unique session ID is maintained.
- Multiple turns share the same conversation context.
- Conversation history persists across requests.
- The Python session wrapper works correctly.

---

# File Location

```text
scripts/
└── test_session.py
```

---

# Responsibility

This script performs the following tasks:

- Connect to Chakra
- Create a new conversation session
- Send multiple user messages
- Reuse the same session ID
- Collect replies
- Verify conversation continuity
- Save the complete session log

It does **not**:

- Test streaming internals
- Validate environment setup
- Generate protobuf code

---

# Execution Flow

```text
Start
   │
   ▼
Load configuration
   │
   ▼
Connect to Chakra
   │
   ▼
Create ChakraSession
   │
   ▼
Send Turn 1
   │
   ▼
Receive Response
   │
   ▼
Send Turn 2
   │
   ▼
Receive Response
   │
   ▼
Close Session
   │
   ▼
Write JSON report
```

---

# Imports

```python
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from client.chakra_client import ChakraClient
from client.config import load_config
from client.session import ChakraSession
```

### Purpose of Imports

| Import | Purpose |
|---------|----------|
| `argparse` | Parse user turns |
| `json` | Save session report |
| `logging` | Console logging |
| `datetime` | Timestamp reports |
| `Path` | Log directory |
| `ChakraClient` | Low-level gRPC client |
| `ChakraSession` | High-level session manager |
| `load_config()` | Load project configuration |

---

# Main Components

## 1. Argument Parser

Accepts a list of conversation turns.

Default:

```text
Turn 1:
Remember the number 42.

Turn 2:
What number did I ask you to remember?
```

Users can override this:

```bash
python scripts/test_session.py \
--turns \
"Hello" \
"Who am I?"
```

---

## 2. Configuration Loading

```python
config = load_config()
```

Loads:

- repository root
- gRPC host
- port
- service information

---

## 3. Client Connection

Creates:

```python
client = ChakraClient(config)
```

Then connects to the running Chakra server.

---

## 4. Session Creation

Creates:

```python
session = ChakraSession(...)
```

Unlike previous scripts, the conversation is now represented as a reusable object.

The session internally owns:

- session ID
- working directory
- conversation history
- completed turns

---

## 5. Sending Multiple Turns

Each user message is sent using:

```python
session.send_message(...)
```

Internally this:

- opens a stream
- sends the message
- waits for completion
- stores the reply
- preserves the same session ID

Example:

```text
Turn 1
User:
Remember the number 42.

Assistant:
I'll remember that.

────────────

Turn 2

User:
What number did I ask you to remember?

Assistant:
42
```

The important part is that both requests belong to the same conversation.

---

## 6. Session Summary

After all turns complete:

```python
session.summary()
```

returns metadata such as:

- session ID
- total turns
- timestamps
- conversation statistics

---

## 7. Session Closure

Finally:

```python
session.close()
```

marks the session as complete.

---

# Output

Produces:

```text
logs/
└── session_<timestamp>.json
```

Example:

```json
{
    "milestone": "1.4",
    "session": {
        ...
    },
    "turns": [
        ...
    ]
}
```

---

# Dependencies

Uses:

```text
client/config.py
```

for configuration.

Uses:

```text
client/chakra_client.py
```

for all gRPC communication.

Uses:

```text
client/session.py
```

to manage the conversation lifecycle.

---

# Interaction with Other Files

```text
test_session.py
        │
        ▼
client/session.py
        │
        ▼
client/chakra_client.py
        │
        ▼
gRPC Stream
        │
        ▼
Chakra Backend
```

Unlike `test_minimal_chat.py`, this script introduces a persistent session abstraction.

---

# Inputs

Command-line arguments:

```bash
--turns
```

Example:

```bash
python scripts/test_session.py \
--turns \
"Remember my favorite color is blue." \
"What is my favorite color?"
```

Optional:

```bash
--timeout
```

---

# Outputs

### Console

Displays each conversation turn.

Example:

```text
Turn 1 reply:
...

Turn 2 reply:
...
```

---

### JSON Report

Saved under:

```text
logs/
```

Contains:

- session metadata
- user messages
- assistant replies
- event counts

---

### Exit Code

```text
0 → Session completed successfully

1 → Session validation failed
```

---

# Why This File Exists

Earlier milestones verified:

- environment setup
- connectivity
- single-turn chat

However, real conversational systems depend on maintaining context across multiple interactions.

This script verifies that:

- the same `session_id` is reused,
- Chakra correctly remembers previous turns,
- the Python session abstraction behaves as expected.

It is the first validation of conversational state rather than isolated request-response communication.

---

# Relationship to Other Milestones

```text
Milestone 1.1
verify_chakra.py
(Environment Verification)
        │
        ▼
Milestone 1.2
test_connectivity.py
(gRPC Connection)
        │
        ▼
Milestone 1.3
test_minimal_chat.py
(Single-turn Chat)
        │
        ▼
Milestone 1.4
test_session.py
(Multi-turn Conversation)
```

---

# Key Takeaways

- Implements **Milestone 1.4 – Session Validation**.
- Verifies that multiple requests share the same `session_id`.
- Introduces the higher-level `ChakraSession` abstraction over the low-level gRPC client.
- Confirms conversation memory and session lifecycle management.
- Produces a detailed JSON report containing the full multi-turn interaction.


----


# `scripts/generate_proto.py`

## Purpose

`generate_proto.py` is a utility script responsible for generating the Python gRPC client code from the Chakra protobuf specification.

Instead of manually writing Python classes for every protobuf message and RPC service, this script invokes the Protocol Buffer compiler (`protoc`) to automatically generate them.

This ensures that the Python client always stays synchronized with the latest version of Chakra's API.

This script is **not part of the runtime**. It is only executed whenever the protobuf definition changes.

---

# File Location

```text
scripts/
└── generate_proto.py
```

---

# Responsibility

This script performs the following tasks:

- Locate the local protobuf specification
- Invoke the Protocol Buffer compiler
- Generate Python protobuf classes
- Generate Python gRPC client classes
- Patch the generated imports
- Store the generated files in the project

It does **not**:

- Start Chakra
- Connect to the server
- Send messages
- Perform any networking

---

# Execution Flow

```text
Start
   │
   ▼
Locate chakra.proto
   │
   ▼
Create output directory
   │
   ▼
Run grpc_tools.protoc
   │
   ▼
Generate Python protobuf code
   │
   ▼
Patch generated imports
   │
   ▼
Save generated files
```

---

# Imports

```python
import subprocess
import sys
from pathlib import Path
```

### Purpose of Imports

| Import | Purpose |
|---------|----------|
| `subprocess` | Execute the protobuf compiler |
| `sys` | Use the current Python interpreter |
| `Path` | Manage repository paths |

---

# Directory Structure

The script works with three important directories.

```text
client/
├── proto/
│   └── chakra.proto
│
└── generated/
    ├── chakra_pb2.py
    ├── chakra_pb2_grpc.py
    └── __init__.py
```

---

# Main Components

## 1. Repository Paths

The script first computes important directories.

```python
REPO_ROOT
PROTO_DIR
OUT_DIR
```

These point to:

- repository root
- protobuf specification
- generated Python code

---

## 2. Output Directory Creation

```python
OUT_DIR.mkdir(...)
```

Ensures

```text
client/generated/
```

exists.

If missing, it is automatically created.

---

## 3. Package Initialization

```python
(OUT_DIR / "__init__.py").touch()
```

Creates

```text
client/generated/__init__.py
```

allowing Python to import the generated files as a package.

---

## 4. Building the protoc Command

The script constructs the command:

```bash
python -m grpc_tools.protoc
```

Equivalent to:

```bash
python -m grpc_tools.protoc \
-Iclient/proto \
--python_out=client/generated \
--grpc_python_out=client/generated \
client/proto/chakra.proto
```

This command reads:

```text
chakra.proto
```

and generates:

```text
chakra_pb2.py

chakra_pb2_grpc.py
```

---

## 5. Running the Compiler

```python
subprocess.check_call(...)
```

Launches the Protocol Buffer compiler.

If compilation fails, the script immediately exits with an error.

---

## 6. Import Patching

After generation, the script modifies:

```text
chakra_pb2_grpc.py
```

Generated code normally contains:

```python
import chakra_pb2 as chakra__pb2
```

which only works when both files are in the same directory.

Inside this project the correct import is:

```python
from client.generated import chakra_pb2 as chakra__pb2
```

The script automatically performs this replacement.

Without this patch, importing the generated module would fail.

---

# Generated Files

Running this script creates:

```text
client/generated/
├── chakra_pb2.py
├── chakra_pb2_grpc.py
└── __init__.py
```

These files should **never be edited manually**.

Any changes would be overwritten the next time the script is executed.

---

# Dependencies

Requires:

```text
client/proto/chakra.proto
```

Requires the package:

```text
grpcio-tools
```

which provides:

```text
grpc_tools.protoc
```

---

# Interaction with Other Files

```text
generate_proto.py
        │
        ▼
client/proto/chakra.proto
        │
        ▼
grpc_tools.protoc
        │
        ▼
client/generated/
        ├── chakra_pb2.py
        └── chakra_pb2_grpc.py
```

Every runtime component depends on these generated files.

---

# Inputs

Input protobuf specification:

```text
client/proto/chakra.proto
```

---

# Outputs

Generated Python files:

```text
client/generated/chakra_pb2.py

client/generated/chakra_pb2_grpc.py
```

---

# When Should This Script Be Run?

Run this script whenever:

- `chakra.proto` changes
- Chakra introduces new RPC methods
- New protobuf messages are added
- Existing message definitions are modified

For normal project usage, this script does **not** need to be executed repeatedly.

---

# Why This File Exists

Writing protobuf serialization code manually would be impractical and error-prone.

This script automates the generation of all Python message classes and gRPC stubs directly from the protobuf specification, ensuring that the client remains fully synchronized with the Chakra backend.

The additional import patch guarantees that the generated files integrate correctly with the project's package structure.

---

# Relationship to Other Files

```text
chakra.proto
      │
      ▼
generate_proto.py
      │
      ▼
chakra_pb2.py
      │
      ▼
chakra_pb2_grpc.py
      │
      ▼
chakra_client.py
```

This script is the bridge between the protobuf specification and the Python implementation.

---

# Key Takeaways

- Generates all Python protobuf and gRPC client code from `chakra.proto`.
- Creates `chakra_pb2.py` and `chakra_pb2_grpc.py`.
- Automatically patches imports to match the project's package structure.
- Should only be run when the protobuf specification changes.
- Is a development utility and is **not** part of the runtime execution path.


----


# `scripts/start_chakra.sh`

## Purpose

`start_chakra.sh` is the launcher script responsible for starting the Chakra gRPC backend from the Headless Harness project.

Instead of manually navigating to the Chakra repository, loading environment variables, and running the appropriate Bun command, this script automates the entire startup process.

This is the standard entry point used throughout Phase 1 whenever the real Chakra backend needs to be started.

---

# File Location

```text
scripts/
└── start_chakra.sh
```

---

# Responsibility

This script performs the following tasks:

- Locate the project root
- Load project environment variables
- Configure gRPC host and port
- Verify Bun is installed
- Navigate to the Chakra repository
- Start the Chakra gRPC server

It does **not**:

- Compile protobuf files
- Validate connectivity
- Send chat requests
- Perform any client-side operations

---

# Execution Flow

```text
Start
   │
   ▼
Locate project root
   │
   ▼
Load .env
   │
   ▼
Configure gRPC variables
   │
   ▼
Verify Bun installation
   │
   ▼
Navigate to Chakra
   │
   ▼
Run Bun startup command
   │
   ▼
Chakra gRPC Server Running
```

---

# Shell Components

The script begins with:

```bash
#!/usr/bin/env bash
```

This allows the script to execute using the system's Bash interpreter regardless of its installation location.

---

# Strict Error Handling

```bash
set -euo pipefail
```

Enables strict shell behavior.

### Meaning

| Option | Purpose |
|---------|----------|
| `-e` | Exit immediately if any command fails |
| `-u` | Treat undefined variables as errors |
| `pipefail` | Fail if any command in a pipeline fails |

This prevents partially executed startup sequences.

---

# Repository Root Detection

```bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
```

Automatically determines the repository root regardless of where the script is executed.

Example:

```text
headless_harness/
├── scripts/
│   └── start_chakra.sh
```

After execution:

```text
ROOT = headless_harness/
```

This avoids hardcoded paths.

---

# Loading Environment Variables

The script checks for:

```text
.env
```

If present:

```bash
set -a
source "$ROOT/.env"
set +a
```

This exports every variable inside `.env` into the current shell.

Example:

```text
OPENAI_BASE_URL=...
OPENAI_MODEL=...
OPENAI_API_KEY=...
GRPC_HOST=...
GRPC_PORT=...
```

These variables become available to the Chakra backend when it starts.

---

# Chakra Repository Location

The script computes:

```bash
CHAKRA_ROOT="$ROOT/harness/chakra"
```

Result:

```text
headless_harness/
└── harness/
    └── chakra/
```

All subsequent commands are executed from this directory.

---

# gRPC Configuration

The script exports:

```bash
export GRPC_HOST="${GRPC_HOST:-localhost}"
export GRPC_PORT="${GRPC_PORT:-50051}"
```

This means:

- use values from `.env` if available
- otherwise fall back to:

```text
localhost
50051
```

This allows configuration without modifying the script.

---

# Bun Verification

The script checks:

```bash
command -v bun
```

If Bun is unavailable, startup stops immediately.

The user receives:

```text
error: bun is required
```

along with guidance for installing Bun or using the mock server.

---

# Starting Chakra

The script changes directory:

```bash
cd "$CHAKRA_ROOT"
```

and executes:

```bash
bun run dev:grpc
```

The `exec` command replaces the current shell process with the Chakra server process.

This means:

```text
start_chakra.sh
        │
        ▼
bun run dev:grpc
        │
        ▼
src/grpc/server.ts
```

Once the server starts, the shell is now directly attached to the Chakra process.

---

# Dependencies

Requires:

```text
Bun
```

Requires:

```text
harness/chakra/
```

Requires:

```text
.env
```

(optional but recommended)

---

# Interaction with Other Files

```text
start_chakra.sh
        │
        ▼
.env
        │
        ▼
Environment Variables
        │
        ▼
bun run dev:grpc
        │
        ▼
harness/chakra/src/grpc/server.ts
        │
        ▼
gRPC Server
```

This script is the bridge between the Headless Harness project and the Chakra backend.

---

# Inputs

Reads:

```text
.env
```

Uses:

```text
GRPC_HOST
GRPC_PORT
OPENAI_BASE_URL
OPENAI_MODEL
OPENAI_API_KEY
```

if present.

---

# Outputs

### Console

Displays startup status.

Example:

```text
Starting Chakra gRPC at localhost:50051...
```

Once successful:

```text
gRPC Server running at localhost:50051
```

---

### Running Server

Leaves the terminal attached to the running Chakra backend until interrupted.

---

# Why This File Exists

Without this script, developers would need to manually:

1. Activate the environment
2. Load `.env`
3. Export variables
4. Navigate to the Chakra repository
5. Execute the correct Bun command

This script encapsulates all of those steps into a single command:

```bash
./scripts/start_chakra.sh
```

making backend startup consistent, reproducible, and less error-prone.

---

# Relationship to Other Files

```text
start_chakra.sh
        │
        ▼
.env
        │
        ▼
src/grpc/server.ts
        │
        ▼
Chakra gRPC Backend
        │
        ▼
test_connectivity.py
        │
        ▼
test_minimal_chat.py
        │
        ▼
test_session.py
```

This script starts the backend that every other Phase 1 validation script communicates with.

---

# Key Takeaways

- Standard launcher for the real Chakra backend.
- Loads project environment variables automatically from `.env`.
- Configures the gRPC host and port before startup.
- Verifies Bun is installed before attempting to launch the server.
- Starts `src/grpc/server.ts` using `bun run dev:grpc`.
- Serves as the entry point for all runtime testing performed in Phase 1.


----


