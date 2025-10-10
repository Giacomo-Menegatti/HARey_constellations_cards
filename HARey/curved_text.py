import numpy as np
from matplotlib.text import TextPath
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D

def curved_text(ax, text, r, angle_offset=0.0, font_size=1.0, font_prop=None):
    """ Add a curved text to an axis. r is the radius of curvature at the text center, angle offset the angle of the text center (in RADIANS)"""

    # Create a TextPath object with the text
    text_path = TextPath((0, 0), text, size=font_size, prop=font_prop)
    bb = text_path.get_extents()
    # Center the text path
    text_centered = Affine2D().translate(-0.5 * (bb.x0 + bb.x1), -0.5 * (bb.y0 + bb.y1)).transform_path(text_path)

    # Curve the text vertexes
    verts = text_centered.vertices
    new_verts = np.array([((r+y)*np.sin(x/r + angle_offset), (r+y)*np.cos(x/r + angle_offset)) for (x,y) in verts])
    text_centered.vertices = new_verts

    # Create a PathPatch from the curved text path and add it to the axis
    patch = PathPatch(text_centered, color='black', linewidth=0)
    ax.add_patch(patch)