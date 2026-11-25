# Case for the tree lights board

Two versions of a case for the ProtoMate for Pico board. Each has a base, a lid, and a small plunger that presses the Pico's BOOTSEL button through the lid. Both lids take the same tree inlay, `case-tree-inlay.stl`.

| Version | Files | Height | Board held by | Pico |
|---|---|---|---|---|
| Low-profile (pins) | `case-pins-*.stl`, `treelights_case_pins.py` | 24.6 mm | Drops onto four pins; posts under the lid clamp it | Plugged into 8.5 mm sockets |
| Screwed | `case-*.stl`, `treelights_case.py` | 28 mm | Four M2.5 screws into standoffs | Plugged into 8.5 mm sockets |

## Low-profile version

All heights are worked out from the stack settings at the top of `treelights_case_pins.py`: shoulder height, the Pico's gap above the board (2.5 soldered, about 11 socketed), and the tallest part on the board. Change one and the walls, USB opening, lid posts and plunger all follow.

- **Pins:** 2.45 mm on one diagonal (they locate the board) and 2.30 mm on the other (they allow for print error), on 4.5 mm shoulders 3 mm tall. The ProtoMate's holes are taken as 2.7 mm: measure yours and print a base to test the fit before the lid.
- **Lid posts:** hollow so they slip over the pin tips and press on the board's corners. If the lid won't close, raise `POST_GAP`.
- **Under the board:** 3 mm. Trim the pins under the board flush.
- **As built:** the Pico plugs into sockets (11 mm above the board), and its header pins stick out 2.5 mm above it. The lever terminal is 13 mm tall with its levers closed. The lid's underside is 22.6 mm up, and the whole case is 24.6 mm tall. These were measured from a photo, so check them with calipers if you can.
- **Lid lip:** notched over the terminal and at the USB end.

## Screwed version

| File | Print |
|---|---|
| `case-base.stl` | Floor down. No supports. |
| `case-lid.stl` | Top face down (as exported). No supports. |
| `case-plunger.stl` | Wide end down. No supports. |

Outside size: 89.2 × 61.4 × 28 mm. PLA or PETG, 0.2 mm layers, 3 walls, 20% infill.

## Before you print

Measure these and change them at the top of `treelights_case.py` if they're different, then run `python3 treelights_case.py` (needs `pip install manifold3d trimesh numpy`):

1. **BOOTSEL position.** This setting is an estimate. Measure from the Pico's USB end to the button centre (`BOOTSEL_FROM_TOP`, set to 12), and from the Pico's centre line (`BOOTSEL_FROM_CENTRE`, set to −4.5, negative is away from the proto area). It was −1 until the first print came out 3–4 mm off.
2. **Tallest part.** The lid's underside is 26 mm above the bottom of the case, about 17 mm above the board. Lay the 1000 µF capacitor on its side, or raise `WALL_TOP_Z`.
3. **Mounting holes.** These should be 78.0 × 50.15 mm apart. Check with a ruler.

If you're unsure, print the base first and check the board fits.

## Printing the base

A 0.6 mm chamfer round the bottom edge of both bases hides any first-layer squash ("elephant's foot"). Set `BOTTOM_CHAMFER = 0` in `treelights_case.py` to leave it out.

To stop the corners lifting (PLA on a Bambu Lab P1S with the Cool Plate SuperTack):

- Close the door and keep the top on.
- In the filament profile, under **Cooling**: no cooling for the first 3 layers, full fan from layer 5, auxiliary part cooling fan at 0%, and exhaust fan off during the print.
- Set the plate type to **Cool Plate SuperTack**, and leave the bed at that profile's temperature.
- Wash the plate with washing-up liquid and water. Don't use glue on it.
- If it still lifts, add a brim with **Brim-object gap: 0**.

## Tree inlay

The tree is cut right through the lid. A separate tree, `case-tree-inlay.stl`, pushes in from inside the lid. Print it in a contrasting colour, for example gold or cream in a green lid.

- Print the lid and the inlay face down, as the STLs are oriented. Both faces then print against the plate and come out smooth, with nothing bridged.
- The front 1.2 mm of the inlay is straight. Behind that, it widens at 45° by 0.8 mm, so it can't push out through the front. It sits flush on both sides.
- The gap is 0.12 mm each side (`INLAY_FIT`). If it's too tight, raise it to 0.15–0.2. If it's loose, add a dab of superglue from the inside.

### Multi-colour inlay

![Inlay colours](inlay/preview.svg)

`inlay/` has the same inlay split into five colours: the tree, the star, and three sets of six baubles. Open `inlay/tree-inlay-colours.3mf` in Bambu Studio. It's a Bambu project made by Bambu Studio itself: one object called "Tree inlay", with parts named Tree, Star, Baubles A, B and C, each on its own filament slot (1–5), set up for a P1S with PLA. The slot colours are placeholders: set them to match your AMS. Or select all five `inlay-*.stl` files, choose **Yes** when it asks to load them as one object with several parts, and give each part a filament yourself.

`python3 treelights_case.py` rebuilds the 3MF through Bambu Studio's command line, if it's installed in /Applications.

- The star and baubles are only 0.6 mm deep, which is three 0.2 mm layers at the face. Filament only changes for those three layers; the rest prints in the tree colour.
- A 4-slot AMS can do four colours. For five, use the same filament for two parts, for example gold for both the star and one set of baubles. Or add a pause for a manual change.
- The baubles are the ones from the web app's tree picture. Some are nudged inward to stay off the edges, and five that hang off the tiers in the app are left out. Change `BAUBLE_D`, `BAUBLE_COLOURS` (up to 5) or `COLOUR_DEPTH` in `treelights_case.py` and rebuild.
- The star is bigger than in the app (about 6 mm across) so its points print.

## Features

- Four 5 mm standoffs with 2.2 mm pilot holes for M2.5 thread-forming screws (about 6 mm long). For brass heat-set inserts, set `SCREW_HOLE_D = 3.6`.
- 5 mm of room under the board for solder joints.
- USB opening in the back wall for the micro-USB plug and its moulding. It's open at the top, and the lid closes it.
- 10 × 6 mm slot in the front wall, in line with the terminal and centred on its wire openings (7 mm above the board, `WIRE_Z`).
- Push-fit lid with a lip (0.25 mm clearance; change `LID_FIT` if it's too tight or loose).
- The app's tree cut through the lid, star towards the cable edge, filled with a separate inlay.
- Two keyholes for hanging on screws 50 mm apart, with the cable edge at the top.

## Assembly

1. Thread the pigtail through the front slot from outside, then put a cable tie round it inside the case as strain relief.
2. Screw the board onto the standoffs and push the wires into the terminal.
3. Fit the Pico in its sockets and plug in the USB cable.
4. Drop the plunger in from below the lid, shaft up, and push the lid on.
