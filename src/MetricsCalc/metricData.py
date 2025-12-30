from math import inf
from panda3d.core import GeomVertexReader


def compute_bb_from_geom(geom):
    vdata = geom.getVertexData()
    reader = GeomVertexReader(vdata, "vertex")
    min_x = min_y = min_z = inf
    max_x = max_y = max_z = -inf
    while not reader.isAtEnd():
        x, y, z = reader.getData3f()
        if x < min_x:
            min_x = x
        if y < min_y:
            min_y = y
        if z < min_z:
            min_z = z
        if x > max_x:
            max_x = x
        if y > max_y:
            max_y = y
        if z > max_z:
            max_z = z
    
    diameter = max_x - min_x
    height = max_z - min_z
    
    return diameter, height   

from panda3d.core import GeomVertexReader

def compute_volume_from_geom(geom):
    """Returns absolute mesh volume of a watertight triangle mesh."""
    total = 0.0
    vdata = geom.getVertexData()
    vreader = GeomVertexReader(vdata, "vertex")

    for pi in range(geom.getNumPrimitives()):
        prim = geom.getPrimitive(pi).decompose()
        for p in range(prim.getNumPrimitives()):
            start = prim.getPrimitiveStart(p)
            end = prim.getPrimitiveEnd(p)
            i = start
            while i + 2 < end:
                i0 = prim.getVertex(i)
                i1 = prim.getVertex(i + 1)
                i2 = prim.getVertex(i + 2)

                vreader.setRow(i0)
                x0, y0, z0 = vreader.getData3f()
                vreader.setRow(i1)
                x1, y1, z1 = vreader.getData3f()
                vreader.setRow(i2)
                x2, y2, z2 = vreader.getData3f()

                # Signed volume of tetrahedron (0, v0, v1, v2)
                vol6 = (
                    x0 * (y1 * z2 - z1 * y2)
                    - y0 * (x1 * z2 - z1 * x2)
                    + z0 * (x1 * y2 - y1 * x2)
                )
                total += vol6 / 6.0
                i += 3

    return abs(total)



def LCA_data(filament_density = 1.20, volume=1):

    volumeMM3 = volume * 16387.064
    mass = (volumeMM3 * filament_density) / 1000
    
    waterMetric = mass / 9.3767
    toyotaMetric = 0.0023 * mass + 11
    fordMetric = 0.00138 * mass + 6.56

    trashMetric = (waterMetric * 13) / 104

    return mass, waterMetric, toyotaMetric, fordMetric, trashMetric


def computing_metrics(geom):


    diameter, height = compute_bb_from_geom(geom)
    print("Height:", height)
    print("Diameter:",diameter)


    volume = compute_volume_from_geom(geom)
    print("Volume:", volume)

    mass, waterMetric, toyotaMetric, fordMetric, trashMetric = LCA_data(volume)
    print("Mass:", mass)
    print("Water Metric:", waterMetric)
    print("Toyota Metric:", toyotaMetric)
    print("Ford Metric:", fordMetric)
    print("Trash Metric:", trashMetric)







