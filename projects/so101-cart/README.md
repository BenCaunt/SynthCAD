# so101-cart

Boundary: `project`

A small two-wheeled cart that carries an SO-101 arm and docks to the back of
the flat disk robot via two N52 disc magnets recessed into the disk-robot lid.
The cart's front cradle wraps around the disk-robot's rear wall so the magnet
faces stay close to parallel and the disk robot can push or pull the cart on
its two passive wheels.

Source references live alongside the cart bundle:

- `real-parts/so-arm-101.snapshot/SO101_Assembly.step`: assembly STEP from
  TheRobotStudio's [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100)
  repository, used as a visual reference for arm placement on the deck.

Current targets:

- `so101-cart-deck`: printable cart body (cradle + deck + axle bosses + magnet
  pockets).
- `so101-cart-wheel`: printable cart wheel for the M5 idler axle.
- `so101-cart`: cart-only reference assembly (deck, two wheels, axle, two
  dock-side magnets, SO-101 arm).
- `flat-disk-robot-with-cart`: docked assembly that places the cart behind the
  flat disk robot to verify the magnetic dock interface.

The cart shares the disk-robot coordinate frame in the docked assembly: the
disk robot stays centered on the origin, and the cart sits behind it with its
cradle wrapping the rear arc.
