import { GrpcServer } from '../src/grpc/server.ts'
import { init } from '../src/entrypoints/init.ts'

// Polyfill MACRO which is normally injected by the bundler
Object.assign(globalThis, {
  MACRO: {
    VERSION: '0.1.7',
    DISPLAY_VERSION: '0.1.7',
    PACKAGE_URL: '@gitlawb/chakra',
  }
})

async function main() {
  // Keep tool results small so the next LLM call is not a 30k-char cargo dump.
  if (!process.env.BASH_MAX_OUTPUT_LENGTH) {
    process.env.BASH_MAX_OUTPUT_LENGTH = '1200'
  }
  process.env.CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS ||= '8000'
  process.env.CLAUDE_CODE_DISABLE_CLAUDE_MDS ||= '1'
  process.env.CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS ||= '1'
  process.env.CLAUDE_CODE_DISABLE_THINKING ||= '1'
  process.env.CLAUDE_CODE_DISABLE_BACKGROUND_TASKS ||= '1'
  process.env.CLAUDE_CODE_DISABLE_AUTO_MEMORY ||= '1'
  process.env.CLAUDE_CODE_DISABLE_ATTACHMENTS ||= '1'
  process.env.CLAUDE_CODE_SIMPLE ||= '1'
  process.env.CLAUDE_CODE_SIMPLE ||= '1'
  const { clearToolSchemaCache } = await import('../src/utils/toolSchemaCache.js')
  clearToolSchemaCache()
  console.log('Starting Chakra gRPC Server...')
  await init()

  // Mirror CLI bootstrap: hydrate secure tokens and resolve provider profile
  const { enableConfigs } = await import('../src/utils/config.js')
  enableConfigs()
  const { applySafeConfigEnvironmentVariables } = await import('../src/utils/managedEnv.js')
  applySafeConfigEnvironmentVariables()
  const { hydrateGeminiAccessTokenFromSecureStorage } = await import('../src/utils/geminiCredentials.js')
  hydrateGeminiAccessTokenFromSecureStorage()
  const { hydrateGithubModelsTokenFromSecureStorage } = await import('../src/utils/githubModelsCredentials.js')
  hydrateGithubModelsTokenFromSecureStorage()

  const { buildStartupEnvFromProfile, applyProfileEnvToProcessEnv } = await import('../src/utils/providerProfile.js')
  const { getProviderValidationError, validateProviderEnvOrExit } = await import('../src/utils/providerValidation.js')
  const startupEnv = await buildStartupEnvFromProfile({ processEnv: process.env })
  if (startupEnv !== process.env) {
    const startupProfileError = await getProviderValidationError(startupEnv)
    if (startupProfileError) {
      console.warn(`Warning: ignoring saved provider profile. ${startupProfileError}`)
    } else {
      applyProfileEnvToProcessEnv(process.env, startupEnv)
    }
  }
  await validateProviderEnvOrExit()

  const port = process.env.GRPC_PORT ? parseInt(process.env.GRPC_PORT, 10) : 50051
  const host = process.env.GRPC_HOST || 'localhost'
  const { GRPC_BUILTIN_AGENT_TYPES } = await import('../src/grpc/builtInGrpcAgents.ts')
  console.log(
    `gRPC built-in subagents: ${GRPC_BUILTIN_AGENT_TYPES.join(', ')}`,
  )
  if (process.env.CHAKRA_GRPC_FULL_TOOLS !== '1') {
    console.log('gRPC datagen slim tools: Read/Write/Edit/Bash (no Glob/Grep/Agent)')
  }

  const server = new GrpcServer()

  server.start(port, host)
}

main().catch((err) => {
  console.error('Fatal error starting gRPC server:', err)
  process.exit(1)
})
