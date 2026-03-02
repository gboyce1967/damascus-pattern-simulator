import numpy as np

def serialize_layers_mesh(layers):
    out = []
    for layer in layers:
        v = np.asarray(layer.mesh.vertices, dtype=np.float64).reshape(-1, 3)
        t = np.asarray(layer.mesh.triangles, dtype=np.int64).reshape(-1, 3)

        # Flatten for transport (Three.js BufferGeometry)
        out.append({
            "color": [float(layer.color[0]), float(layer.color[1]), float(layer.color[2])],
            "vertices": v.flatten().astype(float).tolist(),
            "triangles": t.flatten().astype(int).tolist()
        })
    return out
