# Flat Disk Workflow

## Targets

- `flat-disk-robot-chassis`
- `flat-disk-robot-lid`
- `flat-disk-robot`

## Source Files

- `synthcad/projects/flat_disk_robot/robot.py`
- `synthcad/projects/flat_disk_robot/urdf.py`
- `synthcad/build.py`
- `synthcad/external_parts.py`
- `projects/flat-disk-robot/docs/flat-disk-robot-notes.md`

## Source References

- `projects/flat-disk-robot/real-parts/repeat-drive-compact-1.snapshot.11/Repeat Compact 1806.STEP`
- `projects/flat-disk-robot/real-parts/as5600-magnetic-encoder-module-1.snapshot.5/AS5600_magnetic_encoder.step`
- `projects/flat-disk-robot/real-parts/seeed-studio-xiao-esp32s3-sense-1.snapshot.2/Seeed Studio XIAO-ESP32-S3-Sense.step`
- `projects/flat-disk-robot/real-parts/OV2640_21mm-160_camera.STEP`
- `projects/flat-disk-robot/real-parts/TOF-sensor-drawing.webp`
- `projects/flat-disk-robot/real-parts/battery.png`

## Project Tests

Project-specific tests belong under `projects/<project-slug>/tests/`, not root
`tests/`. Root tests are for shared SynthCAD tooling.

For each project, write tests that cover:

- geometry invariants for printable parts and assemblies;
- critical real-component interfaces such as holes, shafts, registers,
  clearances, service access, and mounting faces;
- expected assembly interferences and documented intentional overlaps;
- source reference and docs metadata resolving to checked-in project files; and
- target selection or project filtering when the project adds registry behavior.

The flat disk robot examples are:

- `projects/flat-disk-robot/tests/test_geometry_invariants.py`
- `projects/flat-disk-robot/tests/test_interference_invariants.py`

## Typical Loop

1. Probe the current target.

```bash
uv run synthcad-probe --target flat-disk-robot --children
```

2. Edit the parameterized CAD source.

3. Run focused tests.

```bash
uv run pytest projects/flat-disk-robot/tests tests/test_build_registry.py
```

4. Regenerate and inspect.

```bash
uv run synthcad-build --project flat-disk-robot
uv run synthcad-inspect --target flat-disk-robot
uv run show-interference --target flat-disk-robot
uv run synthcad-report --project flat-disk-robot
```

5. Update robot notes with changed assumptions, known interferences, or
   validation evidence.
