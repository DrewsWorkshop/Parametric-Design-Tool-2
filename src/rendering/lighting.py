from panda3d.core import AmbientLight, DirectionalLight, Vec4


def setup_lights(render):
    """Setup ambient and directional lighting for the scene with enhanced shadows."""
    
    # Increase ambient light to reduce harsh shadows
    amb = AmbientLight("ambient")
    amb.setColor(Vec4(0.4, 0.4, 0.45, 1))  # Brighter ambient for softer contrast
    amb_np = render.attachNewNode(amb)
    render.setLight(amb_np)

    # Main directional light (sun) for shadows and highlights
    sun = DirectionalLight("sun")
    sun.setColor(Vec4(0.8, 0.8, 0.7, 1))  # Reduced intensity for softer highlights
    sun_np = render.attachNewNode(sun)
    sun_np.setHpr(-45, -45, 0)  # Better angle for shadows
    render.setLight(sun_np)
    
    # Secondary fill light to reduce harsh shadows
    fill = DirectionalLight("fill")
    fill.setColor(Vec4(0.4, 0.4, 0.5, 1))  # Cooler fill light
    fill_np = render.attachNewNode(fill)
    fill_np.setHpr(120, -20, 0)  # Opposite side, softer angle
    render.setLight(fill_np)

    # Enable automatic shader generation
    render.setShaderAuto()
