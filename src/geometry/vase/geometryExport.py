from panda3d.core import Geom, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter



def vaseGeometryExport(segment_count=16, object_width=1.0, twist_angle=0.0, 
                           twist_groove_depth=1.0, vertical_wave_freq=3.0, 
                           vertical_wave_depth=1.0, wall_thickness=0.5) -> Geom:

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

    ObjectType = "Vase"


    height=7.0
    segments=40
    height_segments=40
    # Hardcoded bottom thickness (simple constant)
    bottom_thickness = 0.2
    # Toggle to preview only the bottom geometry
    show_bottom_only = False
    # Fine-grained debug toggles
    show_bottom_outer = True
    show_bottom_inner = True
    show_outer_surface = True
    show_inner_surface = True
    show_side_connect_walls = True
    
    vformat = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("vase_modulated_vn", vformat, Geom.UHStatic)

    vwriter = GeomVertexWriter(vdata, "vertex")
    nwriter = GeomVertexWriter(vdata, "normal")

    indices = []
    half_height = height / 2.0

    def add_vertex(x, y, z, nx, ny, nz):
        """Helper to add a vertex with its normal."""
        vwriter.addData3f(x, y, z)
        nwriter.addData3f(nx, ny, nz)
        return vwriter.getWriteRow() - 1

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

    # Generate vertices for bottom faces (cup bottom)
    # Bottom face - outer ring (normals down)
    bottom_outer_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        bottom_radius = get_surface_modulation(angle, 0.0)  # Bottom face
        bottom_v = add_vertex(bottom_radius * math.cos(angle), bottom_radius * math.sin(angle), -half_height, 0, 0, -1)
        bottom_outer_vertices.append(bottom_v)
    
    # Top face - outer ring (normals up)
    top_outer_vertices = []
    for i in range(segments):
        angle = (2.0 * math.pi * i) / segments
        top_radius = get_surface_modulation(angle, 1.0)  # Top face
        top_v = add_vertex(top_radius * math.cos(angle), top_radius * math.sin(angle), half_height, 0, 0, 1)
        top_outer_vertices.append(top_v)

    # Create bottom faces as triangle fans to center (cup bottom)
    # Outer bottom (faces downward)
    if show_bottom_outer:
        bottom_center_outer = add_vertex(0.0, 0.0, -half_height, 0, 0, -1)
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((bottom_center_outer, bottom_outer_vertices[next_i], bottom_outer_vertices[i]))

    # Top face (faces upward)
    top_center = add_vertex(0.0, 0.0, half_height, 0, 0, 1)
    for i in range(segments):
        next_i = (i + 1) % segments
        indices.append((top_center, top_outer_vertices[i], top_outer_vertices[next_i]))

    # (Inner vertical wall intentionally omitted)
    
    # Create side walls with height segments
    if not show_bottom_only:
        for h in range(height_segments):
            z1 = half_height - (height * h) / height_segments
            z2 = half_height - (height * (h + 1)) / height_segments
            length_ratio1 = 1.0 - (h / height_segments)
            length_ratio2 = 1.0 - ((h + 1) / height_segments)
            
            # Store vertices for this height level
            outer_upper_vertices = []
            outer_lower_vertices = []
            # No inner geometry for export
            
            for i in range(segments):
                angle = (2.0 * math.pi * i) / segments
                
                # Get modulated radii for outer surface
                outer_radius_upper = get_surface_modulation(angle, length_ratio1)
                outer_radius_lower = get_surface_modulation(angle, length_ratio2)
                
                # Calculate approximate normals
                nx = math.cos(angle)
                ny = math.sin(angle)
                
                # Add outer surface vertices
                outer_upper_v = add_vertex(outer_radius_upper * math.cos(angle), outer_radius_upper * math.sin(angle), z1, nx, ny, 0)
                outer_lower_v = add_vertex(outer_radius_lower * math.cos(angle), outer_radius_lower * math.sin(angle), z2, nx, ny, 0)
                outer_upper_vertices.append(outer_upper_v)
                outer_lower_vertices.append(outer_lower_v)
                
                # No inner surface
            
            # Create outer surface quads
            if show_outer_surface:
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([
                        (outer_upper_vertices[i], outer_lower_vertices[i], outer_lower_vertices[next_i]),
                        (outer_upper_vertices[i], outer_lower_vertices[next_i], outer_upper_vertices[next_i])
                    ])
            
            # No inner surface quads
            
            # No inner/outer connecting walls for export

    tris = GeomTriangles(Geom.UHStatic)
    for a, b, c in indices:
        tris.addVertices(a, b, c)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    return ObjectType,geom
