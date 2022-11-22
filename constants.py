from matplotlib.patches import Rectangle


# (distance_miles, upper_node, lower_node)
PUMPING_NODES = [(30.5, 264, 188144), (38.5, 1397, 189277)]
FAULT_NODES = [(25.5, 34233, 183593), (75.5, 9068, 196948)]

PROP_FILES = {
    'top': 'usgmodel/DISref/qt.top{}.dat',
    'bot': 'usgmodel/DISref/qt.bot{}.dat',
}
RCH_FILE = 'usgmodel/RCHref/rch.nodes.ref'
GHB_FILE = 'usgmodel/xsect3.ghb'

QUADTREE_GRID = 'output_shapes/qt_point.shp'

FIG_DIR = 'figures'

NLAY = 9
COLNUM = 54

COLORS = ['b', 'g', '#aaaaaa']
PROXY = [Rectangle((0, 0), 0, 0, facecolor=c, linewidth=.08) for c in COLORS]
FIG_LABELS = ['Recharge', 'GHB', 'Active']
