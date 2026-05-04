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
- `docs/flat-disk-robot-notes.md`

## Source References

- `real-parts/repeat-drive-compact-1.snapshot.11/Repeat Compact 1806.STEP`
- `real-parts/as5600-magnetic-encoder-module-1.snapshot.5/AS5600_magnetic_encoder.step`
- `real-parts/seeed-studio-xiao-esp32s3-sense-1.snapshot.2/Seeed Studio XIAO-ESP32-S3-Sense.step`
- `real-parts/OV2640_21mm-160_camera.STEP`
- `real-parts/TOF-sensor-drawing.webp`
- `real-parts/battery.png`

## Typical Loop

1. Probe the current target.

```bash
uv run synthcad-probe --target flat-disk-robot --children
```

2. Edit the parameterized CAD source.

3. Run focused tests.

```bash
uv run pytest tests/test_geometry_invariants.py tests/test_build_registry.py
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
