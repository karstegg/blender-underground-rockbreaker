import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler

# ==============================================================================
# 1. SCENE RESET & COLLECTIONS
# ==============================================================================
if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)

for block_group in (
    bpy.data.meshes,
    bpy.data.curves,
    bpy.data.armatures,
    bpy.data.materials,
    bpy.data.lights,
    bpy.data.cameras,
):
    for item in list(block_group):
        if item.users == 0:
            block_group.remove(item)

def make_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

col_base    = make_collection("01_Pedestal_Base")
col_boom    = make_collection("02_Boom_Assembly")
col_breaker = make_collection("03_Hydraulic_Breaker")
col_hoses   = make_collection("04_Hydraulic_Hoses")
col_mine    = make_collection("05_Mine_Tip_Grizzly")
col_bay     = make_collection("06_Underground_Mine_Bay")

# ==============================================================================
# 2. PROCEDURAL INDUSTRIAL MATERIALS (Blender 3.6 / 4.x / 5.x Compatible)
# ==============================================================================
def create_mat(
    name,
    color,
    metallic=0.0,
    roughness=0.5,
    coat=0.0,
    noise_scale=0.0,
    rough_var=0.0,
    bump_strength=0.0,
    color_var=0.0,
):
    mat = bpy.data.materials.new(name=name)
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if coat > 0.0 and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat

    if noise_scale > 0.0 and (rough_var > 0.0 or bump_strength > 0.0 or color_var > 0.0):
        tex_coord = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 6.0
        noise.inputs["Roughness"].default_value = 0.62
        links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

        if rough_var > 0.0:
            mr = nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 0.25
            mr.inputs["From Max"].default_value = 0.75
            mr.inputs["To Min"].default_value = max(0.02, roughness - rough_var)
            mr.inputs["To Max"].default_value = min(0.98, roughness + rough_var)
            links.new(noise.outputs["Fac"], mr.inputs["Value"])
            links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

        if color_var > 0.0:
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = 'RGBA'
            dark_c = tuple(max(0.0, c * (1.0 - color_var)) for c in color)
            light_c = tuple(min(1.0, c * (1.0 + color_var * 0.65)) for c in color)
            mix.inputs["A"].default_value = (*dark_c, 1.0)
            mix.inputs["B"].default_value = (*light_c, 1.0)
            links.new(noise.outputs["Fac"], mix.inputs["Factor"])
            links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])

        if bump_strength > 0.0:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = bump_strength
            bump.inputs["Distance"].default_value = 0.015
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat

mat_red = create_mat(
    "Rockbreaker_Red", (0.76, 0.038, 0.024),
    metallic=0.22, roughness=0.30, coat=0.28,
    noise_scale=4.5, rough_var=0.07, bump_strength=0.03, color_var=0.08,
)
mat_dark = create_mat(
    "Dark_Steel", (0.065, 0.072, 0.080),
    metallic=0.80, roughness=0.38,
    noise_scale=7.0, rough_var=0.09, bump_strength=0.04, color_var=0.10,
)
mat_machined = create_mat(
    "Machined_Steel", (0.50, 0.53, 0.56),
    metallic=0.92, roughness=0.24,
    noise_scale=12.0, rough_var=0.05, bump_strength=0.02,
)
mat_chrome = create_mat(
    "Hydraulic_Chrome", (0.90, 0.92, 0.95),
    metallic=0.98, roughness=0.08,
)
mat_hose = create_mat(
    "Hydraulic_Rubber", (0.022, 0.023, 0.026),
    metallic=0.02, roughness=0.72,
    noise_scale=18.0, rough_var=0.08, bump_strength=0.03,
)
mat_concrete = create_mat(
    "Mine_Concrete", (0.155, 0.150, 0.142),
    metallic=0.00, roughness=0.88,
    noise_scale=2.2, rough_var=0.09, bump_strength=0.16, color_var=0.22,
)
mat_yellow = create_mat(
    "Safety_Yellow", (0.86, 0.56, 0.02),
    metallic=0.12, roughness=0.36, coat=0.15,
    noise_scale=5.0, rough_var=0.08, bump_strength=0.03, color_var=0.08,
)
mat_hazard_black = create_mat(
    "Hazard_Black", (0.025, 0.025, 0.028),
    metallic=0.08, roughness=0.48,
)
mat_ore = create_mat(
    "Oversize_Ore_Rock", (0.145, 0.132, 0.122),
    metallic=0.09, roughness=0.90,
    noise_scale=6.5, rough_var=0.08, bump_strength=0.32, color_var=0.28,
)
mat_void = create_mat(
    "Ore_Pass_Void", (0.006, 0.006, 0.008),
    metallic=0.00, roughness=1.00,
)
mat_shotcrete = create_mat(
    "Mine_Shotcrete", (0.088, 0.085, 0.082),
    metallic=0.00, roughness=0.94,
    noise_scale=2.4, rough_var=0.06, bump_strength=0.65, color_var=0.35,
)
mat_hpu_blue = create_mat(
    "HPU_Industrial_Blue", (0.06, 0.19, 0.34),
    metallic=0.35, roughness=0.36, coat=0.18,
    noise_scale=5.5, rough_var=0.07, bump_strength=0.03, color_var=0.08,
)
mat_cabinet = create_mat(
    "Control_Cabinet_Grey", (0.42, 0.44, 0.46),
    metallic=0.45, roughness=0.42,
    noise_scale=8.0, rough_var=0.06, bump_strength=0.02,
)
mat_vent_duct = create_mat(
    "Vent_Duct_Yellow", (0.78, 0.44, 0.03),
    metallic=0.02, roughness=0.58,
    noise_scale=9.0, rough_var=0.09, bump_strength=0.08, color_var=0.12,
)
mat_pipe_water = create_mat(
    "Pipe_Water_Blue", (0.06, 0.28, 0.56),
    metallic=0.62, roughness=0.38,
)
mat_pipe_air = create_mat(
    "Pipe_Air_Orange", (0.72, 0.24, 0.03),
    metallic=0.58, roughness=0.40,
)

def create_emissive_mat(name, color, strength=8.0):
    mat = bpy.data.materials.new(name=name)
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat

mat_lamp_glow = create_emissive_mat("Mine_Lamp_Emissive", (1.0, 0.94, 0.80), strength=14.0)
mat_led_green = create_emissive_mat("Indicator_Green",    (0.08, 0.95, 0.22), strength=6.0)
mat_led_red   = create_emissive_mat("Indicator_Red",      (0.95, 0.10, 0.08), strength=6.0)

# ==============================================================================
# 3. GEOMETRY, SHADING & RIGGING HELPERS
# ==============================================================================
def apply_auto_smooth_bmesh(bm, angle_deg=35.0):
    """Smooth curved faces while keeping edges sharper than angle_deg crisp."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    angle_rad = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < angle_rad
        else:
            e.smooth = False

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

def parent_to_bone(obj, arm_obj, bone_name):
    """Attach an object in its current world transform to a specific armature bone."""
    bpy.context.view_layer.update()
    world_mat = obj.matrix_world.copy()
    obj.parent = arm_obj
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    pbone = arm_obj.pose.bones[bone_name]
    # Blender bone parenting places origin at bone tail along bone matrix
    bone_world = arm_obj.matrix_world @ pbone.matrix @ Matrix.Translation((0.0, pbone.length, 0.0))
    obj.matrix_parent_inverse = bone_world.inverted()
    obj.matrix_world = world_mat
    return obj

def make_empty(name, loc, col, parent=None, size=0.25):
    emp = bpy.data.objects.new(name, None)
    emp.location = Vector(loc)
    emp.empty_display_type = 'PLAIN_AXES'
    emp.empty_display_size = size
    obj = link_obj(emp, col, parent=parent)
    bpy.context.view_layer.update()
    return obj

def make_box(name, loc, dims, col, rot=(0, 0, 0), mat=None, parent=None, bevel=0.012):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(dims), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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
    apply_auto_smooth_bmesh(bm, angle_deg=38.0 if verts >= 12 else 20.0)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
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
        apply_auto_smooth_bmesh(bm, angle_deg=35.0)
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
        bevel_w=0.010
    )
    build_loft(
        f"{name}_TopFlange",
        lambda p, up, h, w: [
            p + up * (h * 0.5 + flange_t) + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 + flange_t) + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 - 0.008)    + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p + up * (h * 0.5 - 0.008)    + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
        ],
        bevel_w=0.008
    )
    build_loft(
        f"{name}_BotFlange",
        lambda p, up, h, w: [
            p - up * (h * 0.5 - 0.008)    + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 - 0.008)    + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 + flange_t) + Vector((0, -(w + flange_extra_w) * 0.5, 0)),
            p - up * (h * 0.5 + flange_t) + Vector((0,  (w + flange_extra_w) * 0.5, 0)),
        ],
        bevel_w=0.008
    )
    return web

def make_pin_boss(name, pos, width, boss_r, pin_r, col, parent=None):
    rot_y = (math.radians(90), 0.0, 0.0)
    objs = []
    objs.append(make_cyl(f"{name}_Boss", pos, boss_r, width, col, rot=rot_y, mat=mat_red, parent=parent, bevel=0.008))
    objs.append(make_cyl(f"{name}_Pin",  pos, pin_r,  width + 0.09, col, rot=rot_y, mat=mat_machined, parent=parent, bevel=0.005))
    for s in (-1, 1):
        cap_pos = Vector(pos) + Vector((0, s * (width * 0.5 + 0.055), 0))
        objs.append(make_cyl(f"{name}_Cap_{s}", cap_pos, pin_r * 0.55, 0.025, col, rot=rot_y, verts=6, mat=mat_dark, parent=parent))
    return objs

def make_link_bar(name, p1, p2, y_offset, width_h, thick_y, col, mat=mat_red, parent=None):
    p1 = Vector((p1[0], y_offset, p1[2]))
    p2 = Vector((p2[0], y_offset, p2[2]))
    mid = (p1 + p2) * 0.5
    dv = p2 - p1
    length = dv.length
    angle_y = -math.atan2(dv.z, dv.x)
    rot_y = (math.radians(90), 0.0, 0.0)
    objs = [
        make_box(f"{name}_Bar", mid, (length, thick_y, width_h), col, rot=(0, angle_y, 0), mat=mat, parent=parent, bevel=0.01),
        make_cyl(f"{name}_Eye1", p1, width_h * 0.58, thick_y + 0.015, col, rot=rot_y, mat=mat, parent=parent, bevel=0.006),
        make_cyl(f"{name}_Eye2", p2, width_h * 0.58, thick_y + 0.015, col, rot=rot_y, mat=mat, parent=parent, bevel=0.006),
    ]
    return objs

def make_hydraulic_cylinder(
    name,
    p_base,
    p_rod,
    barrel_r,
    rod_r,
    col,
    base_parent,
    rod_parent,
    barrel_ratio=0.56,
    rod_bone=None,
):
    """Build a telescoping hydraulic cylinder with crisp auto-smoothed geometry and DAMPED_TRACK constraints."""
    p_base = Vector(p_base)
    p_rod  = Vector(p_rod)
    dv = p_rod - p_base
    dist = dv.length
    quat = dv.normalized().to_track_quat('Z', 'X')

    emp_base = make_empty(f"{name}_BaseTarget", p_base, col, parent=base_parent, size=0.08)
    if rod_bone:
        emp_rod = make_empty(f"{name}_RodTarget", p_rod, col, parent=None, size=0.08)
        parent_to_bone(emp_rod, rod_parent, rod_bone)
    else:
        emp_rod = make_empty(f"{name}_RodTarget", p_rod, col, parent=rod_parent, size=0.08)

    barrel_len = dist * barrel_ratio
    rod_len    = dist * 0.78

    # Barrel mesh (origin at p_base, extends along +Z)
    bm_b = bmesh.new()
    m_eye = Matrix.Rotation(math.radians(90), 4, 'X')
    bmesh.ops.create_cone(
        bm_b, cap_ends=True, cap_tris=False, segments=28,
        radius1=barrel_r * 0.92, radius2=barrel_r * 0.92, depth=barrel_r * 1.45,
        matrix=m_eye,
    )
    bmesh.ops.create_cone(
        bm_b, cap_ends=True, cap_tris=False, segments=32,
        radius1=barrel_r, radius2=barrel_r, depth=barrel_len,
        matrix=Matrix.Translation((0, 0, barrel_r * 0.7 + barrel_len * 0.5)),
    )
    # Gland nut / collar with subtle chamfered step
    bmesh.ops.create_cone(
        bm_b, cap_ends=True, cap_tris=False, segments=32,
        radius1=barrel_r * 1.14, radius2=barrel_r * 1.14, depth=0.11,
        matrix=Matrix.Translation((0, 0, barrel_r * 0.7 + barrel_len - 0.02)),
    )
    # Port bosses
    port_z = (barrel_r * 0.7 + 0.14, barrel_r * 0.7 + barrel_len - 0.16)
    for z_port in port_z:
        bmesh.ops.create_cube(
            bm_b, size=1.0,
            matrix=Matrix.Translation((barrel_r * 1.05, 0, z_port)) @ Matrix.Diagonal((0.06, 0.06, 0.07, 1.0)),
        )
    apply_auto_smooth_bmesh(bm_b, angle_deg=35.0)
    mesh_b = bpy.data.meshes.new(f"{name}_Barrel")
    bm_b.to_mesh(mesh_b)
    bm_b.free()
    obj_barrel = bpy.data.objects.new(f"{name}_Barrel", mesh_b)
    obj_barrel.location = p_base
    obj_barrel.rotation_euler = quat.to_euler()
    link_obj(obj_barrel, col, mat=mat_dark, parent=base_parent)

    c_b = obj_barrel.constraints.new('DAMPED_TRACK')
    c_b.target = emp_rod
    c_b.track_axis = 'TRACK_Z'

    # Chrome piston rod mesh (origin at p_rod, extends along -Z)
    bm_r = bmesh.new()
    bmesh.ops.create_cone(
        bm_r, cap_ends=True, cap_tris=False, segments=28,
        radius1=rod_r * 1.65, radius2=rod_r * 1.65, depth=barrel_r * 1.35,
        matrix=m_eye,
    )
    bmesh.ops.create_cone(
        bm_r, cap_ends=True, cap_tris=False, segments=28,
        radius1=rod_r, radius2=rod_r, depth=rod_len,
        matrix=Matrix.Translation((0, 0, -(rod_r * 1.2 + rod_len * 0.5))),
    )
    apply_auto_smooth_bmesh(bm_r, angle_deg=35.0)
    mesh_r = bpy.data.meshes.new(f"{name}_Rod")
    bm_r.to_mesh(mesh_r)
    bm_r.free()
    obj_rod = bpy.data.objects.new(f"{name}_Rod", mesh_r)
    obj_rod.location = p_rod
    obj_rod.rotation_euler = quat.to_euler()
    if rod_bone:
        link_obj(obj_rod, col, mat=mat_chrome, parent=None)
        parent_to_bone(obj_rod, rod_parent, rod_bone)
    else:
        link_obj(obj_rod, col, mat=mat_chrome, parent=rod_parent)

    c_r = obj_rod.constraints.new('DAMPED_TRACK')
    c_r.target = emp_base
    c_r.track_axis = 'TRACK_NEGATIVE_Z'

    return obj_barrel, obj_rod, emp_base, emp_rod

def make_hose(name, points, radius, col, mat=mat_hose, parent=None, hooks=None):
    """
    Create a 3D NURBS hydraulic hose.
    Optional `hooks`: list of (target_obj, [point_indices]) tuples so the hose
    flexes smoothly across moving joints without detaching from fittings.
    """
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
    link_obj(obj, col, mat=mat, parent=parent)

    if hooks:
        bpy.context.view_layer.update()
        for idx, (target_obj, pt_indices) in enumerate(hooks):
            mod = obj.modifiers.new(f"Hook_{idx}", 'HOOK')
            mod.object = target_obj
            mod.vertex_indices_set(list(pt_indices))
            mod.matrix_inverse = target_obj.matrix_world.inverted() @ obj.matrix_world

    return obj

def make_fitting(name, loc, col, rot=(0, 0, 0), radius=0.032, length=0.07, parent=None):
    return make_cyl(name, loc, radius, length, col, rot=rot, verts=6, mat=mat_machined, parent=parent)

# ==============================================================================
# 4. MASTER KINEMATIC COORDINATES (Meters, XZ Centerline Plane)
# ==============================================================================
Z_PLINTH_TOP      = 0.80
Z_GRIZZLY_TOP     = 0.085
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
P_LINK_BASE       = Vector((6.66, 0.00, 3.68))
P_LINK_APEX       = Vector((7.26, 0.00, 4.12))
P_BREAKER_PIVOT   = Vector((7.15, 0.00, 3.38))
P_BREAKER_LINK    = Vector((7.65, 0.00, 3.50))

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
make_box("Turret_Manifold_Tray", (-0.64, 0.0, 1.84), (0.34, 0.56, 0.05), col_base, mat=mat_red, parent=turret_pivot, bevel=0.006)
for sy in (-0.22, 0.22):
    make_xz_plate(
        f"Manifold_Tray_Gusset_{sy:.2f}",
        [(-0.52, 1.62), (-0.52, 1.82), (-0.76, 1.82)],
        sy, 0.03, col_base, mat=mat_red, parent=turret_pivot, bevel=0.004,
    )
make_box("Hydraulic_Valve_Block", (-0.62, 0.0, 1.98), (0.24, 0.42, 0.22), col_base, mat=mat_dark, parent=turret_pivot, bevel=0.008)
for i, y_off in enumerate([-0.15, -0.05, 0.05, 0.15]):
    make_fitting(f"Valve_Port_Fitting_{i+1}", (-0.62, y_off, 2.11), col_base, radius=0.026, length=0.06, parent=turret_pivot)

# Planetary slew drive motor + mounting flange
make_cyl("Slew_Motor_Flange",  (-0.36, 0.30, 1.59), 0.145, 0.04, col_base, verts=24, mat=mat_machined, parent=turret_pivot, bevel=0.005)
make_cyl("Slew_Motor_Housing", (-0.36, 0.30, 1.78), 0.110, 0.34, col_base, verts=28, mat=mat_dark, parent=turret_pivot, bevel=0.008)
make_cyl("Slew_Motor_Cap",     (-0.36, 0.30, 1.98), 0.082, 0.09, col_base, verts=24, mat=mat_machined, parent=turret_pivot, bevel=0.005)

make_pin_boss("Boom_Base", P_BOOM_BASE, 0.60, 0.14, 0.068, col_base, parent=turret_pivot)
make_pin_boss("Lift_Cyl_Base_Pin", (P_LIFT_BASE_X, 0.0, P_LIFT_BASE_Z), 0.88, 0.10, 0.052, col_base, parent=turret_pivot)

# ==============================================================================
# 6. COLLECTION 02: ARCHED MAIN BOOM, DIPPER ARM, 4-BAR IK & HYDRAULIC CYLINDERS
# ==============================================================================
boom_pivot = make_empty("Boom_Pivot", P_BOOM_BASE, col_boom, parent=turret_pivot, size=0.35)

# Smooth 13-station curved box-girder main boom
boom_stations = [
    (0.05, 2.15, 0.44, 0.40),
    (0.30, 2.50, 0.47, 0.40),
    (0.58, 2.90, 0.52, 0.40),
    (0.88, 3.31, 0.57, 0.40),
    (1.18, 3.68, 0.61, 0.39),
    (1.48, 3.96, 0.64, 0.38),
    (1.78, 4.13, 0.62, 0.38),
    (2.12, 4.26, 0.59, 0.37),
    (2.55, 4.38, 0.56, 0.36),
    (3.05, 4.51, 0.52, 0.35),
    (3.55, 4.63, 0.47, 0.34),
    (4.05, 4.74, 0.42, 0.33),
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
        col=col_boom, base_parent=turret_pivot, rod_parent=boom_pivot, barrel_ratio=0.55,
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
    (4.78, 4.74, 0.50, 0.34),
    (5.35, 4.40, 0.44, 0.32),
    (6.05, 3.98, 0.38, 0.29),
    (6.68, 3.63, 0.32, 0.27),
    (7.15, 3.38, 0.26, 0.25),
]
make_box_girder("Dipper_Arm", dipper_stations, col_boom, mat=mat_red, parent=dipper_pivot, flange_extra_w=0.045, flange_t=0.03)

make_hydraulic_cylinder(
    "Dipper_Cylinder",
    P_DIPPER_CYL_BASE, P_DIPPER_CYL_ROD,
    barrel_r=0.105, rod_r=0.060,
    col=col_boom, base_parent=boom_pivot, rod_parent=dipper_pivot, barrel_ratio=0.56,
)

# Breaker Pivot & Link Target (created before 4-bar IK so IK targets Breaker_Link_Target)
breaker_pivot = make_empty("Breaker_Pivot", P_BREAKER_PIVOT, col_breaker, parent=dipper_pivot, size=0.30)
breaker_link_target = make_empty("Breaker_Link_IK_Target", P_BREAKER_LINK, col_boom, parent=breaker_pivot, size=0.08)

# Native 2-Bone IK Rig for Exact Closed-Chain 4-Bar Breaker Curl Linkage
# Zero Python drivers required; works automatically when rotating Breaker_Pivot about Y.
arm_data = bpy.data.armatures.new("Linkage_4Bar_IK_Rig")
arm_obj = bpy.data.objects.new("Linkage_4Bar_IK_Rig", arm_data)
link_obj(arm_obj, col_boom, parent=dipper_pivot)
arm_obj.hide_render = True
arm_obj.display_type = 'WIRE'

bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

inv_arm = arm_obj.matrix_world.inverted()
b_rocker = arm_data.edit_bones.new("Rocker_Bone")
b_rocker.head = inv_arm @ P_LINK_BASE
b_rocker.tail = inv_arm @ P_LINK_APEX
b_rocker.align_roll(Vector((0.0, 1.0, 0.0)))

b_push = arm_data.edit_bones.new("Push_Bone")
b_push.parent = b_rocker
b_push.use_connect = True
b_push.head = inv_arm @ P_LINK_APEX
b_push.tail = inv_arm @ P_BREAKER_LINK
b_push.align_roll(Vector((0.0, 1.0, 0.0)))

bpy.ops.object.mode_set(mode='POSE')
pb_rocker = arm_obj.pose.bones["Rocker_Bone"]
pb_push   = arm_obj.pose.bones["Push_Bone"]

# Lock IK strictly to the XZ plane (align_roll aligns bone local Z to world +Y)
for pb in (pb_rocker, pb_push):
    pb.lock_ik_x = True
    pb.lock_ik_y = True
    pb.lock_ik_z = False

ik_con = pb_push.constraints.new('IK')
ik_con.target = breaker_link_target
ik_con.chain_count = 2
ik_con.iterations = 64

bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.hide_set(True)
bpy.context.view_layer.update()

make_pin_boss("Link_Dipper_Pin", P_LINK_BASE, 0.42, 0.09, 0.045, col_boom, parent=dipper_pivot)

# Apex pin and Rocker/Push bars are bone-parented so the 4-bar linkage articulates cleanly
apex_pin_objs = make_pin_boss("Link_Apex_Pin", P_LINK_APEX, 0.42, 0.09, 0.045, col_boom, parent=None)
for o in apex_pin_objs:
    parent_to_bone(o, arm_obj, "Rocker_Bone")

for side, y_pos in [("L", 0.175), ("R", -0.175)]:
    for o in make_link_bar(f"Rocker_Link_{side}", P_LINK_BASE, P_LINK_APEX, y_pos, 0.13, 0.045, col_boom, mat=mat_red, parent=None):
        parent_to_bone(o, arm_obj, "Rocker_Bone")

for side, y_pos in [("L", 0.11), ("R", -0.11)]:
    for o in make_link_bar(f"Push_Link_{side}", P_LINK_APEX, P_BREAKER_LINK, y_pos, 0.12, 0.045, col_boom, mat=mat_red, parent=None):
        parent_to_bone(o, arm_obj, "Push_Bone")

make_hydraulic_cylinder(
    "Breaker_Curl_Cylinder",
    P_CURL_CYL_BASE, P_LINK_APEX,
    barrel_r=0.092, rod_r=0.054,
    col=col_boom, base_parent=dipper_pivot, rod_parent=arm_obj,
    barrel_ratio=0.56, rod_bone="Rocker_Bone",
)

# ==============================================================================
# 7. COLLECTION 03: HYDRAULIC ROCK BREAKER (HAMMER)
# ==============================================================================
make_pin_boss("Breaker_Main_Pin", P_BREAKER_PIVOT, 0.46, 0.10, 0.050, col_breaker, parent=breaker_pivot)
make_pin_boss("Breaker_Link_Pin", P_BREAKER_LINK,  0.46, 0.095, 0.046, col_breaker, parent=breaker_pivot)

HX = 7.42
Z_SHIFT = 0.18  # Elevates breaker cleanly so chisel tip seats on target boulder top

bracket_pts = [
    (7.04, 3.00 + Z_SHIFT),
    (7.78, 3.00 + Z_SHIFT),
    (7.76, 3.44 + Z_SHIFT),
    (7.52, 3.44 + Z_SHIFT),
    (7.42, 3.24 + Z_SHIFT),
    (7.24, 3.36 + Z_SHIFT),
    (7.04, 3.32 + Z_SHIFT),
]
for side, y_pos in [("L", 0.19), ("R", -0.19)]:
    make_xz_plate(f"Breaker_Bracket_{side}", bracket_pts, y_pos, 0.05, col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.008)

make_box("Breaker_Top_Cap", (HX, 0.0, 2.97 + Z_SHIFT), (0.74, 0.48, 0.11), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.01)
for bx in (7.12, 7.32, 7.52, 7.72):
    for by in (-0.19, 0.19):
        make_cyl(f"Cap_Bolt_{bx:.2f}_{by:.2f}", (bx, by, 3.04 + Z_SHIFT), 0.018, 0.04, col_breaker, verts=6, mat=mat_machined, parent=breaker_pivot)

make_box("Breaker_Main_Body",   (HX, 0.0, 2.04 + Z_SHIFT), (0.54, 0.46, 1.78), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.025)
make_box("Breaker_Upper_Collar",(HX, 0.0, 2.81 + Z_SHIFT), (0.59, 0.50, 0.22), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.012)
make_box("Breaker_Lower_Skirt", (HX, 0.0, 1.24 + Z_SHIFT), (0.60, 0.52, 0.24), col_breaker, mat=mat_red, parent=breaker_pivot, bevel=0.015)

# Flush-framed recessed service slots (thin machined bezel + inset dark rubber plug)
for side_sign, side_y in [(-1, -0.23), (1, 0.23)]:
    for iz, z_slot in enumerate([2.54, 2.28, 2.02, 1.76, 1.50]):
        zs = z_slot + Z_SHIFT
        make_box(f"Breaker_SlotFrame_{side_sign}_{iz}", (HX, side_y + side_sign * 0.004, zs), (0.16, 0.012, 0.115), col_breaker, mat=mat_dark, parent=breaker_pivot, bevel=0.003)
        make_box(f"Breaker_SlotPlug_{side_sign}_{iz}",  (HX, side_y + side_sign * 0.008, zs), (0.12, 0.008, 0.080), col_breaker, mat=mat_hose, parent=breaker_pivot, bevel=0.002)
        make_cyl(f"Breaker_SideBolt_{side_sign}_{iz}",  (HX + 0.16, side_y + side_sign * 0.012, zs), 0.022, 0.032, col_breaker, rot=(math.radians(90), 0, 0), verts=6, mat=mat_machined, parent=breaker_pivot)
        make_cyl(f"Breaker_SideBoltB_{side_sign}_{iz}", (HX - 0.16, side_y + side_sign * 0.012, zs), 0.022, 0.032, col_breaker, rot=(math.radians(90), 0, 0), verts=6, mat=mat_machined, parent=breaker_pivot)

Z_BREAKER_PORT = 2.18 + Z_SHIFT
for py in (-0.11, 0.11):
    make_cyl(f"Breaker_HydPort_{py:.2f}", (HX - 0.30, py, Z_BREAKER_PORT), 0.036, 0.11, col_breaker, rot=(0, math.radians(90), 0), verts=6, mat=mat_machined, parent=breaker_pivot)

make_cyl("Breaker_Tool_Chuck", (HX, 0.0, 1.01 + Z_SHIFT), 0.145, 0.26, col_breaker, verts=28, mat=mat_dark, parent=breaker_pivot, bevel=0.008)
make_cyl("Tool_Retainer_Pin",  (HX, 0.0, 1.05 + Z_SHIFT), 0.032, 0.34, col_breaker, rot=(math.radians(90), 0, 0), mat=mat_machined, parent=breaker_pivot)

# Forged moil point chisel with crisp auto-smoothing (tip at z = 0.50 m)
bm_chisel = bmesh.new()
bmesh.ops.create_cone(
    bm_chisel, cap_ends=True, cap_tris=False, segments=28,
    radius1=0.072, radius2=0.072, depth=0.38,
    matrix=Matrix.Translation((0, 0, 0.72 + Z_SHIFT)),
)
bmesh.ops.create_cone(
    bm_chisel, cap_ends=True, cap_tris=False, segments=28,
    radius1=0.012, radius2=0.072, depth=0.22,
    matrix=Matrix.Translation((0, 0, 0.42 + Z_SHIFT)),
)
apply_auto_smooth_bmesh(bm_chisel, angle_deg=35.0)
mesh_chisel = bpy.data.meshes.new("Breaker_Moil_Chisel")
bm_chisel.to_mesh(mesh_chisel)
bm_chisel.free()
obj_chisel = bpy.data.objects.new("Breaker_Moil_Chisel", mesh_chisel)
obj_chisel.location = (HX, 0.0, 0.0)
link_obj(obj_chisel, col_breaker, mat=mat_dark, parent=breaker_pivot)
Z_CHISEL_TIP = 0.31 + Z_SHIFT  # = 0.49 m

# ==============================================================================
# 8. COLLECTION 04: CONTINUOUS HOOKED HYDRAULIC HOSES & STEEL HARDLINES
# ==============================================================================
# Lower boom bulkhead junction blocks (bridges Turret_Manifold_Hoses -> Boom_Spine_Lines cleanly)
make_box("Boom_Bulkhead_Block", (0.48, 0.0, 2.94), (0.14, 0.48, 0.11), col_hoses, rot=(0, math.radians(-52), 0), mat=mat_dark, parent=boom_pivot, bevel=0.006)

# 8a. Flexible manifold hoses (Turret valve block -> Boom bulkhead block) with HOOK modifiers
turret_hose_targets = [
    (-0.15, -0.225),
    (-0.05, -0.175),
    ( 0.05,  0.175),
    ( 0.15,  0.225),
]
for i, (y_val, y_bm) in enumerate(turret_hose_targets):
    pts = [
        (-0.62, y_val, 2.12),
        (-0.66, y_val * 1.15, 2.52 + (i % 2) * 0.06),
        (-0.32, (y_val + y_bm) * 0.55, 2.74 + (i % 2) * 0.05),
        ( 0.08, y_bm * 0.90, 2.66),
        ( 0.46, y_bm, 2.95),
    ]
    make_fitting(f"Boom_Entry_Fitting_{i+1}", (0.46, y_bm, 2.95), col_hoses, rot=(0, math.radians(38), 0), radius=0.025, length=0.07, parent=boom_pivot)
    make_hose(
        f"Turret_Manifold_Hose_{i+1}", pts, 0.021, col_hoses,
        parent=turret_pivot,
        hooks=[(turret_pivot, [0, 1]), (boom_pivot, [3, 4])],
    )

# 8b. Rigid steel hardlines along main boom + elbow jumper hoses + dipper steel hardlines
for side, y_sign in [("L", 1.0), ("R", -1.0)]:
    y_outer = y_sign * 0.225
    y_inner = y_sign * 0.175

    # Outer hardline: Boom -> Elbow jumper -> Dipper hardline -> Breaker feed hose
    boom_line_pts = [
        (0.46, y_outer, 2.95),
        (0.95, y_outer, 3.66),
        (1.52, y_outer, 4.24),
        (2.35, y_outer, 4.56),
        (3.40, y_outer, 4.81),
        (4.24, y_outer, 4.98),
    ]
    make_hose(f"Boom_Spine_Line_{side}", boom_line_pts, 0.019, col_hoses, mat=mat_machined, parent=boom_pivot)

    # Inner hardline: feeds dipper cylinder / auxiliary circuit cleanly to boom mid-elbow
    boom_aux_pts = [
        (0.46, y_inner, 2.95),
        (0.95, y_inner, 3.70),
        (1.48, y_inner, 4.28),
        (1.86, y_inner, 4.56),
    ]
    make_hose(f"Boom_Aux_Line_{side}", boom_aux_pts, 0.016, col_hoses, mat=mat_machined, parent=boom_pivot)

    for cx, cz in [(1.15, 3.88), (2.45, 4.58), (3.65, 4.86)]:
        make_box(f"Boom_Hose_Clamp_{side}_{cx:.1f}", (cx, y_outer, cz), (0.08, 0.06, 0.09), col_hoses, mat=mat_dark, parent=boom_pivot, bevel=0.004)

    # Bulkhead fittings at end of Boom_Spine_Line and start of Dipper_Hardline
    make_fitting(f"Boom_Elbow_Fitting_{side}", (4.24, y_outer, 4.98), col_hoses, rot=(0, math.radians(78), 0), radius=0.026, length=0.07, parent=boom_pivot)
    make_fitting(f"Dipper_Entry_Fitting_{side}", (5.36, y_sign * 0.185, 4.46), col_hoses, rot=(0, math.radians(122), 0), radius=0.026, length=0.07, parent=dipper_pivot)

    # Flexible Elbow Jumper Hose hooked across Boom_Pivot -> Dipper_Pivot
    elbow_pts = [
        (4.24, y_outer, 4.98),
        (4.58, y_outer * 1.12, 5.18),
        (4.92, y_outer * 1.14, 4.90),
        (5.16, y_sign * 0.20, 4.64),
        (5.36, y_sign * 0.185, 4.46),
    ]
    make_hose(
        f"Elbow_Jumper_Hose_{side}", elbow_pts, 0.021, col_hoses,
        parent=boom_pivot,
        hooks=[(boom_pivot, [0, 1]), (dipper_pivot, [3, 4])],
    )

    # Rigid Steel Hardline along Dipper Arm (closes the old gap cleanly!)
    dipper_hardline_pts = [
        (5.36, y_sign * 0.185, 4.46),
        (5.85, y_sign * 0.175, 4.16),
        (6.32, y_sign * 0.165, 3.86),
    ]
    make_hose(f"Dipper_Hardline_{side}", dipper_hardline_pts, 0.019, col_hoses, mat=mat_machined, parent=dipper_pivot)
    make_box(f"Dipper_Clamp_{side}", (5.85, y_sign * 0.175, 4.16), (0.07, 0.055, 0.08), col_hoses, rot=(0, math.radians(31), 0), mat=mat_dark, parent=dipper_pivot, bevel=0.004)
    make_fitting(f"Dipper_Exit_Fitting_{side}", (6.32, y_sign * 0.165, 3.86), col_hoses, rot=(0, math.radians(122), 0), radius=0.026, length=0.07, parent=dipper_pivot)

# 8c. Flexible Breaker Feed Hoses (Dipper hardline exit -> Breaker swivel ports) hooked across Dipper -> Breaker
for idx, (y_dip, y_port, dip_drop) in enumerate([(0.165, 0.11, 2.26), (-0.165, -0.11, 2.38)]):
    breaker_hose_pts = [
        (6.32, y_dip, 3.86),
        (6.24, y_dip * 1.08, 3.12),
        (6.14, y_dip * 0.96, dip_drop),
        (6.54, y_port, dip_drop - 0.18),
        (6.95, y_port, Z_BREAKER_PORT - 0.05),
        (HX - 0.30, y_port, Z_BREAKER_PORT),
    ]
    make_hose(
        f"Breaker_Feed_Hose_{idx+1}", breaker_hose_pts, 0.023, col_hoses,
        parent=dipper_pivot,
        hooks=[(dipper_pivot, [0, 1]), (breaker_pivot, [4, 5])],
    )

# ==============================================================================
# 9. COLLECTION 05: UNDERGROUND MINE TIP / GRIZZLY BAY INSTALLATION
# ==============================================================================
mine_root = make_empty("Mine_Tip_Environment", (0, 0, 0), col_mine, size=0.4)

# Unified seamless concrete tipping deck slab with rectangular ore-pass cutout (no slab seams!)
def make_deck_with_opening(name, x_min, x_max, y_min, y_max, ox_min, ox_max, oy_min, oy_max, z_bot, z_top, col, mat, parent):
    bm = bmesh.new()
    outer_pts = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
    inner_pts = [(ox_min, oy_min), (ox_max, oy_min), (ox_max, oy_max), (ox_min, oy_max)]

    ob = [bm.verts.new((x, y, z_bot)) for (x, y) in outer_pts]
    ot = [bm.verts.new((x, y, z_top)) for (x, y) in outer_pts]
    ib = [bm.verts.new((x, y, z_bot)) for (x, y) in inner_pts]
    it = [bm.verts.new((x, y, z_top)) for (x, y) in inner_pts]

    for i in range(4):
        j = (i + 1) % 4
        # Top annular quads
        bm.faces.new([ot[i], ot[j], it[j], it[i]])
        # Bottom annular quads
        bm.faces.new([ib[i], ib[j], ob[j], ob[i]])
        # Outer perimeter walls
        bm.faces.new([ob[i], ob[j], ot[j], ot[i]])
        # Inner ore-pass cutout walls
        bm.faces.new([it[i], it[j], ib[j], ib[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    return link_obj(obj, col, mat=mat, parent=parent, bevel=0.025)

make_deck_with_opening(
    "Tip_Deck_Concrete_Slab",
    x_min=-1.50, x_max=12.00, y_min=-3.80, y_max=3.80,
    ox_min=5.00, ox_max=9.00, oy_min=-2.00, oy_max=2.00,
    z_bot=-0.50, z_top=0.00,
    col=col_mine, mat=mat_concrete, parent=mine_root,
)

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

# Detailed safety bollards (base flange + hazard collar + dome cap) + safety chains
bollard_coords = [(3.8, -2.2), (3.8, 2.2), (4.8, -2.35), (4.8, 2.35), (9.2, -2.35), (9.2, 2.35)]
for bx, by in bollard_coords:
    make_box(f"Bollard_Base_{bx}_{by}", (bx, by, 0.015), (0.28, 0.28, 0.03), col_mine, mat=mat_dark, parent=mine_root, bevel=0.005)
    make_cyl(f"Safety_Bollard_{bx}_{by}", (bx, by, 0.52), 0.082, 1.00, col_mine, verts=20, mat=mat_yellow, parent=mine_root, bevel=0.008)
    make_cyl(f"Bollard_Band_{bx}_{by}", (bx, by, 0.78), 0.085, 0.14, col_mine, verts=20, mat=mat_hazard_black, parent=mine_root)
    make_cyl(f"Bollard_Cap_{bx}_{by}",  (bx, by, 1.03), 0.086, 0.04, col_mine, verts=20, mat=mat_dark, parent=mine_root, bevel=0.012)

for chain_idx, (p1, p2) in enumerate([
    ((3.8, -2.2), (4.8, -2.35)),
    ((4.8, -2.35), (9.2, -2.35)),
    ((3.8,  2.2), (4.8,  2.35)),
    ((4.8,  2.35), (9.2,  2.35)),
]):
    mid_x = 0.5 * (p1[0] + p2[0])
    mid_y = 0.5 * (p1[1] + p2[1])
    sag = 0.16 if abs(p2[0] - p1[0]) > 2.0 else 0.07
    chain_pts = [
        (p1[0], p1[1], 0.90),
        (0.75 * p1[0] + 0.25 * p2[0], 0.75 * p1[1] + 0.25 * p2[1], 0.90 - sag * 0.75),
        (mid_x, mid_y, 0.90 - sag),
        (0.25 * p1[0] + 0.75 * p2[0], 0.25 * p1[1] + 0.75 * p2[1], 0.90 - sag * 0.75),
        (p2[0], p2[1], 0.90),
    ]
    make_hose(f"Safety_Chain_{chain_idx+1}", chain_pts, 0.012, col_mine, mat=mat_yellow, parent=mine_root)

# Fractured oversize ore boulders seated cleanly ON TOP of the grizzly bars (zero bar clipping!)
def make_ore_boulder(name, xy_loc, scale, seed, z_floor=Z_GRIZZLY_TOP, seat_depth=0.012, target_top_z=None):
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)

    # Generate directional cleavage planes for angular fractured rock
    planes = []
    for _ in range(9):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        planes.append((d, rng.uniform(0.55, 0.92), rng.uniform(0.18, 0.36)))

    rot_m = Euler((rng.uniform(0, 3.14), rng.uniform(0, 3.14), rng.uniform(0, 3.14)), 'XYZ').to_matrix()

    for v in bm.verts:
        p = v.co.copy()
        for d, cut, strength in planes:
            proj = p.dot(d)
            if proj > cut:
                p -= d * (proj - cut) * strength
        # Fine angular crag variation
        jitter = 1.0 + 0.08 * math.sin(p.x * 7.3 + seed) * math.cos(p.y * 6.1 - seed) + rng.uniform(-0.04, 0.04)
        p *= jitter
        p = rot_m @ p
        v.co = Vector((p.x * scale[0], p.y * scale[1], p.z * scale[2]))

    # Flatten underside slightly so boulder rests naturally across grizzly bars
    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)
    h = max_z - min_z
    for v in bm.verts:
        if v.co.z < min_z + h * 0.14:
            v.co.z = min_z + (v.co.z - min_z) * 0.35

    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)

    # Optionally scale Z so boulder top meets chisel tip exactly
    if target_top_z is not None:
        desired_h = max(0.22, target_top_z - (z_floor - seat_depth))
        cur_h = max(0.01, max_z - min_z)
        z_mul = desired_h / cur_h
        for v in bm.verts:
            v.co.z = (v.co.z - min_z) * z_mul
        min_z = 0.0
    else:
        for v in bm.verts:
            v.co.z -= min_z
        min_z = 0.0

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Keep fractured ore flat-shaded for crisp rock cleavage facets
    for f in bm.faces:
        f.smooth = False

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector((xy_loc[0], xy_loc[1], z_floor - seat_depth))
    return link_obj(obj, col_mine, mat=mat_ore, parent=mine_root)

make_ore_boulder("Oversize_Boulder_Target", (HX, 0.02),    (0.50, 0.46, 0.34), seed=42,  target_top_z=Z_CHISEL_TIP + 0.015)
make_ore_boulder("Oversize_Boulder_2",      (6.30, -0.82), (0.42, 0.36, 0.28), seed=17)
make_ore_boulder("Oversize_Boulder_3",      (7.92,  0.96), (0.45, 0.35, 0.26), seed=89)
make_ore_boulder("Oversize_Boulder_4",      (6.68,  1.15), (0.35, 0.30, 0.22), seed=103)

# ==============================================================================
# 10. COLLECTION 06: UNDERGROUND MINE BAY (SHOTCRETE DRIFT, ROCK BOLTS & HPU)
# ==============================================================================
bay_root = make_empty("Underground_Mine_Bay_Root", (0, 0, 0), col_bay, size=0.45)

def rock_noise(x, y, z):
    """Deterministic multi-octave blasted-rock surface displacement (meters)."""
    n1 = math.sin(x * 0.72 + y * 0.55) * math.cos(z * 0.68 - x * 0.31)
    n2 = math.sin(x * 1.95 - z * 1.45 + 1.1) * math.cos(y * 1.75 + x * 0.85)
    n3 = math.cos(x * 3.70 + y * 3.10 - z * 2.90)
    return 0.18 * n1 + 0.08 * n2 + 0.035 * n3

def arch_profile_point(theta):
    """
    Cross-section profile of the cutaway underground rock-breaker chamber in YZ.
    theta in [0.0, 1.0]:
      0.0 -> floor at +Y back wall (y = +4.15, z = -0.50)
      0.38 -> upper +Y shoulder (y = +4.15, z = 4.20)
      0.78 -> vaulted crown (y = 0.2, z = 7.45)
      1.0 -> cutaway front eyebrow (y = -3.65, z = 6.55) clearing Main_Camera sightline
    """
    if theta <= 0.38:
        t = theta / 0.38
        y = 4.15
        z = -0.50 + t * 4.70
        ny, nz = -1.0, 0.0
    else:
        t = (theta - 0.38) / 0.62
        ang = t * math.radians(122.0)  # 0 deg (+Y shoulder) -> 122 deg (-Y cutaway brow)
        ry = 4.15
        rz = 3.25
        y = ry * math.cos(ang)
        z = 4.20 + rz * math.sin(ang)
        ny = -math.cos(ang)
        nz = -math.sin(ang)
    return y, z, ny, nz

# 10a. Sculpted Cutaway Shotcrete Excavation Shell (back wall + vaulted roof)
def build_shotcrete_cavern():
    bm = bmesh.new()
    nx = 32
    nt = 22
    x_start, x_end = -2.40, 12.20
    shell_thick = 0.45

    inner_grid = []
    outer_grid = []
    for ix in range(nx + 1):
        x = x_start + (x_end - x_start) * (ix / nx)
        in_row = []
        out_row = []
        for it in range(nt + 1):
            theta = it / nt
            y, z, ny, nz = arch_profile_point(theta)
            # Taper rock roughness gently near the cutaway lip so it looks cleanly excavated
            edge_fade = min(1.0, (1.0 - theta) * 8.0)
            disp = rock_noise(x, y, z) * edge_fade
            xi = x
            yi = y + ny * disp
            zi = z + nz * disp
            in_row.append(bm.verts.new((xi, yi, zi)))
            out_row.append(bm.verts.new((xi, yi - ny * shell_thick, zi - nz * shell_thick)))
        inner_grid.append(in_row)
        outer_grid.append(out_row)

    for ix in range(nx):
        for it in range(nt):
            bm.faces.new([inner_grid[ix][it], inner_grid[ix+1][it], inner_grid[ix+1][it+1], inner_grid[ix][it+1]])
            bm.faces.new([outer_grid[ix][it+1], outer_grid[ix+1][it+1], outer_grid[ix+1][it], outer_grid[ix][it]])

    # Cap front cutaway brow & bottom edge & X end lips
    for ix in range(nx):
        bm.faces.new([inner_grid[ix][nt], inner_grid[ix+1][nt], outer_grid[ix+1][nt], outer_grid[ix][nt]])
        bm.faces.new([outer_grid[ix][0], outer_grid[ix+1][0], inner_grid[ix+1][0], inner_grid[ix][0]])
    for it in range(nt):
        bm.faces.new([inner_grid[0][it], inner_grid[0][it+1], outer_grid[0][it+1], outer_grid[0][it]])
        bm.faces.new([outer_grid[nx][it], outer_grid[nx][it+1], inner_grid[nx][it+1], inner_grid[nx][it]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    apply_auto_smooth_bmesh(bm, angle_deg=55.0)
    mesh = bpy.data.meshes.new("Mine_Cavern_Shotcrete")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Mine_Cavern_Shotcrete", mesh)
    return link_obj(obj, col_bay, mat=mat_shotcrete, parent=bay_root)

build_shotcrete_cavern()

# 10b. Rear Rock Bulkhead Wall behind Pedestal (x = -2.35)
def build_rear_bulkhead():
    bm = bmesh.new()
    ny_seg, nz_seg = 14, 14
    y_min, y_max = -3.80, 4.30
    z_min, z_max = -0.50, 7.60
    x_face = -2.30
    grid_f = []
    grid_b = []
    for iy in range(ny_seg + 1):
        y = y_min + (y_max - y_min) * (iy / ny_seg)
        rf, rb = [], []
        for iz in range(nz_seg + 1):
            z = z_min + (z_max - z_min) * (iz / nz_seg)
            # Clip top curve smoothly to cavern arch height
            max_z = 4.20 + 3.35 * math.sqrt(max(0.0, 1.0 - (y / 4.35) ** 2))
            zc = min(z, max_z)
            disp = rock_noise(x_face, y, zc)
            rf.append(bm.verts.new((x_face + disp, y, zc)))
            rb.append(bm.verts.new((x_face - 0.50, y, zc)))
        grid_f.append(rf)
        grid_b.append(rb)
    for iy in range(ny_seg):
        for iz in range(nz_seg):
            bm.faces.new([grid_f[iy][iz], grid_f[iy+1][iz], grid_f[iy+1][iz+1], grid_f[iy][iz+1]])
            bm.faces.new([grid_b[iy][iz+1], grid_b[iy+1][iz+1], grid_b[iy+1][iz], grid_b[iy][iz]])
    for iz in range(nz_seg):
        bm.faces.new([grid_b[0][iz], grid_f[0][iz], grid_f[0][iz+1], grid_b[0][iz+1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    apply_auto_smooth_bmesh(bm, angle_deg=55.0)
    mesh = bpy.data.meshes.new("Mine_Rear_Rock_Bulkhead")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Mine_Rear_Rock_Bulkhead", mesh)
    return link_obj(obj, col_bay, mat=mat_shotcrete, parent=bay_root)

build_rear_bulkhead()

# 10c. LHD Haulage Drift Tunnel Extension on +X side (behind wheel-stop curb)
def build_haulage_drift():
    bm = bmesh.new()
    nx = 12
    nt = 18
    x_start, x_end = 12.00, 19.50
    grid = []
    for ix in range(nx + 1):
        x = x_start + (x_end - x_start) * (ix / nx)
        row = []
        for it in range(nt + 1):
            t = it / nt
            # Horseshoe haulage drift cross-section (width 6.4m, height 5.2m)
            if t < 0.25:
                u = t / 0.25
                y = 3.20
                z = -0.10 + u * 2.80
                ny, nz = -1.0, 0.0
            elif t <= 0.75:
                u = (t - 0.25) / 0.50
                ang = u * math.pi
                y = 3.20 * math.cos(ang)
                z = 2.70 + 2.50 * math.sin(ang)
                ny, nz = -math.cos(ang), -math.sin(ang)
            else:
                u = (t - 0.75) / 0.25
                y = -3.20
                z = 2.70 - u * 2.80
                ny, nz = 1.0, 0.0
            disp = rock_noise(x, y, z) * 0.85
            row.append(bm.verts.new((x, y + ny * disp, z + nz * disp)))
        grid.append(row)

    for ix in range(nx):
        for it in range(nt):
            bm.faces.new([grid[ix][it], grid[ix+1][it], grid[ix+1][it+1], grid[ix][it+1]])

    # Dark back cap deep inside haulage tunnel + floor slab extension
    cap_verts = grid[-1]
    bm.faces.new(list(reversed(cap_verts)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    apply_auto_smooth_bmesh(bm, angle_deg=55.0)
    mesh = bpy.data.meshes.new("Haulage_Drift_Tunnel")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Haulage_Drift_Tunnel", mesh)
    link_obj(obj, col_bay, mat=mat_shotcrete, parent=bay_root)

    # Haulage floor roadway extending into the drift
    make_box("Haulage_Roadway_Slab", (15.75, 0.0, -0.25), (7.60, 6.80, 0.50), col_bay, mat=mat_concrete, parent=bay_root, bevel=0.0)
    # Shotcrete brow & side cheeks framing the haulage portal transition (x = 12.1)
    make_box("Haulage_Portal_Brow",   (12.15,  0.00, 6.25), (0.65, 8.60, 2.60), col_bay, mat=mat_shotcrete, parent=bay_root, bevel=0.04)
    make_box("Haulage_Portal_CheekL", (12.15,  3.75, 2.60), (0.65, 1.35, 5.40), col_bay, mat=mat_shotcrete, parent=bay_root, bevel=0.04)
    make_box("Haulage_Portal_CheekR", (12.15, -3.75, 2.60), (0.65, 1.35, 5.40), col_bay, mat=mat_shotcrete, parent=bay_root, bevel=0.04)

build_haulage_drift()

# 10d. Steel Ground-Support Arch Ribs & Staggered Rock Bolts
for r_idx, rx in enumerate([-1.10, 1.80, 4.70, 7.60, 10.50]):
    rib_pts = []
    for it in range(17):
        theta = it / 16.0
        y, z, ny, nz = arch_profile_point(theta)
        rib_pts.append((rx, y + ny * 0.16, z + nz * 0.16))
    make_hose(f"Mine_Arch_Rib_{r_idx+1}", rib_pts, 0.065, col_bay, mat=mat_dark, parent=bay_root)

# Rock bolt plates & protruding bolt tails across shotcrete wall and vault
bm_bolts = bmesh.new()
for ix in range(8):
    bx = -1.6 + ix * 1.85
    for it_idx, theta in enumerate([0.14, 0.28, 0.44, 0.60, 0.76, 0.90]):
        bx_stagger = bx + (0.85 if it_idx % 2 == 1 else 0.0)
        if bx_stagger > 11.6:
            continue
        y, z, ny, nz = arch_profile_point(theta)
        disp = rock_noise(bx_stagger, y, z)
        pos = Vector((bx_stagger, y + ny * (disp + 0.02), z + nz * (disp + 0.02)))
        nrm = Vector((0.0, ny, nz)).normalized()
        q = nrm.to_track_quat('Z', 'X').to_matrix().to_4x4()
        m_plate = Matrix.Translation(pos) @ q @ Matrix.Diagonal((0.18, 0.18, 0.018, 1.0))
        bmesh.ops.create_cube(bm_bolts, size=1.0, matrix=m_plate)
        m_nut = Matrix.Translation(pos + nrm * 0.045) @ q
        bmesh.ops.create_cone(bm_bolts, cap_ends=True, segments=6, radius1=0.026, radius2=0.026, depth=0.08, matrix=m_nut)

apply_auto_smooth_bmesh(bm_bolts, angle_deg=35.0)
mesh_bolts = bpy.data.meshes.new("Mine_Rock_Bolts")
bm_bolts.to_mesh(mesh_bolts)
bm_bolts.free()
obj_bolts = bpy.data.objects.new("Mine_Rock_Bolts", mesh_bolts)
link_obj(obj_bolts, col_bay, mat=mat_machined, parent=bay_root)

# 10e. Suspended Ventilation Duct (Vent Bag) & Mine Services Pipes along +Y Back Wall
vent_x_start, vent_x_end = -2.10, 12.20
vent_y, vent_z = 3.15, 5.55
make_cyl(
    "Mine_Ventilation_Duct",
    ((vent_x_start + vent_x_end) * 0.5, vent_y, vent_z),
    0.42, vent_x_end - vent_x_start, col_bay,
    rot=(0, math.radians(90), 0), verts=28, mat=mat_vent_duct, parent=bay_root,
)
for i in range(11):
    vx = -1.6 + i * 1.35
    # Ribbed coupling ring
    make_cyl(f"Vent_Duct_Ring_{i+1}", (vx, vent_y, vent_z), 0.445, 0.055, col_bay, rot=(0, math.radians(90), 0), verts=28, mat=mat_dark, parent=bay_root)
    # Suspension strap up to roof arch
    make_box(f"Vent_Hanger_{i+1}", (vx, vent_y + 0.08, vent_z + 0.72), (0.04, 0.03, 0.85), col_bay, rot=(math.radians(-14), 0, 0), mat=mat_machined, parent=bay_root, bevel=0.0)

# Compressed air (orange) and mine water (blue) service lines along +Y wall
for p_name, pz, p_mat in [("Mine_Water_Pipe", 2.55, mat_pipe_water), ("Mine_Air_Pipe", 2.95, mat_pipe_air)]:
    make_cyl(p_name, (5.0, 3.72, pz), 0.068, 14.4, col_bay, rot=(0, math.radians(90), 0), verts=20, mat=p_mat, parent=bay_root)
for wx in (-1.2, 1.8, 4.8, 7.8, 10.8):
    make_box(f"Service_Pipe_Bracket_{wx:.1f}", (wx, 3.88, 2.75), (0.09, 0.50, 0.65), col_bay, mat=mat_dark, parent=bay_root, bevel=0.005)

# 10f. Hydraulic Power Unit (HPU) & Electrical Control Cabinet (visible along +Y wall, clear of slew radius)
HPU_X, HPU_Y = 2.45, 2.95
hpu_root = make_empty("HPU_Power_Pack_Assembly", (HPU_X, HPU_Y, 0.0), col_bay, parent=bay_root, size=0.25)

# Heavy steel skid frame
make_box("HPU_Skid_Base", (HPU_X, HPU_Y, 0.07), (1.75, 1.05, 0.14), col_bay, mat=mat_dark, parent=hpu_root, bevel=0.01)
# Main hydraulic oil reservoir tank
make_box("HPU_Oil_Tank", (HPU_X - 0.27, HPU_Y, 0.62), (1.05, 0.86, 0.96), col_bay, mat=mat_hpu_blue, parent=hpu_root, bevel=0.018)
make_box("HPU_Tank_TopPlate", (HPU_X - 0.27, HPU_Y, 1.12), (1.10, 0.90, 0.05), col_bay, mat=mat_dark, parent=hpu_root, bevel=0.008)
make_box("HPU_Oil_SightGlass", (HPU_X - 0.27, HPU_Y - 0.44, 0.65), (0.08, 0.03, 0.42), col_bay, mat=mat_machined, parent=hpu_root, bevel=0.004)
make_cyl("HPU_Breather_Cap", (HPU_X - 0.60, HPU_Y, 1.22), 0.055, 0.14, col_bay, verts=16, mat=mat_dark, parent=hpu_root, bevel=0.006)
make_cyl("HPU_Return_Filter", (HPU_X + 0.03, HPU_Y + 0.17, 1.32), 0.085, 0.34, col_bay, verts=20, mat=mat_dark, parent=hpu_root, bevel=0.008)

# Electric motor + hydraulic pump mounted on right side of skid
make_cyl("HPU_Electric_Motor", (HPU_X + 0.55, HPU_Y, 0.48), 0.24, 0.62, col_bay, rot=(0, math.radians(90), 0), verts=24, mat=mat_hpu_blue, parent=hpu_root, bevel=0.008)
make_box("HPU_Motor_Feet", (HPU_X + 0.55, HPU_Y, 0.21), (0.44, 0.46, 0.14), col_bay, mat=mat_dark, parent=hpu_root, bevel=0.005)
make_box("HPU_Motor_JunctionBox", (HPU_X + 0.55, HPU_Y - 0.17, 0.74), (0.20, 0.16, 0.16), col_bay, mat=mat_dark, parent=hpu_root, bevel=0.006)
make_cyl("HPU_Hydraulic_Pump", (HPU_X + 0.99, HPU_Y, 0.48), 0.13, 0.26, col_bay, rot=(0, math.radians(90), 0), verts=20, mat=mat_machined, parent=hpu_root, bevel=0.006)

# Oil-to-air radiator cooler mounted above motor
make_box("HPU_Oil_Cooler_Housing", (HPU_X + 0.57, HPU_Y, 1.28), (0.58, 0.68, 0.56), col_bay, mat=mat_dark, parent=hpu_root, bevel=0.012)
make_cyl("HPU_Cooler_FanShroud", (HPU_X + 0.57, HPU_Y - 0.35, 1.28), 0.22, 0.06, col_bay, rot=(math.radians(90), 0, 0), verts=24, mat=mat_machined, parent=hpu_root)
# Protective yellow tubular frame over HPU
for fx in (HPU_X - 0.81, HPU_X + 0.81):
    for fy in (HPU_Y - 0.49, HPU_Y + 0.49):
        make_cyl(f"HPU_CagePost_{fx:.2f}_{fy:.2f}", (fx, fy, 0.90), 0.028, 1.56, col_bay, verts=12, mat=mat_yellow, parent=hpu_root)
make_box("HPU_Canopy_Roof", (HPU_X, HPU_Y, 1.70), (1.72, 1.06, 0.05), col_bay, mat=mat_yellow, parent=hpu_root, bevel=0.008)

# Electrical Starter / Remote Control Cabinet next to HPU
CAB_X, CAB_Y = 0.85, 3.05
make_box("Control_Cabinet_Plinth", (CAB_X, CAB_Y, 0.08), (0.86, 0.58, 0.16), col_bay, mat=mat_dark, parent=bay_root, bevel=0.006)
make_box("Control_Cabinet_Body",   (CAB_X, CAB_Y, 0.96), (0.82, 0.52, 1.60), col_bay, mat=mat_cabinet, parent=bay_root, bevel=0.015)
make_box("Control_Cabinet_Hazard", (CAB_X, CAB_Y - 0.265, 1.52), (0.70, 0.015, 0.12), col_bay, mat=mat_yellow, parent=bay_root, bevel=0.003)
make_box("Control_Isolator_Handle",(CAB_X + 0.27, CAB_Y - 0.28, 1.12), (0.06, 0.07, 0.16), col_bay, mat=mat_red, parent=bay_root, bevel=0.004)
make_cyl("Control_LED_Run",        (CAB_X - 0.19, CAB_Y - 0.27, 1.32), 0.025, 0.03, col_bay, rot=(math.radians(90), 0, 0), verts=16, mat=mat_led_green, parent=bay_root)
make_cyl("Control_LED_Stop",       (CAB_X - 0.09, CAB_Y - 0.27, 1.32), 0.025, 0.03, col_bay, rot=(math.radians(90), 0, 0), verts=16, mat=mat_led_red, parent=bay_root)

# Armored hydraulic & power umbilical running cleanly from HPU along deck into Pedestal Base
for c_idx, dy in enumerate([-0.06, 0.06]):
    umb_pts = [
        (HPU_X - 0.84, HPU_Y - 0.20 + dy, 0.30),
        (HPU_X - 1.15, HPU_Y - 0.70 + dy, 0.06),
        (0.40,         1.65 + dy,         0.06),
        (-0.35 + dy,   1.05,              0.08),
        (-0.46 + dy,   0.42,              0.98),
    ]
    make_hose(f"HPU_Supply_Conduit_{c_idx+1}", umb_pts, 0.034, col_bay, mat=mat_hose, parent=bay_root)

# 10g. Overhead Underground High-Bay LED Floodlight Fixtures
lamp_xs = [1.20, 5.20, 9.20]
for l_idx, lx in enumerate(lamp_xs):
    ly, lz = 1.65, 6.55
    make_cyl(f"Mine_Lamp_DropRod_{l_idx+1}", (lx, ly, lz + 0.38), 0.022, 0.72, col_bay, verts=12, mat=mat_dark, parent=bay_root)
    make_box(f"Mine_Lamp_Body_{l_idx+1}",    (lx, ly, lz), (0.68, 0.42, 0.14), col_bay, rot=(math.radians(14), 0, 0), mat=mat_dark, parent=bay_root, bevel=0.01)
    make_box(f"Mine_Lamp_Lens_{l_idx+1}",    (lx, ly - 0.02, lz - 0.075), (0.58, 0.34, 0.025), col_bay, rot=(math.radians(14), 0, 0), mat=mat_lamp_glow, parent=bay_root, bevel=0.004)

# ==============================================================================
# 11. UNDERGROUND MINE WORLD, INTERIOR LIGHTING & FULL-RIG CAMERA FRAMING
# ==============================================================================
scene = bpy.context.scene
if not scene.world:
    scene.world = bpy.data.worlds.new("Mine_World")
world = scene.world
if bpy.app.version < (5, 0, 0):
    world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()
w_out = wnodes.new("ShaderNodeOutputWorld")
w_bg  = wnodes.new("ShaderNodeBackground")
w_tex = wnodes.new("ShaderNodeTexCoord")
w_sep = wnodes.new("ShaderNodeSeparateXYZ")
w_ramp = wnodes.new("ShaderNodeValToRGB")
w_ramp.color_ramp.elements[0].position = 0.0
w_ramp.color_ramp.elements[0].color = (0.015, 0.017, 0.022, 1.0)
w_ramp.color_ramp.elements[1].position = 0.70
w_ramp.color_ramp.elements[1].color = (0.075, 0.088, 0.112, 1.0)
w_bg.inputs["Strength"].default_value = 0.65
wlinks.new(w_tex.outputs["Generated"], w_sep.inputs["Vector"])
wlinks.new(w_sep.outputs["Z"], w_ramp.inputs["Fac"])
wlinks.new(w_ramp.outputs["Color"], w_bg.inputs["Color"])
wlinks.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

def add_area_light(name, loc, target, energy, size, color=(1.0, 1.0, 1.0)):
    ldata = bpy.data.lights.new(name=name, type='AREA')
    ldata.energy = energy
    ldata.size = size
    ldata.color = color
    lobj = bpy.data.objects.new(name, ldata)
    lobj.location = Vector(loc)
    lobj.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(lobj)

# Interior overhead high-bay mine floodlights (positioned directly below physical fixtures inside cavern)
add_area_light("Mine_HighBay_Light_1", (1.20, 1.50, 6.25), (1.00, 0.0, 1.80), energy=1400, size=1.4, color=(1.0, 0.94, 0.84))
add_area_light("Mine_HighBay_Light_2", (5.20, 1.50, 6.25), (4.60, 0.0, 2.20), energy=1800, size=1.6, color=(1.0, 0.95, 0.86))
add_area_light("Mine_HighBay_Light_3", (9.20, 1.50, 6.25), (7.60, 0.0, 1.20), energy=1500, size=1.4, color=(1.0, 0.94, 0.84))
# Subtle cool spill from the receding LHD haulage drift + cutaway front fill for metallic readability
add_area_light("Haulage_Drift_Backlight", (14.5, 0.0, 3.6), (7.5, 0.0, 1.8), energy=950,  size=2.4, color=(0.70, 0.85, 1.0))
add_area_light("Cutaway_Front_Fill",      (4.4, -7.8, 4.4), (4.5, 0.5, 2.6), energy=550,  size=5.0, color=(0.94, 0.96, 1.0))

cam_data = bpy.data.cameras.new("Main_Camera")
cam_data.lens = 34
cam_obj = bpy.data.objects.new("Main_Camera", cam_data)
cam_obj.location = Vector((4.4, -12.6, 3.6))
cam_obj.rotation_euler = (Vector((4.2, 0.4, 2.75)) - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

bpy.context.view_layer.update()
print("Stationary Underground Rock Breaker, Grizzly Tip & Mine Bay generated cleanly!")
