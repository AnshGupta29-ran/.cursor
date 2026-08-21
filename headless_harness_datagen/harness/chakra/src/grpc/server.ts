// harness/chakra/src/grpc/server.ts
import * as grpc from '@grpc/grpc-js'
import * as protoLoader from '@grpc/proto-loader'
import path from 'path'
import { randomUUID } from 'crypto'
import { setOriginalCwd, setProjectRoot } from '../bootstrap/state.js'
import { QueryEngine } from '../QueryEngine.js'
import { filterToolsByDenyRules, getTools } from '../tools.js'
import { BashTool } from '../tools/BashTool/BashTool.js'
import { FileEditTool } from '../tools/FileEditTool/FileEditTool.js'
import { FileReadTool } from '../tools/FileReadTool/FileReadTool.js'
import { FileWriteTool } from '../tools/FileWriteTool/FileWriteTool.js'
import { getDefaultAppState } from '../state/AppStateStore.js'
import { AppState } from '../state/AppState.js'
import { FileStateCache, READ_FILE_STATE_CACHE_SIZE } from '../utils/fileStateCache.js'
import { GRPC_BUILTIN_AGENTS } from './builtInGrpcAgents.js'
import {
  getGitStatus,
  getSystemContext,
  getUserContext,
} from '../context.js'
import { clearToolSchemaCache } from '../utils/toolSchemaCache.js'

const PROTO_PATH = path.resolve(import.meta.dirname, '../proto/openclaude.proto')

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
})

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any
const chakraProto = protoDescriptor.chakra.v1

const MAX_SESSIONS = 1000

const GRPC_SYSTEM_PROMPT = `You are a coding agent. Stay inside the assigned repository.
Use Write and Edit. Do not spawn Agent, Plan, or Explore. Do not loop ls or cargo.
Never print IMPLEMENTATION_STATUS: COMPLETE until ALL exist: README.md, scripts/smoke.py (or npm run smoke), fixtures/ or data/ seed files, and a working demo matching platform_prompt.md.
If some source already exists, keep writing the missing pieces. Do not rebuild from zero. Never ls -R.
If cargo/link/dlltool fails once on Windows, stop looping the compiler — keep source plus a best-effort smoke.`

const SLIM_TOOL_PROMPTS: Record<string, string> = {
  Read: 'Read a file. Arguments: file_path, optional offset, limit.',
  Write: 'Write a file. Arguments: file_path, content. Overwrites.',
  Edit: 'Replace exact text in a file. Arguments: file_path, old_string, new_string.',
  Bash: 'Run a shell command in the repo cwd. Argument: command. Never ls -R; ignore target/. Do not cargo in a loop if dlltool/link fails — Write/Edit instead.',
}

const MAX_SESSION_MESSAGES = 8
const TOOL_RESULT_MAX_CHARS = 2000
const READ_LINE_CAP = 200

function slimBashCommand(command: string): string {
  const trimmed = command.trim()
  const isTreeDump =
    /^ls\s+-R(\s+\.)?$/i.test(trimmed) ||
    /^ls\s+-R\s/i.test(trimmed) ||
    /^ls\s+-la;\s*ls src/i.test(trimmed) ||
    /ls Cargo\.toml package\.json/i.test(trimmed)
  if (isTreeDump) {
    // Always-succeed listing. `ls src; ls Cargo.toml package.json` exits 2 on
    // TS/Python workdirs (missing Cargo.toml) and session-health kills the run.
    const safe = 'ls -la'
    console.log(`gRPC slimBash: rewrote tree dump -> ${safe}`)
    return safe
  }
  if (/^find\s+\.\s+-type\s+f/i.test(trimmed) && !trimmed.includes('-prune')) {
    const safe =
      'find . \\( -name target -o -name node_modules -o -name .venv \\) -prune -o -type f -print'
    console.log(`gRPC slimBash: rewrote find dump -> ${safe.slice(0, 80)}`)
    return safe
  }
  return command
}

function resolveGrpcModel(requestModel: string | undefined): string {
  return (requestModel || process.env.OPENAI_MODEL || '').trim()
}

function stripFatReminders(text: string): string {
  return text.replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, '').trim()
}

function capText(text: string, maxChars = TOOL_RESULT_MAX_CHARS): string {
  const cleaned = stripFatReminders(text)
  if (cleaned.length <= maxChars) return cleaned
  return `${cleaned.slice(0, maxChars)}\n...[truncated]`
}

function capContent(content: unknown, maxChars = TOOL_RESULT_MAX_CHARS): unknown {
  if (typeof content === 'string') return capText(content, maxChars)
  if (!Array.isArray(content)) return content
  return content.map((block: any) => {
    if (!block || typeof block !== 'object') return block
    if (typeof block.content === 'string') {
      return { ...block, content: capText(block.content, maxChars) }
    }
    if (typeof block.text === 'string') {
      return { ...block, text: capText(block.text, maxChars) }
    }
    return block
  })
}

function isApiHistoryMessage(msg: unknown): boolean {
  if (!msg || typeof msg !== 'object') return false
  const t = (msg as { type?: string }).type
  return t === 'user' || t === 'assistant'
}

function truncateSessionMessages(messages: unknown[], maxChars = TOOL_RESULT_MAX_CHARS): unknown[] {
  return messages.map((msg) => {
    if (!msg || typeof msg !== 'object') return msg
    const rec = msg as Record<string, any>
    const inner = rec.message ?? rec
    if (inner.content === undefined) return msg
    const nextContent = capContent(inner.content, maxChars)
    if (rec.message) {
      return { ...rec, message: { ...rec.message, content: nextContent } }
    }
    return { ...rec, content: nextContent }
  })
}

function capSessionMessages(messages: unknown[], maxMessages = MAX_SESSION_MESSAGES): unknown[] {
  if (messages.length <= maxMessages) return messages
  const first = messages[0]
  const rest = messages.slice(1)
  const tail = rest.slice(-(maxMessages - 1))
  console.log(`gRPC session trim: ${messages.length} -> ${maxMessages} (kept bootstrap)`)
  return [first, ...tail]
}

function prepareSessionMessages(messages: unknown[]): unknown[] {
  const apiOnly = messages.filter(isApiHistoryMessage)
  const dropped = messages.length - apiOnly.length
  if (dropped > 0) {
    console.log(`gRPC session drop non-api msgs: ${dropped}`)
  }
  return capSessionMessages(truncateSessionMessages(apiOnly))
}

function truncateToolResultBlock(block: any): any {
  if (!block || typeof block !== 'object') return block
  return { ...block, content: capContent(block.content) }
}

function jsonPayloadChars(value: unknown): number {
  try {
    return JSON.stringify(value).length
  } catch {
    return 0
  }
}

function grpcTools(permissionContext: Parameters<typeof getTools>[0]) {
  // Full Claude-Code tool schemas (~dozens) time out gpt-oss on TensorStudio
  // before first token. Datagen only needs repo read/write/shell.
  if (process.env.CHAKRA_GRPC_FULL_TOOLS === '1') {
    return getTools(permissionContext)
  }
  const slim = [
    FileReadTool,
    FileWriteTool,
    FileEditTool,
    BashTool,
  ].filter(tool => tool.isEnabled())
  if (process.env.CHAKRA_GRPC_FULL_TOOLS !== '1') {
    // toolToAPISchema caches by tool.name for the process lifetime. Without
    // clearing, the first full Bash prompt (~4k tokens) sticks forever.
    clearToolSchemaCache()
  }
  return filterToolsByDenyRules(slim, permissionContext).map(tool => {
    const origMap = (tool as any).mapToolResultToToolResultBlockParam?.bind(tool)
    return {
      ...tool,
      prompt: async () => SLIM_TOOL_PROMPTS[tool.name] ?? tool.name,
      mapToolResultToToolResultBlockParam: origMap
        ? (data: unknown, toolUseID: string) =>
            truncateToolResultBlock(origMap(data, toolUseID))
        : (tool as any).mapToolResultToToolResultBlockParam,
    }
  })
}

export class GrpcServer {
  private server: grpc.Server
  private sessions: Map<string, any[]> = new Map()
  private slimToolSchemaChars = 0
  private slimToolSchemaMeasured = false

  constructor() {
    this.server = new grpc.Server()
    this.server.addService(chakraProto.AgentService.service, {
      Chat: this.handleChat.bind(this),
    })
  }

  start(port: number = 50051, host: string = 'localhost') {
    this.server.bindAsync(
      `${host}:${port}`,
      grpc.ServerCredentials.createInsecure(),
      (error, boundPort) => {
        if (error) {
          console.error('Failed to start gRPC server')
          return
        }
        console.log(`gRPC Server running at ${host}:${boundPort}`)
      }
    )
  }

  private async measureSlimToolSchemas(
    tools: ReturnType<typeof grpcTools>,
    permissionContext: Parameters<typeof getTools>[0],
  ): Promise<number> {
    if (this.slimToolSchemaMeasured) {
      return this.slimToolSchemaChars
    }
    const { toolToAPISchema } = await import('../utils/api.js')
    let total = 0
    for (const tool of tools) {
      const schema = await toolToAPISchema(tool, {
        getToolPermissionContext: async () => permissionContext,
        tools,
        agents: [],
      })
      total += JSON.stringify(schema).length
    }
    this.slimToolSchemaChars = total
    this.slimToolSchemaMeasured = true
    console.log(
      `gRPC slim tool schemas: ${total} chars (~${Math.ceil(total / 4)} tokens) for ${tools.length} tools`,
    )
    return total
  }

  private handleChat(call: grpc.ServerDuplexStream<any, any>) {
    let engine: QueryEngine | null = null
    let appState: AppState = getDefaultAppState()
    const fileCache: FileStateCache = new FileStateCache(READ_FILE_STATE_CACHE_SIZE, 25 * 1024 * 1024)

    // To handle ActionRequired (ask user for permission)
    const pendingRequests = new Map<string, (reply: string) => void>()

    // Accumulated messages from previous turns for multi-turn context
    let previousMessages: any[] = []
    let sessionId = ''
    let interrupted = false

    call.on('data', async (clientMessage) => {
      try {
        if (clientMessage.request) {
          if (engine) {
            call.write({
              error: {
                message: 'A request is already in progress on this stream',
                code: 'ALREADY_EXISTS'
              }
            })
            return
          }
          interrupted = false
          const req = clientMessage.request
          sessionId = req.session_id || ''
          previousMessages = []

          // Load previous messages from session store (cross-stream persistence)
          if (sessionId && this.sessions.has(sessionId)) {
            previousMessages = prepareSessionMessages(this.sessions.get(sessionId)!)
          }

          const toolNameById = new Map<string, string>()
          let sawToolResult = false

          const workDir = req.working_directory || process.cwd()
          // Align gRPC workspace init with the CLI: client working_directory
          // becomes the session project root and permission root (originalCwd).
          setOriginalCwd(workDir)
          setProjectRoot(workDir)
          // Do not recompute git status / CLAUDE.md on every turn. A cargo
          // target/ tree makes `git status --short` expensive, and customSystemPrompt
          // already skips getSystemContext.
          if (process.env.CHAKRA_GRPC_FULL_TOOLS === '1') {
            getUserContext.cache?.clear?.()
            getGitStatus.cache?.clear?.()
            getSystemContext.cache?.clear?.()
          }
          const chatModel = resolveGrpcModel(req.model)
          const userMessage = String(req.message || '')
          const historyChars = jsonPayloadChars(previousMessages)
          const tools = grpcTools(appState.toolPermissionContext)
          const toolSchemaChars = await this.measureSlimToolSchemas(
            tools,
            appState.toolPermissionContext,
          )
          const estPromptChars =
            userMessage.length +
            historyChars +
            GRPC_SYSTEM_PROMPT.length +
            toolSchemaChars
          console.log(
            `gRPC Chat msgChars=${userMessage.length} historyMsgs=${previousMessages.length} ` +
              `historyChars=${historyChars} toolSchemaChars=${toolSchemaChars} ` +
              `estPromptTokens~${Math.ceil(estPromptChars / 4)} ` +
              `session=${sessionId || 'new'} model=${chatModel || '(env default)'}`,
          )

          engine = new QueryEngine({
            cwd: workDir,
            tools,
            commands: [], // Slash commands
            mcpClients: [],
            customSystemPrompt:
              process.env.CHAKRA_GRPC_FULL_TOOLS === '1'
                ? undefined
                : GRPC_SYSTEM_PROMPT,
            thinkingConfig: { type: 'disabled' },
            agents:
              process.env.CHAKRA_GRPC_FULL_TOOLS === '1'
                ? GRPC_BUILTIN_AGENTS
                : [],
            ...(previousMessages.length > 0 ? { initialMessages: previousMessages } : {}),
            includePartialMessages: true,
            canUseTool: async (tool, input, context, assistantMsg, toolUseID) => {
              if (tool.name === 'Bash' && input && typeof (input as any).command === 'string') {
                ;(input as any).command = slimBashCommand((input as any).command)
              }
              if (tool.name === 'Read' && input && typeof input === 'object') {
                const rec = input as Record<string, unknown>
                const limit = rec.limit
                if (typeof limit !== 'number' || limit > READ_LINE_CAP) {
                  rec.limit = READ_LINE_CAP
                }
                // Avoid Read of a directory (Chakra token-counts the listing and throws).
                const fp = String(rec.file_path || rec.path || '')
                if (fp.endsWith('\\') || fp.endsWith('/') || /[\\/]$/.test(fp)) {
                  rec.file_path = fp.replace(/[\\/]+$/, '') + '/platform_prompt.md'
                }
              }
              if (toolUseID) {
                toolNameById.set(toolUseID, tool.name)
              }
              // Notify client of the tool call first
              call.write({
                tool_start: {
                  tool_name: tool.name,
                  arguments_json: JSON.stringify(input),
                  tool_use_id: toolUseID
                }
              })

              // Ask user for permission
              const promptId = randomUUID()
              const question = `Approve ${tool.name}?`
              call.write({
                action_required: {
                  prompt_id: promptId,
                  question,
                  type: 'CONFIRM_COMMAND'
                }
              })

              return new Promise((resolve) => {
                pendingRequests.set(promptId, (reply) => {
                  if (reply.toLowerCase() === 'yes' || reply.toLowerCase() === 'y') {
                    resolve({ behavior: 'allow' })
                  } else {
                    resolve({ behavior: 'deny', reason: 'User denied via gRPC' })
                  }
                })
              })
            },
            getAppState: () => appState,
            setAppState: (updater) => { appState = updater(appState) },
            readFileCache: fileCache,
            userSpecifiedModel: chatModel || undefined,
            fallbackModel: chatModel || undefined,
          })

          // Track accumulated response data for FinalResponse
          let fullText = ''
          let promptTokens = 0
          let completionTokens = 0

          const generator = engine.submitMessage(req.message)

          for await (const msg of generator) {
            if (msg.type === 'stream_event') {
              if (msg.event.type === 'content_block_delta' && msg.event.delta.type === 'text_delta') {
                call.write({
                  text_chunk: {
                    text: msg.event.delta.text
                  }
                })
                fullText += msg.event.delta.text
              }
            } else if (msg.type === 'user') {
              // Extract tool results
              const content = msg.message.content
              if (Array.isArray(content)) {
                for (const block of content) {
                  if (block.type === 'tool_result') {
                    let outputStr = ''
                    if (typeof block.content === 'string') {
                      outputStr = block.content
                    } else if (Array.isArray(block.content)) {
                      outputStr = block.content.map(c => c.type === 'text' ? c.text : '').join('\n')
                    }
                    sawToolResult = true
                    call.write({
                      tool_result: {
                        tool_name: toolNameById.get(block.tool_use_id) ?? block.tool_use_id,
                        tool_use_id: block.tool_use_id,
                        output: outputStr,
                        is_error: block.is_error || false
                      }
                    })
                  }
                }
              }
            } else if (msg.type === 'result') {
              // Extract real token counts and final text from the result
              if (msg.subtype === 'success') {
                if (msg.result) {
                  fullText = msg.result
                }
                promptTokens = msg.usage?.input_tokens ?? 0
                completionTokens = msg.usage?.output_tokens ?? 0
              }
            }
          }

          if (!interrupted) {
            const proxyTimeout =
              /API Error:\s*The operation timed out/i.test(fullText) ||
              ((promptTokens === 0 && completionTokens === 0) &&
                /timed out/i.test(fullText))
            if (proxyTimeout && !sawToolResult) {
              // Cold first-token timeout: drop empty history.
              if (sessionId) {
                this.sessions.delete(sessionId)
              }
              previousMessages = []
            } else if (proxyTimeout && sawToolResult) {
              // Mid-turn timeout after tools: keep session, strip huge dumps.
              previousMessages = prepareSessionMessages(engine.getMessages())
              if (sessionId) {
                this.sessions.set(sessionId, previousMessages)
              }
            } else {
              previousMessages = prepareSessionMessages(engine.getMessages())
              if (sessionId) {
                if (!this.sessions.has(sessionId) && this.sessions.size >= MAX_SESSIONS) {
                  this.sessions.delete(this.sessions.keys().next().value)
                }
                this.sessions.set(sessionId, previousMessages)
              }
            }

            call.write({
              done: {
                full_text: fullText,
                prompt_tokens: promptTokens,
                completion_tokens: completionTokens
              }
            })
            console.log(
              `gRPC Done prompt_tokens=${promptTokens} completion_tokens=${completionTokens} ` +
                `session=${sessionId || 'new'} historyMsgsNext=${previousMessages.length}`,
            )
          }

          engine = null

        } else if (clientMessage.input) {
          const promptId = clientMessage.input.prompt_id
          const reply = clientMessage.input.reply
          if (pendingRequests.has(promptId)) {
            pendingRequests.get(promptId)!(reply)
            pendingRequests.delete(promptId)
          }
        } else if (clientMessage.cancel) {
          interrupted = true
          if (engine) {
            engine.interrupt()
          }
          call.end()
        }
      } catch (err: any) {
        console.error('Error processing stream')
        call.write({
          error: {
            message: err.message || "Internal server error",
            code: "INTERNAL"
          }
        })
        call.end()
      }
    })

    call.on('end', () => {
      interrupted = true
      // Unblock any pending permission prompts so canUseTool can return
      for (const resolve of pendingRequests.values()) {
        resolve('no')
      }
      if (engine) {
        engine.interrupt()
      }
      engine = null
      pendingRequests.clear()
    })
  }
}
