# Complete Flow Diagram

## System Lifecycle

The orchestration process follows a linear flow with cyclic monitoring and recovery branches.

### 1. Initialization Phase
1.  **User Command**: `/orchestrate "task"`
2.  **Task Analysis**: Orchestrator decomposes task -> `[Gemini Task, Claude Task, Codex Task]`
3.  **Permissions Setup (Proactive)**:
    - Validate/Create `workspace_dir`
    - Validate `target_dir`
    - `chmod 755` if needed
4.  **Dashboard Launch**: Start API server & UI.

### 2. Execution Phase (The Loop)

**Launch Workers** (with Fallback Strategy)

**Main Loop:**
```mermaid
graph TD
    A[Monitor Worker Streams] --> B{Event Received?}
    B -- Yes --> C[Parse Event]
    B -- No --> D{Timeout > 15m?}
    D -- Yes --> E[Trigger Timeout Review]
    D -- No --> A

    C --> F{Is Error?}
    F -- Yes --> G[Permission Recovery Engine]
    
    G --> H{Can Auto-Fix?}
    H -- Yes --> I[Stop Worker]
    I --> J[Adjust Flags]
    J --> K[Relaunch Worker]
    K --> A
    H -- No --> L[ESCALATE: Pause & Notify User]

    F -- No --> M{Is Review Trigger?}
    M -- Yes --> N[Initiate Review Cycle]
    M -- No --> O[Update State/Dashboard]
    O --> A

    N --> P[Collect Peer Reviews]
    P --> Q[Decision Logic]
    Q -- Blocker --> R[STOP_AND_ESCALATE]
    Q -- 2+ Concerns --> S[PAUSE_AND_CLARIFY]
    Q -- 1 Concern --> T[LOG_AND_CONTINUE]
    Q -- Approved --> U[CONTINUE]
    
    T --> A
    U --> A
```

### 3. Completion Phase
- **Trigger**: All agents report `MILESTONE: COMPLETE`
- **Final Review**: Full consistency check.
- **Success**: `DEFINITION_OF_DONE` met.
- **Artifacts**: Source code, tests, documentation finalized in `target_dir`.
