# Datagen autonomy (overrides default "confirm first / pausing is cheap")

You are instructed to work **fully autonomously** for harness datagen tasks.

## Hard rules
- **Never** ask for confirmation, approval, go-ahead, or "which phase next?"
- **Never** refuse for size, time, or "too big for one response"
- Keep calling tools until acceptance criteria pass; then print `DONE …`
- Do **not** stop after scaffolding, a phase plan, or "please confirm"
- Local file/shell/test work needs no confirmation
- If a tool/package is missing, work around it and keep going (stdlib / alternate stack)

## Dimension lock (synthetic variety — mandatory)
- Honor `language_runtime` from the PRD / CHAKRA_NEXT_TASK (java, rust, go, csharp, cpp, typescript, python, …).
- Do **not** homogenize every task to Python/React unless locked.
- Honor `ui_surface`, `persistence`, and complexity band exactly.

## Pace (stop burning hours on low tasks)
- **low**: few files, complete happy path fast (~15–25 tool calls). No gold-plate.
- **medium**: solid MVP, keep building; no research tours.
- **hard**: full acceptance, still build-first. One failed toolchain install → faithful alternate that keeps UI + API behavior; document swap in README.
- Never spend 2–3 hours searching, reinstalling toolchains, or re-reading the same files.

## Build-first (anti time-waste) — mandatory
- **Write/Edit first.** Implement from the open `platform_prompt.md`.
- **Forbidden:** WebSearch, WebFetch, docs tours, winget/ripgrep scavenger hunts, Explore/research subagents.
- **At most 2** targeted Glob/Grep reads inside **this task’s workdir** before coding.
- Do not Grep sibling tasks or the whole repo.

## Demo quality (not stubs / not tiny demos)
- **Not DONE** if: dead page, hello-world SPA, Cargo.toml-only, README-only, API with no exercise path, upload that does nothing.
- Ship seeded data + one-command run in README + primary workflows that mutate visible state.
- `api_only` still needs an operator console that calls the live API unless PRD forbids UI.

## Pipeline mode (when `CHAKRA_NEXT_TASK.md` is the instruction)
- Implement **only** the single task named there.
- After printing `DONE <task_key>: …`, **STOP**. Do not open the next PRD yourself.
- The outer `datagen_pipeline` checkpoints and feeds the next thin prompt.

## Marathon mode (only if explicitly told to continue through N→N+1)
- After DONE, immediately open the **next** task’s single `platform_prompt.md` (never the whole forged paste file).

## Shells / servers
- Do not leave hung `npm install` / servers across stops.
- Prefer foreground commands; verify health then keep implementing.
- Before DONE, kill orphaned duplicate servers on the same port.
