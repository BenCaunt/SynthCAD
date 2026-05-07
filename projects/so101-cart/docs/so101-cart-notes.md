# SO-101 Cart Notes

## Goal

Prototype a magnetic dock between the flat disk robot and a small two-wheeled
cart that carries a [SO-101 follower
arm](https://github.com/TheRobotStudio/SO-ARM100). The disk robot provides the
drive, sensing, and control; the cart is a passive trailer that lets the arm
move around without giving up any of the disk's chassis volume.

## Coordinate System

The cart shares the disk robot's coordinate frame in the docked assembly:

- Origin is the disk robot's center on the ground plane.
- +Y points forward (same as the disk robot).
- The cart's cradle wraps the disk-robot rear arc and extends backward in -Y.
- Z is vertical; wheels touch the ground at Z = 0.

## Magnetic Dock Interface

Two N52 12 x 5 mm disc magnets sit in the rear of the disk robot lid (one on
each side of the rear service opening). Both magnet bores are radial so each
magnet's outer pole face lies essentially flush with the curved outer surface
of the lid wall. Inward-facing bosses give the bores enough wall depth without
poking past the 216 mm lid envelope.

The cart's front cradle is a cylindrical segment that wraps the rear of the
disk robot with a 0.5 mm radial clearance. The cradle holds the matching cart
magnets in radial bores so the two pole faces stay parallel and within ~0.5 mm
of each other when docked.

## Cart Layout

- **Cradle:** annular segment, inner radius 108.5 mm, outer radius 116.5 mm,
  ±40° around the rear (-90°). Height matches the lid wall + roof.
- **Deck:** 180 x 260 x 8 mm flat plate, top surface coplanar with the disk
  robot lid roof so the SO-101 base sits at a known Z.
- **Cheek legs:** two vertical plates that hang from the deck and carry an M5
  axle at Z = 35 mm.
- **Wheels:** two passive 70 mm OD printed wheels with central M5 clearance
  bores, mounted outboard of the cheeks.
- **SO-101:** the imported assembly STEP from TheRobotStudio is placed on the
  deck centered laterally and forward of the wheel axle.

## Build Chain

Targets are produced by `synthcad.projects.so101_cart.cart` and exported
through `synthcad.build`:

- `so101-cart-deck` (printable)
- `so101-cart-wheel` (printable)
- `so101-cart` (cart-only reference assembly)
- `flat-disk-robot-with-cart` (docked reference assembly)

The lid magnet bosses are part of the existing `flat-disk-robot-lid`
printable; the lid no longer needs a separate build target for the dock.

## Source References

- `real-parts/so-arm-101.snapshot/SO101_Assembly.step` — TheRobotStudio's
  SO-101 follower assembly, downloaded from the
  [SO-ARM100 repo](https://github.com/TheRobotStudio/SO-ARM100/tree/main/STEP/SO101).
