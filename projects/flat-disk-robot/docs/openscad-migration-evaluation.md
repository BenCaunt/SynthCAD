# OpenSCAD migration evaluation for Flat Disk Robot

## Executive summary

OpenSCAD is a credible alternative to Build123D for this project **if your priorities are deterministic text-based CAD, easy parameter sharing, and broad maker-tool interoperability**. The biggest tradeoff is that you lose Python's full ecosystem and object model as the primary modeling language.

For LLM-assisted workflows, OpenSCAD is often easier to synthesize at the **single-part CSG** level because it has a smaller language surface area and a direct constructive geometry style. Build123D remains stronger for large multi-file engineering systems where Python abstractions, testing, and integration with simulation pipelines are key.

## One-to-one prototype port

A first-pass one-to-one OpenSCAD version was created at:

- `projects/flat-disk-robot/openscad/flat_disk_robot.scad`

What was mapped directly from the current Build123D model:

- Disk chassis base and perimeter wall envelope.
- Front sensor opening + rear service opening.
- Wheel well cutouts and side symmetry pattern.
- Lid shell concept (top plate + side skirt).
- Lid mount bosses and M4 through-hole pattern.

What is intentionally not yet ported one-to-one:

- Imported detailed STEP-based electronics/motors/camera clearancing.
- Press-fit-specific details and tunneled service channels.
- Decorative and branded features (vents/logo text) and nuanced tolerancing.
- Full assembly tagging/material metadata currently embedded in Build123D flow.

## What you gain by switching

1. **Interoperability with OpenSCAD-centric tooling**
   - Native fit with OpenSCAD pipelines used by many makers, print farms, and scriptable STL generation workflows.
   - Easy handoff to users who expect `.scad` source as the canonical editable model.

2. **Very predictable textual geometry expression**
   - Core modeling is mostly `union/difference/intersection`, `translate/rotate`, and primitives.
   - Fewer conceptual layers can mean faster onboarding for contributors who do not want Python CAD APIs.

3. **Good match for LLM generation and repair loops**
   - Simpler syntax and less API ceremony typically produce fewer malformed-code failure modes.
   - LLMs can often patch features by editing small localized CSG blocks.

4. **Reproducible CLI rendering/export**
   - OpenSCAD command-line export flows are straightforward for CI artifact production.

## What you lose / risks

1. **Python-first engineering workflow**
   - You lose direct leverage of your existing Python abstractions, tests, data structures, and helper libraries.

2. **Assembly richness and metadata ergonomics**
   - Build123D + Python currently gives cleaner avenues for semantic tagging, richer composition, and cross-module reuse.

3. **Complex parametric maintainability can degrade**
   - OpenSCAD scales well for many projects, but very complex assemblies can become less navigable without strong modular discipline.

4. **Parity effort is non-trivial**
   - A true full-fidelity migration of `synthcad/projects/flat_disk_robot/robot.py` is substantial and should be phased.

## LLM usability answer (direct)

- **Will models like me use OpenSCAD better?**
  - For focused part geometry and edits: often yes.
  - For broader software-defined mechanical systems integrated with Python tooling/tests: Build123D can still be better.

- **Will compatibility with other CAD/software improve?**
  - For maker/open-source script CAD ecosystems: yes.
  - For professional MCAD exchange, the important boundary remains exported neutral formats (STEP/STL/3MF), which both pipelines can produce via toolchains.

## Recommended migration strategy

1. Keep Build123D as source of truth initially.
2. Maintain OpenSCAD parity only for the shell/chassis/lid envelope and mounting interfaces.
3. Add geometry-invariant checks on exported meshes/measurements to guard drift.
4. Decide after 2-3 iterations whether dual-maintenance overhead is acceptable.

## Suggested acceptance criteria for a real switch

- OpenSCAD version reproduces all manufacturing-critical interfaces within tolerance.
- CI exports STL/STEP artifacts and passes dimensional checks.
- At least one non-author contributor can successfully modify both chassis and lid features in OpenSCAD without hand-holding.
- Documentation clearly states canonical source (single-source vs dual-source policy).
