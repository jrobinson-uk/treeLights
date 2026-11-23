# Case for the tree lights board

Two versions of a case for the ProtoMate for Pico board. Each has a base, a lid, and a small plunger that presses the Pico's BOOTSEL button through the lid.

| Version | Files | Height | Board held by | Pico |
|---|---|---|---|---|
| Low-profile (pins) | `case-pins-*.stl`, `treelights_case_pins.py` | 19.6 mm | Drops onto four pins; posts under the lid clamp it | Soldered on its header pins |
| Screwed | `case-*.stl`, `treelights_case.py` | 28 mm | Four M2.5 screws into standoffs | Plugged into 8.5 mm sockets |

## Low-profile version

All heights are worked out from the stack settings at the top of `treelights_case_pins.py`: shoulder height, the Pico's gap above the board (2.5 soldered, about 11 socketed), and the tallest part on the board. Change one and the walls, USB opening, lid posts and plunger all follow.

- **Pins:** 2.45 mm on one diagonal (they locate the board) and 2.30 mm on the other (they allow for print error), on 4.5 mm shoulders 3 mm tall. The ProtoMate's holes are taken as 2.7 mm: measure yours and print a base to test the fit before the lid.
- **Lid posts:** hollow so they slip over the pin tips and press on the board's corners. If the lid won't close, raise `POST_GAP`.
- **Under the board:** 3 mm. Trim the pins under the board flush.
- **Tallest part:** set to 10 mm above the board, for the spring terminal or the 1000 µF capacitor lying flat. Measure yours.

## Screwed version

| File | Print |
|---|---|
| `case-base.stl` | Floor down. No supports. |
| `case-lid.stl` | Top face down (as exported). No supports. |
| `case-plunger.stl` | Wide end down. No supports. |

Outside size: 89.2 × 61.4 × 28 mm. PLA or PETG, 0.2 mm layers, 3 walls, 20% infill.

## Before you print

Measure these and change them at the top of `treelights_case.py` if they're different, then run `python3 treelights_case.py` (needs `pip install manifold3d trimesh numpy`):

1. **BOOTSEL position.** This setting is an estimate. Measure from the Pico's USB end to the button centre (`BOOTSEL_FROM_TOP`, set to 12), and from the Pico's centre line (`BOOTSEL_FROM_CENTRE`, set to −1, negative is away from the proto area).
2. **Tallest part.** The lid's underside is 26 mm above the bottom of the case, about 17 mm above the board. Lay the 1000 µF capacitor on its side, or raise `WALL_TOP_Z`.
3. **Mounting holes.** These should be 78.0 × 50.15 mm apart. Check with a ruler.

If you're unsure, print the base first and check the board fits.

## Features

- Four 5 mm standoffs with 2.2 mm pilot holes for M2.5 thread-forming screws (about 6 mm long). For brass heat-set inserts, set `SCREW_HOLE_D = 3.6`.
- 5 mm of room under the board for solder joints.
- USB opening in the back wall for the micro-USB plug and its moulding. It's open at the top, and the lid closes it.
- 7 × 5 mm slot in the front wall, in line with the spring terminal, for the lights pigtail.
- Push-fit lid with a lip (0.25 mm clearance; change `LID_FIT` if it's too tight or loose).
- The app's tree engraved in the lid, star towards the cable edge.
- Two keyholes for hanging on screws 50 mm apart, with the cable edge at the top.

## Assembly

1. Thread the pigtail through the front slot from outside, then put a cable tie round it inside the case as strain relief.
2. Screw the board onto the standoffs and push the wires into the terminal.
3. Fit the Pico in its sockets and plug in the USB cable.
4. Drop the plunger in from below the lid, shaft up, and push the lid on.
