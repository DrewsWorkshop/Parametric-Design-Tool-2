from panda3d.core import Geom, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, Material

######## GLOBAL VARIABLES

# Printer Default
overhangAngle = 50.0

# Object Details
objectHeight = 7.0 #inches

#Geometry Resolution
segments = 50 #number of segments around the circumference
height_segments = 40 #number of segments along the height



def stoolGeometry(segment_count=16, object_width=1.0, twist_angle=0.0, 
                           twist_groove_depth=1.0, vertical_wave_freq=3.0, 
                           vertical_wave_depth=1.0, wall_thickness=0.5, 
                           max_overhang_angle=overhangAngle) -> Geom:

    """Build a modulated pipe geometry with inner and outer surface variations.
    
    Args:
        radius: Base radius of the cylinder
        height: Height of the cylinder (extends from -height/2 to +height/2)
        segments: Number of segments around the circumference
        height_segments: Number of segments along the height
        segment_count: Number of segments for twist grooves
        object_width: Base width of the object (outer radius)
        twist_angle: Amount of twist applied
        twist_groove_depth: Depth of the twist grooves
        vertical_wave_freq: Frequency of vertical waves
        vertical_wave_depth: Depth of vertical waves
        wall_thickness: Thickness of the pipe wall (offset between inner and outer radius)
    """
    
    import math

    ObjectType = "Stool"


    height=objectHeight
    # Hardcoded top thickness (simple constant)
    top_thickness = 0.2
    # Toggle to preview only the top geometry
    show_top_only = False
    # Fine-grained debug toggles
    show_top_outer = True
    show_top_inner = True
    show_outer_surface = True
    show_inner_surface = True
    # Now the side connecting wall is at the bottom band
    show_side_connect_walls = True
    
    vformat = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData("stool_modulated_vn", vformat, Geom.UHStatic)

    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")
    cwriter = GeomVertexWriter(vdata, "color")

    indices = []
    half_height = height / 2.0
    
    # Track vertex colors based on overhang angle
    vertex_colors = {}  # vertex_idx -> (r, g, b, a)

    def add_vertex(x, y, z, nx, ny, nz, r=1.0, g=1.0, b=1.0, a=1.0):
        """Helper to add a vertex with its normal and color."""
        vwriter.addData3f(x, y, z)
        nwriter.addData3f(nx, ny, nz)
        cwriter.addData4f(r, g, b, a)
        vertex_idx = vwriter.getWriteRow() - 1
        
        # Check if this vertex should be red (will be updated later)
        return vertex_idx

    def get_surface_modulation(phi, length_ratio):
        """Surface modulation function converted from C#."""
        phi += twist_angle * 0.067 * math.pi * length_ratio
        modulated_radius = object_width + (twist_groove_depth * 0.06) * math.cos(segment_count * phi) + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        return modulated_radius

    def get_inner_surface_modulation(phi, length_ratio):
        """Inner surface modulation function with wall thickness offset."""
        phi += twist_angle * 0.067 * math.pi * length_ratio
        modulated_radius = (object_width - wall_thickness) + (twist_groove_depth * 0.06) * math.cos(segment_count * phi) + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        return modulated_radius

    # Generate vertices for top faces (stool top)
    # Top face - outer ring (normals up)
    top_outer_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        top_radius = get_surface_modulation(angle, 1.0)  # Top face
        top_v = add_vertex(top_radius * math.cos(angle), top_radius * math.sin(angle), half_height, 0, 0, 1)
        top_outer_vertices.append(top_v)
    
    # Top face - inner ring (normals down for interior top)
    top_inner_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        top_inner_radius = get_inner_surface_modulation(angle, 1.0)  # Top face
        top_v = add_vertex(top_inner_radius * math.cos(angle), top_inner_radius * math.sin(angle), half_height, 0, 0, -1)
        top_inner_vertices.append(top_v)

    # Create top faces as triangle fans to center (solid top)
    # Outer top (faces upward)
    if show_top_outer:
        top_center_outer = add_vertex(0.0, 0.0, half_height, 0, 0, 1)
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((top_center_outer, top_outer_vertices[i], top_outer_vertices[next_i]))

        # Inner top (faces downward inside the stool) at lowered Z to create thickness
    inner_top_bottom_ring = []
    inner_z_bottom = half_height - top_thickness
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        r = get_inner_surface_modulation(angle, 1.0)
        v = add_vertex(r * math.cos(angle), r * math.sin(angle), inner_z_bottom, 0, 0, -1)
        inner_top_bottom_ring.append(v)

    if show_top_inner:
        top_center_inner = add_vertex(0.0, 0.0, inner_z_bottom, 0, 0, -1)
        for i in range(segments):
            next_i = (i + 1) % segments
            # Flip winding so the inner top faces the intended direction
            indices.append((top_center_inner, inner_top_bottom_ring[next_i], inner_top_bottom_ring[i]))

    # (No inner vertical wall; bottom remains open like the vase top)
    
    # Create side walls with height segments
    if not show_top_only:
        for h in range(height_segments):
            z1 = half_height - (height * h) / height_segments
            z2 = half_height - (height * (h + 1)) / height_segments
            length_ratio1 = 1.0 - (h / height_segments)
            length_ratio2 = 1.0 - ((h + 1) / height_segments)
            
            # Store vertices for this height level
            outer_upper_vertices = []
            outer_lower_vertices = []
            inner_upper_vertices = []
            inner_lower_vertices = []
            
            for i in range(segments):
                angle = (2.0 * math.pi * i) / segments
                
                # Get modulated radii for outer surface
                outer_radius_upper = get_surface_modulation(angle, length_ratio1)
                outer_radius_lower = get_surface_modulation(angle, length_ratio2)
                
                # Get modulated radii for inner surface
                inner_radius_upper = get_inner_surface_modulation(angle, length_ratio1)
                inner_radius_lower = get_inner_surface_modulation(angle, length_ratio2)
                
                # Calculate approximate normals
                nx = math.cos(angle)
                ny = math.sin(angle)
                
                # Add outer surface vertices
                outer_upper_v = add_vertex(outer_radius_upper * math.cos(angle), outer_radius_upper * math.sin(angle), z1, nx, ny, 0)
                outer_lower_v = add_vertex(outer_radius_lower * math.cos(angle), outer_radius_lower * math.sin(angle), z2, nx, ny, 0)
                outer_upper_vertices.append(outer_upper_v)
                outer_lower_vertices.append(outer_lower_v)
                
                # Add inner surface vertices (inverted normals)
                # Weld the top of the inner wall to the inner top disk ring for the topmost band
                if h == 0:
                    inner_upper_v = inner_top_bottom_ring[i]
                else:
                    inner_upper_v = add_vertex(inner_radius_upper * math.cos(angle), inner_radius_upper * math.sin(angle), z1, -nx, -ny, 0)
                inner_lower_v = add_vertex(inner_radius_lower * math.cos(angle), inner_radius_lower * math.sin(angle), z2, -nx, -ny, 0)
                inner_upper_vertices.append(inner_upper_v)
                inner_lower_vertices.append(inner_lower_v)
            
            # Create outer surface quads
            if show_outer_surface:
                for i in range(segments):
                    next_i = (i + 1) % segments
                    
                    # Calculate overhang angle for this face
                    angle1 = (2.0 * math.pi * i) / segments
                    angle2 = (2.0 * math.pi * next_i) / segments
                    
                    r1_upper = get_surface_modulation(angle1, length_ratio1)
                    r1_lower = get_surface_modulation(angle1, length_ratio2)
                    r2_lower = get_surface_modulation(angle2, length_ratio2)
                    
                    v0 = (r1_upper * math.cos(angle1), r1_upper * math.sin(angle1), z1)
                    v1 = (r1_lower * math.cos(angle1), r1_lower * math.sin(angle1), z2)
                    v2 = (r2_lower * math.cos(angle2), r2_lower * math.sin(angle2), z2)
                    
                    # Calculate face normal
                    e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
                    e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
                    cross = (e1[1]*e2[2] - e1[2]*e2[1], e1[2]*e2[0] - e1[0]*e2[2], e1[0]*e2[1] - e1[1]*e2[0])
                    cross_len = math.sqrt(cross[0]*cross[0] + cross[1]*cross[1] + cross[2]*cross[2])
                    
                    # Calculate overhang angle and create gradient color
                    if cross_len > 1e-9:
                        nz = cross[2] / cross_len
                        # Convert to overhang angle (negative = overhang, positive = no overhang)
                        angle_deg = (90.0 - math.degrees(math.acos(max(-1, min(1, nz)))))
                        
                        # Create gradient based on max overhang angle
                        # Yellow starts 5 degrees before max overhang
                        yellow_start = max_overhang_angle - 5
                        
                        # Clamp angle between 0 and max overhang degrees
                        clamped_angle = max(-max_overhang_angle, min(0.0, angle_deg))
                        abs_angle = abs(clamped_angle)
                        
                        # Create gradient color
                        if abs_angle < yellow_start:  # Below yellow start: white
                            r = 1.0
                            g = 1.0
                            b = 1.0
                        elif abs_angle < max_overhang_angle:  # Yellow start to max: yellow to red
                            t = (abs_angle - yellow_start) / (max_overhang_angle - yellow_start)  # Full transition range
                            r = 1.0
                            g = 1.0 - t  # Start at yellow (1,1,0), end at red (1,0,0)
                            b = 0.0
                        else:  # At max overhang: red
                            r = 1.0
                            g = 0.0
                            b = 0.0
                        
                        # Store color for all vertices of this face
                        face_color = (r, g, b, 1.0)
                        vertex_colors[outer_upper_vertices[i]] = face_color
                        vertex_colors[outer_lower_vertices[i]] = face_color
                        vertex_colors[outer_upper_vertices[next_i]] = face_color
                        vertex_colors[outer_lower_vertices[next_i]] = face_color
                    
                    indices.extend([
                        (outer_upper_vertices[i], outer_lower_vertices[i], outer_lower_vertices[next_i]),
                        (outer_upper_vertices[i], outer_lower_vertices[next_i], outer_upper_vertices[next_i])
                    ])
            
            # Create inner surface quads
            if show_inner_surface:
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([
                        (inner_upper_vertices[i], inner_upper_vertices[next_i], inner_lower_vertices[i]),
                        (inner_lower_vertices[i], inner_upper_vertices[next_i], inner_lower_vertices[next_i])
                    ])
            
            # Create wall faces connecting inner and outer surfaces (only at the very bottom band)
            if show_side_connect_walls and h == height_segments - 1:
                # Use dedicated vertices with downward normals for flat shading on the bottom ring
                wall_outer_bottom = []
                wall_inner_bottom = []
                for i in range(segments):
                    angle = (2.0 * math.pi * i) / segments
                    outer_r = get_surface_modulation(angle, length_ratio2)
                    inner_r = get_inner_surface_modulation(angle, length_ratio2)
                    # create new vertices with consistent normal down (0,0,-1)
                    wall_outer_bottom.append(add_vertex(outer_r * math.cos(angle), outer_r * math.sin(angle), z2, 0, 0, -1))
                    wall_inner_bottom.append(add_vertex(inner_r * math.cos(angle), inner_r * math.sin(angle), z2, 0, 0, -1))
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([
                        (wall_outer_bottom[i], wall_inner_bottom[i], wall_outer_bottom[next_i]),
                        (wall_inner_bottom[i], wall_inner_bottom[next_i], wall_outer_bottom[next_i])
                    ])

    # Create main geometry with vertex colors
    tris = GeomTriangles(Geom.UHStatic)
    for a, b, c in indices:
        tris.addVertices(a, b, c)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    
    # Update vertex colors based on overhang gradient
    for vertex_idx, color in vertex_colors.items():
        cwriter.setRow(vertex_idx)
        cwriter.setData4f(color[0], color[1], color[2], color[3])
    
    # Create simple material
    material = Material()
    material.setDiffuse((0.6, 0.8, 1.0, 1.0))  # Light blue color
    material.setShininess(32.0)
    
    # Check if any overhang exists (any red areas)
    has_overhang = any(color[0] == 1.0 and color[1] == 0.0 and color[2] == 0.0 for color in vertex_colors.values())
    
    return ObjectType, geom, material, has_overhang


def overhangStoolCheck(
    segment_count=16,
    object_width=1.0,
    twist_angle=0.0,
    twist_groove_depth=1.0,
    vertical_wave_freq=3.0,
    vertical_wave_depth=1.0,
    wall_thickness=0.5,
    max_overhang_angle=overhangAngle,
):
    """Lightweight overhang check for the Stool.

    Uses the same sampling resolution and modulation formulas as stoolGeometry,
    but avoids building Panda3D geometry. Returns True if any sampled face
    exceeds the max_overhang_angle threshold.
    """
    import math

    # Match stoolGeometry's internal resolution exactly
    height = 7.0
    top_thickness = 0.2

    half_height = height / 2.0

    def get_surface_modulation(phi, length_ratio):
        phi += twist_angle * 0.067 * math.pi * length_ratio
        return (
            object_width
            + (twist_groove_depth * 0.06) * math.cos(segment_count * phi)
            + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        )

    def get_inner_surface_modulation(phi, length_ratio):
        phi += twist_angle * 0.067 * math.pi * length_ratio
        return (
            (object_width - wall_thickness)
            + (twist_groove_depth * 0.06) * math.cos(segment_count * phi)
            + (vertical_wave_depth * 0.15) * math.cos(vertical_wave_freq * length_ratio)
        )

    # Determine inner top bottom plane (to match thickness treatment)
    inner_z_bottom = half_height - top_thickness

    # Scan side walls only (same region as stoolGeometry outer surface quads)
    for h in range(height_segments):
        z1 = half_height - (height * h) / height_segments
        z2 = half_height - (height * (h + 1)) / height_segments
        length_ratio1 = 1.0 - (h / height_segments)
        length_ratio2 = 1.0 - ((h + 1) / height_segments)

        for i in range(segments):
            next_i = (i + 1) % segments

            angle1 = (2.0 * math.pi * i) / segments
            angle2 = (2.0 * math.pi * next_i) / segments

            r1_upper = get_surface_modulation(angle1, length_ratio1)
            r1_lower = get_surface_modulation(angle1, length_ratio2)
            r2_lower = get_surface_modulation(angle2, length_ratio2)

            v0 = (r1_upper * math.cos(angle1), r1_upper * math.sin(angle1), z1)
            v1 = (r1_lower * math.cos(angle1), r1_lower * math.sin(angle1), z2)
            v2 = (r2_lower * math.cos(angle2), r2_lower * math.sin(angle2), z2)

            # Face normal via cross product
            e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
            cross = (
                e1[1] * e2[2] - e1[2] * e2[1],
                e1[2] * e2[0] - e1[0] * e2[2],
                e1[0] * e2[1] - e1[1] * e2[0],
            )
            cross_len = math.sqrt(cross[0] * cross[0] + cross[1] * cross[1] + cross[2] * cross[2])
            if cross_len <= 1e-9:
                continue

            nz = cross[2] / cross_len
            # Convert to overhang angle (negative = overhang, positive = no overhang), same as geometry
            angle_deg = 90.0 - math.degrees(math.acos(max(-1.0, min(1.0, nz))))

            # If magnitude exceeds threshold on the negative side, it's an overhang
            # Geometry clamps to [-max_overhang, 0] for coloring; here we just check threshold
            if angle_deg <= 0.0 and abs(angle_deg) >= max_overhang_angle:
                return True

    return False
