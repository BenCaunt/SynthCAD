# M3564C Load Cell Notes

Source reference: `projects/m3564c-load-cell/real-parts/m3564c-drawing.pdf`.

The source drawing is titled `Pro/ENGINEER - M3564C`, dated December 11, 2020,
and specifies dimensions in millimeters.

## Drawing-Derived Dimensions

- Part: Sunrise Instruments M3564C six-axis circular load cell, extra thin,
  D60 mm, F2000N.
- Outer body diameter: 60.00 mm.
- Outer ring thickness: 12.00 +/- 0.01 mm.
- Inner ring face offset: 0.5 mm above the outer ring on the tool side and
  0.5 mm below the outer ring on the robot side.
- Center bore: 7.00 mm through.
- Tool-side through holes: 6 x 5.20 mm on a 24.00 mm bolt circle, 60 degree
  equal spacing.
- Tool-side dowel pockets: 3 x 3.01 +0.01/-0 mm, 3 mm deep, on a 28.00 mm
  bolt circle, 120 degree equal spacing.
- Robot-side threaded pattern: 2 x M5 through holes on a 55.00 mm bolt circle,
  70 degree spacing, repeated 3 times at 120 degree spacing.
- Robot-side dowel pockets: 3 x 3.01 +0.01/-0 mm, 3 mm deep, on a 55.00 mm
  bolt circle, 120 degree equal spacing.
- Cable: 4 m cable, shown exiting from the side of the load cell.

## Modeling Assumptions

- The drawing does not dimension the internal flexure relief outline, cable
  gland radii, engraving depth, or thread minor diameter. The model therefore
  treats those as review/detail approximations and keeps the dimensioned bolt
  circles, hole diameters, face offsets, and main envelope as the controlled
  interfaces.
- M5 threaded holes are represented by simple 4.2 mm through cylinders, matching
  a common M5 tap-drill/minor-diameter approximation. Thread geometry is
  intentionally omitted because SynthCAD reference parts use simple
  mounting-interface solids instead of helical thread detail.
- The inner raised land is modeled as 35.0 mm diameter based on the drawing
  view proportions and the nearby 35.00 mm callout. This is the only primary
  envelope dimension not explicitly tied to a diameter symbol in the visible
  drawing.
- The long cable is represented by a short direction stub so generated review
  artifacts remain compact.
