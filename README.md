# Underground Mine Stationary Rock Breaker (Blender Python)

A procedural Blender 3D (`bpy` / `bmesh`) generator that builds a detailed **stationary pedestal rock breaker boom** mounted beside an **underground mine tip (grizzly bay)** with hierarchical joint rigging and auto-tracking hydraulic cylinders.

## Features

The script builds and organizes all geometry into seven Outliner collections:

* **`01_Pedestal_Base`** — Chamfered concrete plinth, steel baseplate with 16 anchor bolts, gusseted pedestal drum, slewing ring bearing with 28 flange bolts, rotating turret cheeks, planetary slew drive, and rear hydraulic manifold block.
* **`02_Boom_Assembly`** — Smooth 13-station curved welded box-girder main boom with overhanging top/bottom flange plates, twin side-mounted lift cylinders, top-mounted dipper cylinder, dog-leg dipper head, tapered dipper arm, curl cylinder, and a live 2-bone IK 4-bar linkage.
* **`03_Hydraulic_Breaker`** — Box-silenced hydraulic hammer housing with twin mounting clevis cheeks, bolted top adapter plate, framed recessed side service slots, tool bushing, retainer pin, and forged moil point chisel seated on the target boulder.
* **`04_Hydraulic_Hoses`** — Continuous hydraulic routing from turret valve fittings through `HOOK`-constrained flexible manifold hoses, clamped steel boom hardlines, elbow jumper hoses, dipper hardlines, and flexible breaker feed hoses that stay locked to their fittings while posing.
* **`05_Mine_Tip_Grizzly`** — Seamless concrete tipping deck with recessed ore-pass shaft, heavy square-mesh grizzly with **`6 × 6 = 36` exact `600 × 600 mm` clear apertures** (`100 mm` I-beam bars on `700 mm` centers), LHD wheel-stop curb, flanged hazard bollards with safety chains, and Voronoi pre-fractured oversize ore boulders seated atop the bars.
* **`06_Underground_Mine_Bay`** — Open-front cutaway shotcrete rock cavern arch, rear rock bulkhead, receding LHD haulage drift tunnel, steel ground-support ribs, staggered rock bolts, suspended yellow ventilation duct, mine air/water service pipes, overhead high-bay LED floodlights, and a skid-mounted Hydraulic Power Unit (HPU) with electrical control cabinet.
* **`07_Rock_Breaking_FX`** — Animated flyrock chips, impact sparks, and soft volumetric-style fading rock-dust puffs triggered during hammering and boulder shattering.

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

## Rock-Breaking Physics & Sound FX (Frames 1–240 @ 24 fps)

Press **`Spacebar`** in Blender to play the built-in 10-second looping Bullet Rigid Body simulation with synchronized sound (`AUDIO_SYNC` enabled):

* **Bullet Rigid Body Physics**: All `600 × 600 mm` grizzly bars, frame, deck, and ore-pass walls are `PASSIVE` colliders; `Breaker_Moil_Chisel`, `Breaker_Tool_Chuck`, and `Breaker_Lower_Skirt` are animated kinematic `PASSIVE` colliders that physically wedge and drive into the rock; fractured ore shards (randomized per boulder — 5 to 11 uneven 3D Voronoi chunks clustered around the chisel impact zone; set `FRACTURE_SEED` for repeatability) and intact boulders are `ACTIVE` rigid bodies (`CONVEX_HULL`) that collide with the hammer chisel, bounce off the steel grizzly grid, and fall through the `600 × 600 mm` apertures into the ore pass (baked automatically into the point cache).
* **Frames 1–86**: Boom engages `Oversize_Boulder_Target`, fires a high-frequency hydraulic percussion burst, and shatters it at Frame 56.
* **Frames 87–180**: Boom lifts, slews smoothly to `Oversize_Boulder_2` via exact analytic IK (articulating all cylinders, the 4-bar linkage, and hooked hydraulic hoses), hammers it, and shatters it at Frame 156 across the `600 × 600 mm` grid.
* **Frames 181–240**: Boom retracts and slews back to the ready pose for seamless looping.
* **Real-World Sound FX (`sounds/*.wav`, VSE Channels 1–6)**: Uses real field recordings converted to 44.1 kHz PCM WAV (actual underground mine machinery & pneumatic rock-hammering from Trbovlje Hrastnik Mine via Wikimedia Commons, CC0 rock shattering & steel clatter from OpenGameArt, and CC0 falling stone cascade from BigSoundBank #1022 — see `sounds/CREDITS.txt`), packed into `underground_rockbreaker.blend`.

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
