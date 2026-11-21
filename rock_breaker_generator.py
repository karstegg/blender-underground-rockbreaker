import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

# ==============================================================================
# 1. SCENE RESET & COLLECTIONS
# ==============================================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)

def make_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

col_base    = make_collection("01_Pedestal_Base")
col_boom    = make_collection("02_Boom_Assembly")
col_breaker = make_collection("03_Hydraulic_Breaker")
col_hoses   = make_collection("04_Hydraulic_Hoses")
col_mine    = make_collection("05_Mine_Tip_Grizzly")

# ==============================================================================
# 2. MATERIALS (Blender 3.x & 4.x Compatible)
# ==============================================================================
def create_mat(name, color, metallic=0.0, roughness=0.5, coat=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if coat > 0.0 and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    return mat

mat_red      = create_mat("Rockbreaker_Red",   (0.76, 0.035, 0.025), metallic=0.25, roughness=0.30, coat=0.25)
mat_dark     = create_mat("Dark_Steel",        (0.06, 0.065, 0.072), metallic=0.78, roughness=0.40)
mat_machined = create_mat("Machined_Steel",    (0.45, 0.47,  0.50),  metallic=0.92, roughness=0.26)
mat_chrome   = create_mat("Hydraulic_Chrome",  (0.88, 0.90,  0.93),  metallic=1.00, roughness=0.07)
mat_hose     = create_mat("Hydraulic_Rubber",  (0.02, 0.02,  0.024), metallic=0.02, roughness=0.78)
mat_concrete = create_mat("Mine_Concrete",     (0.22, 0.215, 0.205), metallic=0.00, roughness=0.90)
mat_yellow   = create_mat("Safety_Yellow",     (0.85, 0.56,  0.02),  metallic=0.15, roughness=0.38)
mat_ore      = create_mat("Oversize_Ore_Rock", (0.14, 0.125, 0.115), metallic=0.08, roughness=0.92)
mat_void     = create_mat("Ore_Pass_Void",     (0.008, 0.008, 0.01), metallic=0.00, roughness=1.00)

# ==============================================================================
# 3. GEOMETRY & RIGGING HELPERS
# ==============================================================================
def link_obj(obj, col, mat=None, parent=None, bevel=0.0, segments=2):
    col.objects.link(obj)
    if mat and obj.type in {'MESH', 'CURVE'}:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    if bevel > 0.0 and obj.type == 'MESH':
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(32)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj

def make_empty(name, loc, col, parent=None, size=0.25):
    emp = bpy.data.objects.new(name, None)
    emp.location = Vector(loc)
    emp.empty_display_type = 'PLAIN_AXES'
    emp.empty_display_size = size
    obj = link_obj(emp, col, parent=parent)
    bpy.context.view_layer.update()  # Ensure world matrix is evaluated before children attach
    return obj

def make_box(name, loc, dims, col, rot=(0, 0, 0), mat=None, parent=None, bevel=0.012):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(dims), verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    obj.rotation_euler = rot
    return link_obj(obj, col, mat=mat, parent=parent, bevel=bevel)

def make_cyl(name, loc, radius, depth, col, rot=(0, 0, 0), verts=28, mat=None, parent=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=verts,
        radius1=radius, radius2=radius, depth=depth
    )
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        if abs(p.normal.z) < 0.7:
            p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    obj.rotation_euler = rot
    return link_obj(obj, col, mat=mat, parent=parent, bevel=bevel)

def make_xz_plate(name, pts_xz, y_center, thickness, col, mat=None, parent=None, bevel=0.01):
    bm = bmesh.new()
    v_back  = [bm.verts.new((x, y_center - thickness * 0.5, z)) for (x, z) in pts_xz]
    v_front = [bm.verts.new((x, y_center + thickness * 0.5, z)) for (x, z) in pts_xz]
    bm.faces.new(v_back)
    bm.faces.new(list(reversed(v_front)))
    n = len(pts_xz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([v_back[i], v_back[j], v_front[j], v_front[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj, col, mat=mat, parent=parent, bevel=bevel)

def make_box_girder(name, stations, col, mat=None, parent=None, flange_extra_w=0.055, flange_t=0.036):
    def build_loft(part_name, ring_fn, bevel_w):
        bm = bmesh.new()
        rings = []
        n = len(stations)
        for i, (x, z, h, w) in enumerate(stations):
            p = Vector((x, 0.0, z))
            if i == 0:
                t = Vector((stations[1][0] - x, 0.0, stations[1][1] - z)).normalized()
            elif i == n - 1:
                t = Vector((x - stations[i-1][0], 0.0, z - stations[i-1][1])).normalized()
            else:
                t1 = Vector((x - stations[i-1][0], 0.0, z - stations[i-1][1])).normalized()
                t2 = Vector((stations[i+1][0] - x, 0.0, stations[i+1][1] - z)).normalized()
                t = (t1 + t2).normalized()
            up = Vector((-t.z, 0.0, t.x)).normalized()
            pts = ring_fn(p, up, h, w)
            rings.append([bm.verts.new(pt) for pt in pts])

        for i in range(n - 1):
            r1, r2 = rings[i], rings[i + 1]
            for k in range(4):
                kn = (k + 1) % 4
                bm.faces.new([r1[k], r1[kn], r2[kn], r2[k]])
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new(part_name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(part_name, mesh)
        return link_obj(obj, col, mat=mat, parent=parent, bevel=bevel_w)

    web = build_loft(
        f"{name}_Web",
        lambda p, up, h, w: [
            p + up * (h * 0.5) + Vector((0,  w * 0.5, 0)),
            p + up * (h * 0.5) + Vector((0, -w * 0.5, 0)),
            p - up * (h * 0.5) + Vector((0, -w * 0.5, 0)),
            p - up * (h * 0.5) + Vector((0,  w * 0.5, 0)),
        ],
        bevel_w=0.012
    )
    build_loft(
        f"{name}_TopFlange",
        lambda p, up, h, w: [
            p + up * (h * 0.5 + flange_t) + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 + flange_t) + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 - 0.005)    + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 - 0.005)    + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
        ],
        bevel_w=0.008
    )
    build_loft(
        f"{name}_BotFlange",
        lambda p, up, h, w: [
            p - up * (h * 0.5 - 0.005)    + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 - 0.005)    + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 + flange_t) + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 + flange_t) + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
        ],
        bevel_w=0.008
    )
    return web

def make_pin_boss(name, pos, width, boss_r, pin_r, col, parent=None):
    rot_y = (math.radians(90), 0.0, 0.0)
    make_cyl(f"{name}_Boss", pos, boss_r, width, col, rot=rot_y, mat=mat_red, parent=parent, bevel=0.008)
    make_cyl(f"{name}_Pin",  pos, pin_r,  width + 0.09, col, rot=rot_y, mat=mat_machined, parent=parent, bevel=0.005)
    for s in (-1, 1):
        cap_pos = Vector(pos) + Vector((0, s * (width * 0.5 + 0.055), 0))
        make_cyl(f"{name}_Cap_{s}", cap_pos, pin_r * 0.55, 0.025, col, rot=rot_y, verts=6, mat=mat_dark, parent=parent)

def make_link_bar(name, p1, p2, y_offset, width_h, thick_y, col, mat=mat_red, parent=None):
    p1 = Vector((p1[0], y_offset, p1[2]))
    p2 = Vector((p2[0], y_offset, p2[2]))
    mid = (p1 + p2) * 0.5
    dv = p2 - p1
    length = dv.length
    angle_y = -math.atan2(dv.z, dv.x)
    make_box(f"{name}_Bar", mid, (length, thick_y, width_h), col, rot=(0, angle_y, 0), mat=mat, parent=parent, bevel=0.01)
    rot_y = (math.radians(90), 0.0, 0.0)
    make_cyl(f"{name}_Eye1", p1, width_h * 0.58, thick_y + 0.015, col, rot=rot_y, mat=mat, parent=parent, bevel=0.006)
    make_cyl(f"{name}_Eye2", p2, width_h * 0.58, thick_y + 0.015, col, rot=rot_y, mat=mat, parent=parent, bevel=0.006)

def make_hydraulic_cylinder(name, p_base, p_rod, barrel_r, rod_r, col, base_parent, rod_parent, barrel_ratio=0.56):
    p_base = Vector(p_base)
    p_rod  = Vector(p_rod)
    dv = p_rod - p_base
    dist = dv.length
    quat = dv.normalized().to_track_quat('Z', 'X')

    emp_base = make_empty(f"{name}_BaseTarget", p_base, col, parent=base_parent, size=0.08)
    emp_rod  = make_empty(f"{name}_RodTarget",  p_rod,  col, parent=rod_parent,  size=0.08)

    barrel_len = dist * barrel_ratio
    rod_len    = dist * 0.78

    # Barrel mesh (origin at p_base, extends along +Z)
    bm_b = bmesh.new()
    m_eye = Matrix.Rotation(math.radians(90), 4, 'X')
    bmesh.ops.create_cone(bm_b, cap_ends=True, segments=24, radius1=barrel_r * 0.92, radius2=barrel_r * 0.92, depth=barrel_r * 1.45, matrix=m_eye)
    bmesh.ops.create_cone(
        bm_b, cap_ends=True, segments=28, radius1=barrel_r, radius2=barrel_r, depth=barrel_len,
        matrix=Matrix.Translation((0, 0, barrel_r * 0.7 + barrel_len * 0.5))
    )
    bmesh.ops.create_cone(
        bm_b, cap_ends=True, segments=28, radius1=barrel_r * 1.14, radius2=barrel_r * 1.14, depth=0.11,
        matrix=Matrix.Translation((0, 0, barrel_r * 0.7 + barrel_len - 0.02))
    )
    for z_port in (barrel_r * 0.7 + 0.14, barrel_r * 0.7 + barrel_len - 0.16):
        bmesh.ops.create_cube(
            bm_b, size=1.0,
            matrix=Matrix.Translation((barrel_r * 1.05, 0, z_port)) @ Matrix.Diagonal((0.06, 0.06, 0.07, 1.0))
        )
    mesh_b = bpy.data.meshes.new(f"{name}_Barrel")
    bm_b.to_mesh(mesh_b)
    bm_b.free()
    for p in mesh_b.polygons:
        p.use_smooth = True
    obj_barrel = bpy.data.objects.new(f"{name}_Barrel", mesh_b)
    obj_barrel.location = p_base
    obj_barrel.rotation_euler = quat.to_euler()
    link_obj(obj_barrel, col, mat=mat_dark, parent=base_parent)

    c_b = obj_barrel.constraints.new('DAMPED_TRACK')
    c_b.target = emp_rod
    c_b.track_axis = 'TRACK_Z'

    # Chrome piston rod mesh (origin at p_rod, extends along -Z)
    bm_r = bmesh.new()
    bmesh.ops.create_cone(bm_r, cap_ends=True, segments=24, radius1=rod_r * 1.65, radius2=rod_r * 1.65, depth=barrel_r * 1.35, matrix=m_eye)
    bmesh.ops.create_cone(
        bm_r, cap_ends=True, segments=24, radius1=rod_r, radius2=rod_r, depth=rod_len,
        matrix=Matrix.Translation((0, 0, -(rod_r * 1.2 + rod_len * 0.5)))
    )
    mesh_r = bpy.data.meshes.new(f"{name}_Rod")
    bm_r.to_mesh(mesh_r)
    bm_r.free()
    for p in mesh_r.polygons:
        p.use_smooth = True
    obj_rod = bpy.data.objects.new(f"{name}_Rod", mesh_r)
    obj_rod.location = p_rod
    obj_rod.rotation_euler = quat.to_euler()
    link_obj(obj_rod, col, mat=mat_chrome, parent=rod_parent)

    c_r = obj_rod.constraints.new('DAMPED_TRACK')
    c_r.target = emp_base
    c_r.track_axis = 'TRACK_NEGATIVE_Z'

    return obj_barrel, obj_rod

def make_hose(name, points, radius, col, mat=mat_hose, parent=None):
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.resolution_u = 16
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(points) - 1)
    for i, pt in enumerate(points):
        spline.points[i].co = (pt[0], pt[1], pt[2], 1.0)
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(points))
    obj = bpy.data.objects.new(name, curve_data)
    return link_obj(obj, col, mat=mat, parent=parent)

# ==============================================================================
# 4. MASTER KINEMATIC COORDINATES (Meters, XZ Centerline Plane)
# ==============================================================================
Z_PLINTH_TOP      = 0.80
P_TURRET_CENTER   = Vector((0.00, 0.00, 1.48))
P_BOOM_BASE       = Vector((0.05, 0.00, 2.15))
P_LIFT_BASE_X     = 0.52
P_LIFT_BASE_Z     = 1.62
P_LIFT_BOOM_X     = 1.42
P_LIFT_BOOM_Z     = 3.72
P_DIPPER_CYL_BASE = Vector((1.88, 0.00, 4.64))
P_DIPPER_PIVOT    = Vector((4.55, 0.00, 4.85))
P_DIPPER_CYL_ROD  = Vector((4.18, 0.00, 5.48))
P_CURL_CYL_BASE   = Vector((4.86, 0.00, 5.22))
P_LINK_BASE       = Vector((6.66, 0.00, 3.60))
P_LINK_APEX       = Vector((7.26, 0.00, 4.04))
P_BREAKER_PIVOT   = Vector((7.15, 0.00, 3.20))
P_BREAKER_LINK    = Vector((7.65, 0.00, 3.32))

# ==============================================================================
# 5. COLLECTION 01: STATIONARY PEDESTAL BASE & SLEW TURRET
# ==============================================================================
root_station = make_empty("Stationary_Rockbreaker_Root", (0, 0, 0), col_base, size=0.45)

make_box("Pedestal_Concrete_Plinth", (0, 0, Z_PLINTH_TOP * 0.5), (1.85, 1.85, Z_PLINTH_TOP), col_base, mat=mat_concrete, parent=root_station, bevel=0.05)

make_cyl("Base_Anchor_Plate", (0, 0, Z_PLINTH_TOP + 0.045), 0.72, 0.09, col_base, verts=36, mat=mat_dark, parent=root_station, bevel=0.008)
for i in range(16):
    ang = (2 * math.pi * i) / 16
    bx, by = 0.63 * math.cos(ang), 0.63 * math.sin(ang)
    make_cyl(f"Anchor_Bolt_{i+1}", (bx, by, Z_PLINTH_TOP + 0.115), 0.024, 0.06, col_base, verts=6, mat=mat_machined, parent=root_station)

make_cyl("Pedestal_Lower_Drum", (0, 0, Z_PLINTH_TOP + 0.27), 0.50, 0.42, col_base, verts=36, mat=mat_red, parent=root_station, bevel=0.01)
for i in range(8):
    ang = (2 * math.pi * i) / 8
    gx, gy = 0.54 * math.cos(ang), 0.54 * math.sin(ang)
    make_box(f"Pedestal_Gusset_{i+1}", (gx, gy, Z_PLINTH_TOP + 0.22), (0.18, 0.045, 0.28), col_base, rot=(0, 0, ang), mat=mat_red, parent=root_station, bevel=0.006)

make_cyl("Slew_Bearing_Inner", (0, 0, 1.33), 0.57, 0.14, col_base, verts=48, mat=mat_dark, parent=root_station, bevel=0.006)
make_cyl("Slew_Bearing_Flange_Bot", (0, 0, 1.25), 0.61, 0.04, col_base, verts=48, mat=mat_machined, parent=root_station)
make_cyl("Slew_Bearing_Flange_Top", (0, 0, 1.41), 0.61, 0.04, col_base, verts=48, mat=mat_machined, parent=root_station)
for i in range(28):
    ang = (2 * math.pi * i) / 28
    bx, by = 0.56 * math.cos(ang), 0.56 * math.sin(ang)
    make_cyl(f"Slew_Bolt_{i+1}", (bx, by, 1.44), 0.016, 0.035, col_base, verts=6, mat=mat_machined, parent=root_station)

turret_pivot = make_empty("Turret_Slew_Pivot", P_TURRET_CENTER, col_base, parent=root_station, size=0.40)

make_cyl("Turret_Deck", (0, 0, 1.50), 0.60, 0.14, col_base, verts=36, mat=mat_red, parent=turret_pivot, bevel=0.012)

turret_cheek_pts = [
    (-0.52, 1.54),
    ( 0.64, 1.54),
    ( 0.64, 1.78),
    ( 0.24, 2.34),
    (-0.22, 2.34),
    (-0.52, 1.88),
]
for side, y_pos in [("L", 0.26), ("R", -0.26)]:
    make_xz_plate(f"Turret_Cheek_{side}", turret_cheek_pts, y_pos, 0.08, col_base, mat=mat_red, parent=turret_pivot, bevel=0.01)

make_box("Turret_Rear_Box", (-0.36, 0.0, 1.82), (0.34, 0.44, 0.50), col_base, mat=mat_red, parent=turret_pivot, bevel=0.01)
make_box("Turret_Manifold_Tray", (-0.64, 0.0, 1.84), (0.32, 0.56, 0.05), col_base, mat=mat_red, parent=turret_pivot, bevel=0.006)
make_box("Hydraulic_Valve_Block", (-0.62, 0.0, 1.98), (0.22, 0.36, 0.22), col_base, mat=mat_dark, parent=turret_pivot, bevel=0.008)
make_cyl("Slew_Motor_Housing", (-0.38, 0.28, 1.72), 0.11, 0.34, col_base, mat=mat_dark, parent=turret_pivot, bevel=0.008)

make_pin_boss("Boom_Base", P_BOOM_BASE, 0.60, 0.14, 0.068, col_base, parent=turret_pivot)
make_pin_boss("Lift_Cyl_Base_Pin", (P_LIFT_BASE_X, 0.0, P_LIFT_BASE_Z), 0.88, 0.10, 0.052, col_base, parent=turret_pivot)

# ==============================================================================
# 6. COLLECTION 02: ARCHED MAIN BOOM, DIPPER ARM & HYDRAULIC CYLINDERS
# ==============================================================================
boom_pivot = make_empty("Boom_Pivot", P_BOOM_BASE, col_boom, parent=turret_pivot, size=0.35)

boom_stations = [
    (0.05, 2.15, 0.44, 0.40),
    (0.50, 2.78, 0.50, 0.40),
    (0.98, 3.44, 0.58, 0.40),
    (1.48, 3.96, 0.64, 0.38),
    (2.05, 4.24, 0.60, 0.38),
    (2.85, 4.46, 0.54, 0.36),
    (3.72, 4.67, 0.46, 0.34),
    (4.55, 4.85, 0.36, 0.32),
]
make_box_girder("Main_Boom", boom_stations, col_boom, mat=mat_red, parent=boom_pivot)

make_pin_boss("Lift_Cyl_Boom_Pin", (P_LIFT_BOOM_X, 0.0, P_LIFT_BOOM_Z), 0.84, 0.11, 0.052, col_boom, parent=boom_pivot)

dipper_cyl_lug_pts = [
    (1.52, 4.24),
    (2.26, 4.40),
    (2.05, 4.78),
    (1.74, 4.78),
]
for side, y_pos in [("L", 0.14), ("R", -0.14)]:
    make_xz_plate(f"Dipper_Cyl_Bracket_{side}", dipper_cyl_lug_pts, y_pos, 0.055, col_boom, mat=mat_red, parent=boom_pivot, bevel=0.008)
make_pin_boss("Dipper_Cyl_Base", P_DIPPER_CYL_BASE, 0.36, 0.095, 0.048, col_boom, parent=boom_pivot)

for side, y_cyl in [("L", 0.34), ("R", -0.34)]:
    make_hydraulic_cylinder(
        f"Lift_Cylinder_{side}",
        (P_LIFT_BASE_X, y_cyl, P_LIFT_BASE_Z),
        (P_LIFT_BOOM_X, y_cyl, P_LIFT_BOOM_Z),
        barrel_r=0.095, rod_r=0.055,
        col=col_boom, base_parent=turret_pivot, rod_parent=boom_pivot, barrel_ratio=0.55
    )

dipper_pivot = make_empty("Dipper_Pivot", P_DIPPER_PIVOT, col_boom, parent=boom_pivot, size=0.35)
make_pin_boss("Dipper_Main_Pivot", P_DIPPER_PIVOT, 0.50, 0.14, 0.064, col_boom, parent=boom_pivot)

dipper_head_pts = [
    (4.06, 5.44),
    (4.26, 5.62),
    (4.98, 5.32),
    (5.26, 4.86),
    (4.82, 4.44),
    (4.36, 4.74),
]
for side, y_pos in [("L", 0.18), ("R", -0.18)]:
    make_xz_plate(f"Dipper_Head_Cheek_{side}", dipper_head_pts, y_pos, 0.055, col_boom, mat=mat_red, parent=dipper_pivot, bevel=0.01)
make_xz_plate("Dipper_Head_Core", [(4.35, 5.38), (4.88, 5.14), (5.10, 4.76), (4.62, 4.65)], 0.0, 0.28, col_boom, mat=mat_red, parent=dipper_pivot, bevel=0.01)

make_pin_boss("Dipper_Cyl_RodPin", P_DIPPER_CYL_ROD, 0.44, 0.10, 0.050, col_boom, parent=dipper_pivot)
make_pin_boss("Curl_Cyl_BasePin",  P_CURL_CYL_BASE,  0.44, 0.095, 0.048, col_boom, parent=dipper_pivot)

dipper_stations = [
    (4.78, 4.72, 0.50, 0.34),
    (5.35, 4.35, 0.44, 0.32),
    (6.05, 3.90, 0.38, 0.29),
    (6.68, 3.50, 0.32, 0.27),
    (7.15, 3.20, 0.26, 0.25),
]
make_box_girder("Dipper_Arm", dipper_stations, col_boom, mat=mat_red, parent=dipper_pivot, flange_extra_w=0.045, flange_t=0.03)

make_hydraulic_cylinder(
    "Dipper_Cylinder",
    P_DIPPER_CYL_BASE, P_DIPPER_CYL_ROD,
    barrel_r=0.105, rod_r=0.060,
    col=col_boom, base_parent=boom_pivot, rod_parent=dipper_pivot, barrel_ratio=0.56
)

make_pin_boss("Link_Dipper_Pin", P_LINK_BASE, 0.42, 0.09, 0.045, col_boom, parent=dipper_pivot)
make_pin_boss("Link_Apex_Pin",   P_LINK_APEX, 0.42, 0.09, 0.045, col_boom, parent=dipper_pivot)

for side, y_pos in [("L", 0.175), ("R", -0.175)]:
    make_link_bar(f"Rocker_Link_{side}", P_LINK_BASE, P_LINK_APEX, y_pos, 0.13, 0.045, col_boom, mat=mat_red, parent=dipper_pivot)
for side, y_pos in [("L", 0.11), ("R", -0.11)]:
    make_link_bar(f"Push_Link_{side}", P_LINK_APEX, P_BREAKER_LINK, y_pos, 0.12, 0.045, col_boom, mat=mat_red, parent=dipper_pivot)

make_hydraulic_cylinder(
    "Breaker_Curl_Cylinder",
    P_CURL_CYL_BASE, P_LINK_APEX,
    barrel_r=0.092, rod_r=0.054,
    col=col_boom, base_parent=dipper_pivot, rod_parent=dipper_pivot, barrel_ratio=0.56
)

# ==============================================================================
# 7. COLLECTION 03: HYDRAULIC ROCK BREAKER (HAMMER)
# ==============================================================================
breaker_pivot = make_empty("Breaker_Pivot", P_BREAKER_PIVOT, col_breaker, parent=dipper_pivot, size=0.30)
make_pin_boss("Breaker_Main_Pin", P_BREAKER_PIVOT, 0.46, 0.10, 0.050, col_breaker, parent=breaker_pivot)
make_pin_boss("Breaker_Link_Pin", P_BREAKER_LINK,  0.46, 0.095, 0.046, col_breaker, parent=breaker_pivot)

HX = 7.42

bracket_pts = [
    (7.04, 3.00),
    (7.78, 3.00),
    (7.76, 3.44),
    (7.52, 3.44),
    (7.42, 3.24),
    (7.24, 3.36),
    (7.04, 3.32),
]
for side, y_pos in [("L", 0.19), ("R", -0.19)]:
    make_xz_plate(f"Breaker_Bracket_{side}", bracket_pts, y_pos, 0.05, col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.008)

make_box("Breaker_Top_Cap", (HX, 0.0, 2.96), (0.74, 0.48, 0.10), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.01)
for bx in (7.12, 7.32, 7.52, 7.72):
    for by in (-0.19, 0.19):
        make_cyl(f"Cap_Bolt_{bx:.2f}_{by:.2f}", (bx, by, 3.025), 0.018, 0.04, col_breaker, verts=6, mat=mat_machined, parent=breaker_pivot)

make_box("Breaker_Main_Body", (HX, 0.0, 2.02), (0.54, 0.46, 1.78), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.025)
make_box("Breaker_Upper_Collar", (HX, 0.0, 2.78), (0.59, 0.50, 0.18), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.012)
make_box("Breaker_Lower_Skirt",  (HX, 0.0, 1.22), (0.60, 0.52, 0.24), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.015)

for side_y in (-0.235, 0.235):
    for iz, z_slot in enumerate([2.52, 2.26, 2.00, 1.74, 1.48]):
        make_box(f"Breaker_BoltSlot_{side_y:.2f}_{iz}", (HX, side_y, z_slot), (0.14, 0.03, 0.10), col_breaker, mat=mat_dark, parent=breaker_pivot, bevel=0.004)
        make_cyl(f"Breaker_SideBolt_{side_y:.2f}_{iz}", (HX + 0.16, side_y, z_slot), 0.022, 0.04, col_breaker, rot=(math.radians(90), 0, 0), verts=6, mat=mat_machined, parent=breaker_pivot)
        make_cyl(f"Breaker_SideBoltB_{side_y:.2f}_{iz}", (HX - 0.16, side_y, z_slot), 0.022, 0.04, col_breaker, rot=(math.radians(90), 0, 0), verts=6, mat=mat_machined, parent=breaker_pivot)

for py in (-0.11, 0.11):
    make_cyl(f"Breaker_HydPort_{py:.2f}", (HX - 0.30, py, 2.15), 0.036, 0.10, col_breaker, rot=(0, math.radians(90), 0), verts=6, mat=mat_machined, parent=breaker_pivot)

make_cyl("Breaker_Tool_Chuck", (HX, 0.0, 0.98), 0.145, 0.26, col_breaker, verts=28, mat=mat_dark, parent=breaker_pivot, bevel=0.008)
make_cyl("Tool_Retainer_Pin",  (HX, 0.0, 1.02), 0.032, 0.34, col_breaker, rot=(math.radians(90), 0, 0), mat=mat_machined, parent=breaker_pivot)

bm_chisel = bmesh.new()
bmesh.ops.create_cone(
    bm_chisel, cap_ends=True, segments=24, radius1=0.072, radius2=0.072, depth=0.52,
    matrix=Matrix.Translation((0, 0, 0.62))
)
bmesh.ops.create_cone(
    bm_chisel, cap_ends=True, segments=24, radius1=0.010, radius2=0.072, depth=0.26,
    matrix=Matrix.Translation((0, 0, 0.23))
)
mesh_chisel = bpy.data.meshes.new("Breaker_Moil_Chisel")
bm_chisel.to_mesh(mesh_chisel)
bm_chisel.free()
for p in mesh_chisel.polygons:
    p.use_smooth = True
obj_chisel = bpy.data.objects.new("Breaker_Moil_Chisel", mesh_chisel)
obj_chisel.location = (HX, 0.0, 0.0)
link_obj(obj_chisel, col_breaker, mat=mat_dark, parent=breaker_pivot)

# ==============================================================================
# 8. COLLECTION 04: HYDRAULIC HOSES & STEEL CLAMP LINES
# ==============================================================================
for i, y_off in enumerate([-0.14, -0.05, 0.05, 0.14]):
    pts = [
        (-0.62, y_off, 2.08),
        (-0.68, y_off * 1.2, 2.48 + (i % 2) * 0.08),
        (-0.34, y_off * 1.1, 2.66 + (i % 2) * 0.06),
        (-0.02, y_off * 0.9, 2.48),
        ( 0.40, y_off * 0.8, 2.95),
    ]
    make_hose(f"Turret_Manifold_Hose_{i+1}", pts, 0.022, col_hoses, parent=turret_pivot)

for side, y_s in [("L", 0.23), ("R", -0.23)]:
    boom_line_pts = [
        (0.42, y_s, 2.95),
        (0.95, y_s, 3.68),
        (1.52, y_s, 4.24),
        (2.35, y_s, 4.58),
        (3.40, y_s, 4.82),
        (4.25, y_s, 4.98),
    ]
    make_hose(f"Boom_Spine_Line_{side}", boom_line_pts, 0.020, col_hoses, mat=mat_dark, parent=boom_pivot)

    for cx, cz in [(1.15, 3.88), (2.45, 4.60), (3.65, 4.86)]:
        make_box(f"Hose_Clamp_{side}_{cx:.1f}", (cx, y_s, cz), (0.08, 0.06, 0.09), col_hoses, mat=mat_machined, parent=boom_pivot, bevel=0.004)

    elbow_pts = [
        (4.25, y_s, 4.98),
        (4.65, y_s * 1.15, 5.18),
        (5.00, y_s * 1.20, 4.78),
        (5.28, y_s * 0.95, 4.46),
        (5.65, y_s * 0.85, 4.24),
    ]
    make_hose(f"Elbow_Jumper_Hose_{side}", elbow_pts, 0.021, col_hoses, parent=boom_pivot)

for idx, (y_dip, y_port, dip_drop) in enumerate([(0.16, 0.11, 2.10), (-0.16, -0.11, 2.22)]):
    breaker_hose_pts = [
        (6.25, y_dip, 3.66),
        (6.18, y_dip * 1.1, 2.92),
        (6.02, y_dip * 1.0, dip_drop),
        (6.48, y_port, dip_drop - 0.24),
        (6.95, y_port, 2.08),
        (HX - 0.30, y_port, 2.15),
    ]
    make_hose(f"Breaker_Feed_Hose_{idx+1}", breaker_hose_pts, 0.024, col_hoses, parent=dipper_pivot)

# ==============================================================================
# 9. COLLECTION 05: UNDERGROUND MINE TIP / GRIZZLY BAY INSTALLATION
# ==============================================================================
mine_root = make_empty("Mine_Tip_Environment", (0, 0, 0), col_mine, size=0.4)

make_box("Tip_Deck_PedestalSide", (1.75,  0.0, -0.25), (6.50, 7.60, 0.50), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.03)
make_box("Tip_Deck_FarSide",      (10.50, 0.0, -0.25), (3.00, 7.60, 0.50), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.03)
make_box("Tip_Deck_LeftWing",     (7.00,  2.90, -0.25), (4.00, 1.80, 0.50), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.03)
make_box("Tip_Deck_RightWing",    (7.00, -2.90, -0.25), (4.00, 1.80, 0.50), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.03)

make_box("OrePass_Wall_Left",  (7.00,  2.08, -1.90), (4.20, 0.16, 3.40), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.0)
make_box("OrePass_Wall_Right", (7.00, -2.08, -1.90), (4.20, 0.16, 3.40), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.0)
make_box("OrePass_Wall_Near",  (4.92,  0.00, -1.90), (0.16, 4.20, 3.40), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.0)
make_box("OrePass_Wall_Far",   (9.08,  0.00, -1.90), (0.16, 4.20, 3.40), col_mine, mat=mat_concrete, parent=mine_root, bevel=0.0)
make_box("OrePass_Dark_Bottom",(7.00,  0.00, -3.40), (4.20, 4.20, 0.20), col_mine, mat=mat_void,     parent=mine_root, bevel=0.0)

make_box("Grizzly_Frame_Near",  (4.96,  0.00, 0.02), (0.16, 4.24, 0.14), col_mine, mat=mat_dark, parent=mine_root, bevel=0.01)
make_box("Grizzly_Frame_Far",   (9.04,  0.00, 0.02), (0.16, 4.24, 0.14), col_mine, mat=mat_dark, parent=mine_root, bevel=0.01)
make_box("Grizzly_Frame_Left",  (7.00,  2.04, 0.02), (4.00, 0.16, 0.14), col_mine, mat=mat_dark, parent=mine_root, bevel=0.01)
make_box("Grizzly_Frame_Right", (7.00, -2.04, 0.02), (4.00, 0.16, 0.14), col_mine, mat=mat_dark, parent=mine_root, bevel=0.01)

for i in range(9):
    gy = -1.80 + i * 0.45
    make_box(f"Grizzly_Bar_Web_{i+1}", (7.00, gy, -0.06), (4.00, 0.08, 0.22), col_mine, mat=mat_dark, parent=mine_root, bevel=0.006)
    make_box(f"Grizzly_Bar_Top_{i+1}", (7.00, gy,  0.06), (4.00, 0.13, 0.05), col_mine, mat=mat_machined, parent=mine_root, bevel=0.008)

for gx in (6.15, 7.85):
    make_box(f"Grizzly_CrossTie_{gx:.2f}", (gx, 0.0, -0.14), (0.14, 4.00, 0.14), col_mine, mat=mat_dark, parent=mine_root, bevel=0.008)

make_box("LHD_Wheel_Stop_Curb", (9.45, 0.0, 0.20), (0.45, 4.40, 0.40), col_mine, mat=mat_yellow, parent=mine_root, bevel=0.04)
for bx, by in [(3.8, -2.2), (3.8, 2.2), (4.8, -2.35), (4.8, 2.35), (9.2, -2.35), (9.2, 2.35)]:
    make_cyl(f"Safety_Bollard_{bx}_{by}", (bx, by, 0.52), 0.085, 1.04, col_mine, verts=16, mat=mat_yellow, parent=mine_root, bevel=0.01)

def make_ore_boulder(name, loc, scale, seed):
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        n = rng.uniform(0.68, 1.24)
        v.co.x *= scale[0] * n
        v.co.y *= scale[1] * n
        v.co.z *= scale[2] * n
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(loc)
    obj.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
    return link_obj(obj, col_mine, mat=mat_ore, parent=mine_root)

make_ore_boulder("Oversize_Boulder_Target", (HX, 0.02, 0.22), (0.46, 0.42, 0.28), seed=42)
make_ore_boulder("Oversize_Boulder_2",      (6.35, -0.78, 0.24), (0.38, 0.34, 0.24), seed=17)
make_ore_boulder("Oversize_Boulder_3",      (7.90,  0.95, 0.22), (0.42, 0.32, 0.22), seed=89)
make_ore_boulder("Oversize_Boulder_4",      (6.70,  1.15, 0.19), (0.32, 0.28, 0.20), seed=103)

# ==============================================================================
# 10. INDUSTRIAL LIGHTING & CAMERA
# ==============================================================================
def add_area_light(name, loc, target, energy, size, color=(1.0, 1.0, 1.0)):
    ldata = bpy.data.lights.new(name=name, type='AREA')
    ldata.energy = energy
    ldata.size = size
    ldata.color = color
    lobj = bpy.data.objects.new(name, ldata)
    lobj.location = Vector(loc)
    lobj.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(lobj)

add_area_light("Mine_Overhead_Flood", (4.2, -3.5, 9.0), (4.0, 0.0, 2.2), energy=2200, size=3.5, color=(1.0, 0.96, 0.90))
add_area_light("Cool_Rim_Light",      (5.0,  6.5, 5.5), (4.0, 0.0, 2.5), energy=900,  size=2.5, color=(0.75, 0.88, 1.0))

cam_data = bpy.data.cameras.new("Main_Camera")
cam_data.lens = 40
cam_obj = bpy.data.objects.new("Main_Camera", cam_data)
cam_obj.location = Vector((4.2, -10.5, 3.8))
cam_obj.rotation_euler = (Vector((4.0, 0.0, 2.3)) - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

bpy.context.view_layer.update()
print("Stationary Underground Rock Breaker & Grizzly Tip generated cleanly!")
