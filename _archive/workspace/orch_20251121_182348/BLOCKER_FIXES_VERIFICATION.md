# Blocker Fixes Verification

## 1) Permission Recovery Loop (Codex)
- **Status:** UNRESOLVED  
- **Findings:** `workers.py` now builds the Codex command with `--skip-git-repo-check`, but the recovery path still does not add the flag when a permission failure occurs. `_fix_codex_permissions` simply stops and relaunches the worker without mutating the command or tracking retries.  
- **Evidence:** Stubbed recovery call shows relaunch happens with the original command and no skip flag injection:  
```
python3 - <<'PY'
from types import SimpleNamespace
from orchestrator.recovery import PermissionRecoveryEngine
from orchestrator.models import AgentName
from pathlib import Path
import tempfile

class DummyWorker:
    def __init__(self):
        self.name = AgentName.CODEX
        self.command = ["codex", "exec", "--json"]
        self.stop_called = False
        self.launch_called = False
    def stop(self): self.stop_called = True
    def launch(self): self.launch_called = True

with tempfile.TemporaryDirectory() as tmp:
    engine = PermissionRecoveryEngine(Path(tmp), Path(tmp), Path(tmp))
    worker = DummyWorker()
    engine._fix_codex_permissions(worker)
    print({'stop_called': worker.stop_called, 'launch_called': worker.launch_called,
           'command_after': worker.command,
           'skip_flag_present': any('--skip-git-repo-check' in part for part in worker.command)})
PY
```
Output: `{'stop_called': True, 'launch_called': True, 'command_after': ['codex', 'exec', '--json'], 'skip_flag_present': False}`

## 2) Event Detection (stderr parsing / offset tracking)
- **Status:** UNRESOLVED  
- **Findings:** Recovery only inspects events of type `ERROR`; permission text inside progress/milestone events is ignored. Worker stdout parsing fails for any event without an explicit timestamp because `_parse_event` references `datetime` without importing it, causing events to be discarded before recovery/state updates run.  
- **Evidence:**  
  - Progress event containing permission text is ignored: `engine.check_for_errors(...)` returns `None` for a `PROGRESS` event with `Not inside a trusted directory`.  
  - Parsing any event without a timestamp raises and drops the event:  
```
python3 - <<'PY'
import tempfile
from pathlib import Path
from orchestrator.workers import WorkerProcess
from orchestrator.models import AgentName

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    (tmp/'target').mkdir(); (tmp/'orch').mkdir()
    wp = WorkerProcess(AgentName.GEMINI, 'test', tmp, tmp/'target', tmp/'orch')
    evt = wp._parse_event({"type": "progress", "payload": {"text": "hello", "progress": 10}})
    print("Parsed event:", evt)
PY
```
Output: `Failed to parse event from gemini: local variable 'datetime' referenced before assignment` and `Parsed event: None`

## 3) Worker State Updates
- **Status:** UNRESOLVED  
- **Findings:** No code applies event-derived progress/status to `WorkerState`. `Coordinator.monitor_loop` overwrites session workers with the static `WorkerProcess.state` objects, which are never mutated from parsed events. Because `_parse_event` fails (above), even basic progress events are dropped, leaving states at defaults.  
- **Evidence:** Reading a progress event leaves the worker at 0% progress:  
```
python3 - <<'PY'
import tempfile, json
from pathlib import Path
from orchestrator.workers import WorkerProcess
from orchestrator.models import AgentName

with tempfile.TemporaryDirectory() as tmp:
    ws = Path(tmp); (ws/'target').mkdir(); (ws/'orch').mkdir()
    (ws/'gemini.jsonl').write_text(json.dumps({"type":"progress","payload":{"text":"Working","progress":50}})+"\n")
    worker = WorkerProcess(AgentName.GEMINI, 'test', ws, ws/'target', ws/'orch')
    events = worker.read_events()
    print("Events parsed:", events)
    print("Worker progress after parsing:", worker.state.progress)
PY
```
Output: `Events parsed: []` and `Worker progress after parsing: 0`

## 4) Review Engine Implementation
- **Status:** UNRESOLVED  
- **Findings:** The decision tree in `evaluate_reviews` returns the correct actions when called, but `Coordinator.conduct_peer_review` is stubbed to always `CONTINUE` without sending/awaiting review requests or applying the decision logic. `should_trigger_review` ignores `request_review` events and the 15-minute fallback until `last_review_time` is set, so reviews will not trigger per spec.  
- **Evidence:** `Coordinator.conduct_peer_review` contains TODO comments and bypasses review responses entirely.

## 5) API Compliance
- **Status:** UNRESOLVED  
- **Findings:** FastAPI routes are global, not session-scoped (`/api/session`, `/api/workers`, etc.). `/api/events/stream` emits aggregate worker/status blobs instead of typed `agent_event`/`recovery_event` SSEs, and it omits session IDs. The manual review endpoint calls the stubbed `conduct_peer_review` and never delivers the review request payload specified in `REVIEW_SYSTEM_SPEC.md`.  
- **Evidence:** `orchestrator/server.py` defines a single global `coordinator` and hard-coded routes; SSE generator builds `workers_update/decision_update/status_update` instead of the envelope in `API_SSE_SPEC.md`.

## 6) Security Sandbox
- **Status:** UNRESOLVED  
- **Findings:** `SafetyEnforcer` exists but is never constructed or passed to the Claude worker. Worker launch paths simply execute `claude --dangerously-skip-permissions ...` with no command filtering, path validation, or sandbox enforcement. No directory restrictions are applied around the Claude subprocess.  
- **Evidence:** No references to `SafetyEnforcer` or `create_default_sandbox` outside `orchestrator/safety.py`; `workers.py::_build_claude_command` launches Claude directly.
