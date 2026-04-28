# Chaos engineer — improvement checklist (FileTugger)

Use this to plan safe resilience experiments for the API, download pipeline, and queue—not for production without controls. Aligns with `chaos-engineer.md`.

## Prerequisites

- [ ] Steady state defined (e.g. API responds healthy, queue eventually drains, no unbounded growth of stuck items).
- [ ] Metrics and logs available to observe impact (queue depth, errors, latency).
- [ ] Blast radius limited (staging, single instance, or feature-flagged subset).

## Hypothesis and safety

- [ ] Experiment hypothesis written: what fails, what should happen, what would surprise you.
- [ ] Rollback or stop condition documented (restart container, clear test queue, revert flag).
- [ ] Customer/user impact explicitly “none” or accepted for the environment.

## Failure modes to consider

- [ ] **Network**: latency, DNS failure, or disconnect during HTTP download or Mega communication.
- [ ] **Process**: Mega subprocess killed mid-operation; API restart during active transfer.
- [ ] **Disk**: full disk or permission errors on download directory.
- [ ] **Dependency**: external URL unreachable or returns unexpected status codes.

## Execution

- [ ] One variable changed per experiment when learning baseline behaviour.
- [ ] Duration and observation window agreed; results captured (timestamps, logs).

## Learning and follow-up

- [ ] Findings logged; bugs or runbook gaps filed.
- [ ] Monitoring or alerts improved if the experiment showed blind spots.
- [ ] Automated regression or chaos-lite checks added to CI only when stable and fast enough.

## Organization (optional)

- [ ] Game day or repeat schedule agreed if resilience testing is ongoing.
