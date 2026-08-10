# Smoke-run all 10 task_games_* projects (headless where possible).
# Usage: pwsh -File harness/chakra/run_all_games_smoke.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
$env:PYGAME_HIDE_SUPPORT_PROMPT = "1"

$results = @()

function Ok($name, $detail) {
  Write-Host "[PASS] $name — $detail" -ForegroundColor Green
  $script:results += [pscustomobject]@{ Task = $name; Status = "PASS"; Detail = $detail }
}
function Fail($name, $detail) {
  Write-Host "[FAIL] $name — $detail" -ForegroundColor Red
  $script:results += [pscustomobject]@{ Task = $name; Status = "FAIL"; Detail = $detail }
}

# --- 01 Core Tap (pytest) ---
Push-Location (Join-Path $Root "task_games_01")
try {
  $out = & python -m pytest -q --tb=line 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) { Ok "01" ($out.Trim() -replace "`r?`n", " ") }
  else { Fail "01" $out.Trim() }
} catch { Fail "01" $_.Exception.Message }
Pop-Location

# --- 02 Rustwake (vitest + smoke) ---
Push-Location (Join-Path $Root "task_games_02")
try {
  if (-not (Test-Path "node_modules")) {
    npm install --silent 2>&1 | Out-Null
  }
  $t = & npm run test 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) { Fail "02-test" $t.Trim(); Pop-Location; throw "stop" }
  $s = & npm run smoke 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) { Ok "02" "test+smoke ok" }
  else { Fail "02" $s.Trim() }
} catch {
  if ($_.Exception.Message -ne "stop") { Fail "02" $_.Exception.Message }
}
Pop-Location

# --- 03-10 pygame demos (auto-quit after ~2s via QUIT event) ---
$smokePy = Join-Path $Root "_smoke_pygame_main.py"
@'
"""Headless smoke: run main.py under dummy SDL and post QUIT after a short delay."""
import os, sys, time, threading

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

game_dir = sys.argv[1]
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
os.chdir(game_dir)
sys.path.insert(0, game_dir)

import pygame  # noqa: E402

pygame.init()


def _quit_soon():
    time.sleep(seconds)
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    except Exception:
        pass
    time.sleep(1.0)
    os._exit(0)


threading.Thread(target=_quit_soon, daemon=True).start()
path = os.path.join(game_dir, "main.py")
with open(path, encoding="utf-8") as f:
    code = f.read()
ns = {"__name__": "__main__", "__file__": path}
exec(compile(code, path, "exec"), ns)
print("SMOKE_OK", game_dir)
'@ | Set-Content -Path $smokePy -Encoding UTF8

3..10 | ForEach-Object {
  $n = "{0:D2}" -f $_
  $dir = Join-Path $Root "task_games_$n"
  if (-not (Test-Path (Join-Path $dir "main.py"))) {
    Fail $n "missing main.py"
    return
  }
  # ensure pygame deps
  $req = Join-Path $dir "requirements.txt"
  if (Test-Path $req) {
    pip install -q -r $req 2>$null | Out-Null
  }
  $proc = Start-Process -FilePath "python" -ArgumentList @($smokePy, $dir, "1.5") `
    -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $env:TEMP "g$n.out") `
    -RedirectStandardError (Join-Path $env:TEMP "g$n.err")
  $ok = $proc.WaitForExit(15000)
  if (-not $ok) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail $n "timeout (>15s)"
  } elseif ($proc.ExitCode -eq 0) {
    Ok $n "pygame smoke exited 0"
  } else {
    $err = Get-Content (Join-Path $env:TEMP "g$n.err") -Raw -ErrorAction SilentlyContinue
    Fail $n "exit $($proc.ExitCode) $err"
  }
}

Write-Host ""
Write-Host "==== SUMMARY ===="
$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
exit $failed
