# Underground Mine Stationary Rock Breaker (Blender Python)

A procedural Blender 3D (`bpy` / `bmesh`) generator that builds a detailed **stationary pedestal rock breaker boom** mounted beside an **underground mine tip (grizzly bay)** with hierarchical joint rigging and auto-tracking hydraulic cylinders.

## Features

The script builds and organizes all geometry into six Outliner collections:

* **`01_Pedestal_Base`** — Chamfered concrete plinth, steel baseplate with 16 anchor bolts, gusseted pedestal drum, slewing ring bearing with 28 flange bolts, rotating turret cheeks, planetary slew drive, and rear hydraulic manifold block.
* **`02_Boom_Assembly`** — Smooth 13-station curved welded box-girder main boom with overhanging top/bottom flange plates, twin side-mounted lift cylinders, top-mounted dipper cylinder, dog-leg dipper head, tapered dipper arm, curl cylinder, and a live 2-bone IK 4-bar linkage.
* **`03_Hydraulic_Breaker`** — Box-silenced hydraulic hammer housing with twin mounting clevis cheeks, bolted top adapter plate, framed recessed side service slots, tool bushing, retainer pin, and forged moil point chisel seated on the target boulder.
* **`04_Hydraulic_Hoses`** — Continuous hydraulic routing from turret valve fittings through `HOOK`-constrained flexible manifold hoses, clamped steel boom hardlines, elbow jumper hoses, dipper hardlines, and flexible breaker feed hoses that stay locked to their fittings while posing.
* **`05_Mine_Tip_Grizzly`** — Seamless concrete tipping deck with recessed ore-pass shaft, 9 heavy I-beam grizzly bars, LHD wheel-stop curb, flanged hazard bollards with safety chains, and fractured oversize ore boulders seated cleanly atop the bars.
* **`06_Underground_Mine_Bay`** — Open-front cutaway shotcrete rock cavern arch, rear rock bulkhead, receding LHD haulage drift tunnel, steel ground-support ribs, staggered rock bolts, suspended yellow ventilation duct, mine air/water service pipes, overhead high-bay LED floodlights, and a skid-mounted Hydraulic Power Unit (HPU) with electrical control cabinet.

## Requirements

* **Blender 3.6+**, **Blender 4.x**, or **Blender 5.x** (no external add-ons required).

## Quick Start

### Option 1: Run Inside Blender (GUI)
1. Open Blender and switch to the **Scripting** workspace.
2. Click **Text → Open** and select `rock_breaker_generator.py`.
3. Click **Run Script** (▶).
4. Press **`Z` → Material Preview** (or **Rendered**) to view materials and lighting.
5. *(Optional)* Open **Viewport Overlays** (top-right of the 3D Viewport) and uncheck **Relationship Lines** to hide the dashed parenting lines.

### Option 2: Run from Command Line (Headless)
Generate a `.blend` file directly without opening the UI:

```bash
blender --background --python rock_breaker_generator.py --python-expr "import bpy; bpy.ops.wm.save_as_mainfile(filepath='underground_rockbreaker.blend')"
```

## Posing the Rig

All major joints are parented hierarchically, hydraulic cylinders use `DAMPED_TRACK` constraints so rods telescope inside their barrels automatically, the 4-bar breaker curl linkage is driven by a native 2-bone IK solver (`Linkage_4Bar_IK_Rig`), and flexible hoses use `HOOK` modifiers across every moving joint:

| Pivot Empty | Axis | Action |
| :--- | :---: | :--- |
| `Turret_Slew_Pivot` | `Z` | Slew boom horizontally across the grizzly |
| `Boom_Pivot` | `Y` | Raise or lower the main boom |
| `Dipper_Pivot` | `Y` | Extend or retract the dipper arm |
| `Breaker_Pivot` | `Y` | Angle the hydraulic hammer |

To isolate just the stationary rock breaker without the tipping bay or tunnel cavern, hide the `05_Mine_Tip_Grizzly` and/or `06_Underground_Mine_Bay` collections in the Outliner.

## Project Structure

```text
.
├── rock_breaker_generator.py   # Procedural Blender Python generator script
├── .gitignore                  # Blender backup and Python cache ignores
└── README.md                   # Documentation and usage instructions
```
