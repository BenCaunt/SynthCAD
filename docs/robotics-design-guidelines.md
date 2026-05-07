# Robotics CAD Robustness Guidelines for SynthCAD

This document captures practical, production-minded guidance for generating
robotics parts and assemblies from LLM-authored CAD code. It focuses on
failure modes seen in current outputs (missing fillets, under-constrained
shafts, weak interfaces) and recommends a hybrid workflow that combines LLM
intent with deterministic geometry and validation tools.

## 1) Core Design Philosophy

- Treat the LLM as a **requirements and topology author**, not as the sole
  mechanical authority.
- Encode repeated mechanical patterns (bearing stacks, motor mounts, bosses,
  fastener joints, service envelopes) as deterministic templates.
- Require every generated part to pass both:
  - **geometry checks** (clearances, wall thickness, fillets/chamfers,
    overhangs, draft/printability), and
  - **load-path checks** (support strategy, span limits, bending risk,
    shaft constraints).

## 2) Frequent Failure Modes and Preferred Fixes

### 2.1 Missing fillets/chamfers

Failure mode:
- Sharp internal corners around bosses, cutouts, and rib roots cause stress
  concentration and brittle failure in printed polymers.

Guideline:
- Default to edge treatments unless a mating interface forbids it.
- Suggested defaults (FDM):
  - Internal fillets at rib roots and boss bases: 1.0-2.5 mm.
  - External corner fillets/chamfers for handling: 0.5-1.5 mm.
  - Lead-in chamfers for insertion features (shafts, bearings, screws):
    0.3-1.0 mm.

### 2.2 Cantilevered shaft/bearing misuse

Failure mode:
- Shaft is supported by one ball bearing with collars/spacers outboard,
  creating an unstable cantilever and large bending moments.

Guideline:
- Do not allow single-bearing shaft support unless explicitly justified by
  low load and very short overhang.
- Preferred support hierarchy:
  1. dual radial bearings with spacing,
  2. bearing + bushing with bounded overhang,
  3. single bearing only with strict span/load limits.
- Add a design rule: unsupported shaft overhang should stay below a specified
  ratio of shaft diameter (e.g., <= 1.0-1.5x) unless FEA or hand calc proves
  adequacy.

### 2.3 Thin walls and weak bosses

Failure mode:
- Wall or boss dimensions are set by aesthetic layout and not by screw preload,
  insertion force, or printer anisotropy.

Guideline:
- Set minimum wall thickness by material/process profile.
- Use boss rules:
  - boss OD >= 2x fastener major diameter (often 2.0-2.5x is safer),
  - generous fillet at boss root,
  - add ribs for tall bosses.

### 2.4 Assembly without serviceability

Failure mode:
- Parts can be assembled in CAD but not in real sequence (tool access blocked,
  no cable bend space, no finger access).

Guideline:
- Include service envelopes in model constraints:
  - screwdriver axis access volumes,
  - connector mating/unmating clearance,
  - cable bend radius and strain relief volume,
  - battery insertion/removal path.

## 3) Prompt Design Strategy for Robust Outputs

Use a staged prompt contract, not a single free-form prompt.

### Stage A: System intent (non-negotiables)

Include hard constraints such as:
- units in mm,
- interface-first modeling,
- mandatory edge treatment policy,
- shaft support policy,
- minimum wall/boss/rib rules,
- no unresolved collisions in final assembly,
- explicit assumptions list.

### Stage B: Task-specific requirement block

Provide:
- performance target (loads, acceleration, duty cycle),
- process/material (FDM/SLS/CNC + material),
- critical purchased parts,
- service constraints,
- mass/size limits.

### Stage C: Structured output schema

Require the LLM to emit:
1. interface table,
2. load-path summary,
3. deterministic feature calls (template usage),
4. open assumptions + risk flags,
5. generated CAD code.

## 4) Recommended Tooling Additions

### 4.1 Deterministic feature library

Add reusable constructors for:
- bearing blocks (single/dual support variants),
- shaft retention stacks,
- motor face mount patterns,
- standoff + screw boss patterns,
- cable routing clips/channels,
- ribbing patterns with auto-fillet roots.

### 4.2 Rule-based geometry linter

Implement a pre-export linter that checks:
- missing fillets on high-stress feature classes,
- min wall/rib/boss dimensions,
- fastener edge distances,
- unsupported spans/overhangs,
- bearing support topology for rotating shafts,
- assembly/service access volumes.

### 4.3 Semi-generative solver path

Adopt an "intent-to-geometry" pipeline:
1. LLM defines interfaces, envelopes, forbidden zones, and load cases.
2. Deterministic generator builds baseline topology.
3. Optional optimizer adjusts internal fill/ribs/webs for mass vs stiffness.
4. FEA-lite verification gates acceptance before final export.

This keeps critical geometry reliable while still leveraging LLM speed.

## 5) Practical Prompt Template (Robotics Part/Assembly)

Use the template below as a base system/developer prompt for CAD generation.

```text
You are generating production-minded robotics CAD in build123d Python.

Hard requirements:
- Use millimeters for all dimensions.
- Prioritize real component interfaces before aesthetics.
- Apply edge treatment defaults:
  - internal structural roots: fillet 1.0-2.5 mm,
  - external handling edges: fillet/chamfer 0.5-1.5 mm,
  - insertion lead-ins: chamfer 0.3-1.0 mm.
- Do not leave load-bearing sharp internal corners unless explicitly justified.
- Rotating shafts must not be unsupported cantilevers by default:
  - prefer dual-bearing support,
  - if single-bearing is used, enforce and report strict overhang/load limits.
- Enforce manufacturable minima for wall thickness, boss geometry, and ribbing
  using the provided process/material profile.
- Preserve assembly and serviceability:
  tool access, connector clearance, cable bend radius, replacement paths.
- Final assembly must report collision status and intentional clearances.

Output format (in this order):
1) Interface table (mount points, datums, holes, shaft fits, clearances).
2) Load-path and support summary (include shaft support rationale).
3) Deterministic feature plan (which reusable templates are used and why).
4) Assumptions + risk list (explicitly flag anything uncertain).
5) build123d code.

If any requirement conflicts, stop and report the conflict instead of guessing.
```

## 6) Validation Checklist (Pre-merge)

- Fillets/chamfers applied per policy or exceptions documented.
- No unjustified single-bearing cantilevered shafts.
- Wall/boss/rib minima verified for process/material.
- Fastener access and cable/service envelopes verified.
- Interference checks clean or intentionally documented.
- Project notes updated with assumptions and known limits.

## 7) Suggested Next Steps for SynthCAD

1. Add a `synthcad/cad/lint.py` module with geometry and topology checks.
2. Add deterministic constructors for common robotics joint patterns.
3. Extend project-local tests to assert support topology and min edge treatment.
4. Integrate lint + interference summary into CI review artifacts.
5. Evolve prompts to require structured rationale before code emission.
