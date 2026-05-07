// Flat Disk Robot prototype port to OpenSCAD.
// Goal: near one-to-one mapping of the high-level chassis + lid envelope from
// synthcad/projects/flat_disk_robot/robot.py (Build123D).

$fn = 128;

ROBOT_DIAMETER = 216;
ROBOT_RADIUS = ROBOT_DIAMETER / 2;
ROBOT_CHASSIS_THICKNESS = 5;
PERIMETER_WALL_THICKNESS = 3;
PERIMETER_WALL_HEIGHT = 18;

ROBOT_WHEEL_CENTER_X = 86.5;
ROBOT_AXLE_Y = -18;
WHEEL_RADIUS = 30; // keep overridable; build123d source derives this from library
ROBOT_WHEEL_GROUND_PROTRUSION = 4.5;
ROBOT_WHEEL_RADIUS = WHEEL_RADIUS + ROBOT_WHEEL_GROUND_PROTRUSION;
WHEEL_HUB_WIDTH = 26;
WHEEL_SLOT_CLEARANCE_X = 2;
WHEEL_SLOT_CLEARANCE_Y = 13;
WHEEL_SLOT_X = WHEEL_HUB_WIDTH + 2 * WHEEL_SLOT_CLEARANCE_X;
WHEEL_SLOT_Y = 2 * ROBOT_WHEEL_RADIUS + WHEEL_SLOT_CLEARANCE_Y;

FRONT_SENSOR_OPENING_DEPTH = 20.4;
FRONT_SENSOR_OPENING_WIDTH = 144;
REAR_SERVICE_OPENING_WIDTH = 62;

LID_MOUNT_POINTS = [
    [-58, -78], [58, -78], [-82, 24], [82, 24], [-68, 60], [68, 60]
];
M4_CLEARANCE_DIAMETER = 4.25;
LID_BOSS_RADIUS = 10;

LID_SHELL_WALL_THICKNESS = 3;
LID_TOP_UNDERSIDE_Z = 46.5;
LID_TOP_THICKNESS = 3;
LID_WALL_BOTTOM_Z = ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT;
LID_WALL_HEIGHT = LID_TOP_UNDERSIDE_Z - LID_WALL_BOTTOM_Z;

module chassis_shell() {
    union() {
        cylinder(h=ROBOT_CHASSIS_THICKNESS, r=ROBOT_RADIUS);
        translate([0,0,ROBOT_CHASSIS_THICKNESS])
            difference() {
                cylinder(h=PERIMETER_WALL_HEIGHT, r=ROBOT_RADIUS);
                translate([0,0,-0.01])
                    cylinder(h=PERIMETER_WALL_HEIGHT+0.02, r=ROBOT_RADIUS-PERIMETER_WALL_THICKNESS);
            }
    }
}

module front_sensor_opening() {
    y = ROBOT_RADIUS - PERIMETER_WALL_THICKNESS/2 - FRONT_SENSOR_OPENING_DEPTH/2;
    translate([0, y, ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT/2])
        cube([FRONT_SENSOR_OPENING_WIDTH, FRONT_SENSOR_OPENING_DEPTH, PERIMETER_WALL_HEIGHT + 2], center=true);
}

module rear_service_opening() {
    y = -ROBOT_RADIUS + PERIMETER_WALL_THICKNESS/2;
    translate([0, y, ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT/2])
        cube([REAR_SERVICE_OPENING_WIDTH, PERIMETER_WALL_THICKNESS + 2, PERIMETER_WALL_HEIGHT + 2], center=true);
}

module wheel_wells() {
    for (sx = [-1, 1])
        translate([sx * ROBOT_WHEEL_CENTER_X, ROBOT_AXLE_Y, ROBOT_CHASSIS_THICKNESS + ROBOT_WHEEL_RADIUS])
            cube([WHEEL_SLOT_X, WHEEL_SLOT_Y, 2*ROBOT_WHEEL_RADIUS + 2], center=true);
}

module lid_mount_holes(z0, z1) {
    for (p = LID_MOUNT_POINTS)
        translate([p[0], p[1], z0])
            cylinder(h=z1-z0, d=M4_CLEARANCE_DIAMETER);
}

module chassis() {
    difference() {
        chassis_shell();
        front_sensor_opening();
        rear_service_opening();
        wheel_wells();
        lid_mount_holes(-1, ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT + 2);
    }
}

module lid() {
    difference() {
        union() {
            // top plate
            translate([0,0,LID_TOP_UNDERSIDE_Z])
                cylinder(h=LID_TOP_THICKNESS, r=ROBOT_RADIUS);
            // side skirt
            translate([0,0,LID_WALL_BOTTOM_Z])
                difference() {
                    cylinder(h=LID_WALL_HEIGHT, r=ROBOT_RADIUS);
                    translate([0,0,-0.01])
                        cylinder(h=LID_WALL_HEIGHT+0.02, r=ROBOT_RADIUS-LID_SHELL_WALL_THICKNESS);
                }
            for (p = LID_MOUNT_POINTS)
                translate([p[0], p[1], LID_WALL_BOTTOM_Z])
                    cylinder(h=LID_WALL_HEIGHT, r=LID_BOSS_RADIUS);
        }
        lid_mount_holes(LID_WALL_BOTTOM_Z - 1, LID_TOP_UNDERSIDE_Z + LID_TOP_THICKNESS + 1);
    }
}

// Preview both separated in X for quick visual compare.
translate([-130,0,0]) chassis();
translate([130,0,0]) lid();
