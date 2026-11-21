# Underground Mine Stationary Rock Breaker (Blender Python)

A procedural Blender 3D (`bpy` / `bmesh`) generator that builds a detailed **stationary pedestal rock breaker boom** mounted beside an **underground mine tip (grizzly bay)** with hierarchical joint rigging and auto-tracking hydraulic cylinders.

## Features

The script builds and organizes all geometry into five Outliner collections:

* **`01_Pedestal_Base`** — Chamfered concrete plinth, steel baseplate with 16 anchor bolts, gusseted pedestal drum, slewing ring bearing with 28 flange bolts, rotating turret cheeks, and rear hydraulic manifold block.
* **`02_Boom_Assembly`** — Curved welded box-girder main boom with overhanging top/bottom flange plates, twin side-mounted lift cylinders, top-mounted dipper cylinder, dog-leg dipper head, tapered dipper arm, curl cylinder, and 4-bar linkage.
* **`03_Hydraulic_Breaker`** — Box-silenced hydraulic hammer housing with twin mounting clevis cheeks, bolted top adapter plate, recessed side service slots, tool bushing, retainer pin, and forged moil point chisel.
* **`04_Hydraulic_Hoses`** — Smooth 3D NURBS hydraulic lines looping from the turret valve block, clamped along the boom spine, arching over the elbow, and hanging into the breaker ports.
* **`05_Mine_Tip_Grizzly`** — Concrete tipping deck framing a recessed ore-pass shaft, 9 heavy I-beam grizzly bars, LHD wheel-stop curb, safety bollards, and angular oversize ore boulders.

## Requirements

* **Blender 3.6+** or **Blender 4.x** (no external add-ons required).

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

All major joints are parented hierarchically, and hydraulic cylinders use `DAMPED_TRACK` constraints so rods telescope inside their barrels automatically:

| Pivot Empty | Axis | Action |
| :--- | :---: | :--- |
| `Turret_Slew_Pivot` | `Z` | Slew boom horizontally across the grizzly |
| `Boom_Pivot` | `Y` | Raise or lower the main boom |
| `Dipper_Pivot` | `Y` | Extend or retract the dipper arm |
| `Breaker_Pivot` | `Y` | Angle the hydraulic hammer |

To isolate just the stationary rock breaker without the tipping bay, hide the `05_Mine_Tip_Grizzly` collection in the Outliner.

## Project Structure

```text
.
├── rock_breaker_generator.py   # Procedural Blender Python generator script
├── .gitignore                  # Blender backup and Python cache ignores
└── README.md                   # Documentation and usage instructions
```
