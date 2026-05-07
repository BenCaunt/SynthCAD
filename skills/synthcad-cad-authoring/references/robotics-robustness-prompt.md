# Robotics Robustness Prompt Add-On

Use this block when requesting CAD for structural or drivetrain robot parts.

```text
Design for robustness, serviceability, and manufacturability first.

Mechanical guardrails:
- Add structural fillets/chamfers by default; justify any omitted edge treatment.
- Avoid single-bearing cantilever shaft layouts unless explicitly approved and
  validated against span/load limits.
- Respect process-specific minima for walls, bosses, ribs, and edge distances.
- Preserve tool access, cable bend radii, connector insertion/removal paths,
  and battery/service replacement paths.

Required reasoning output before code:
1) Interface map.
2) Load-path + support strategy.
3) Feature-template plan.
4) Risks and assumptions.

Then emit build123d code.
```
