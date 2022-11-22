from typing import List, Tuple, Dict

import numpy as np
import os
import arcpy as arc
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

import constants as const

import matplotlib as mpl


mpl.use('Agg')

mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['font.size'] = 10


def float_format(x: float) -> str:
    """
    Formats a floating number for plot labeling
    Args:
        x: input float number

    Returns:
        string representation with one decimal
    """
    return '{:,.1f}'.format(x)


def plot_properties_full_extent(
        patches: List[List[Rectangle], List[Rectangle], List[Rectangle]], dis: Dict[str, np.array], figure_path: str):
    """
    Plot the 3D aquifer properties along the full extent of the cross-section
    Args:
        patches: list of rectangles (grid cells) to be plotted
        dis: discretization dictionary with top/bottom elevations
        figure_path: output figure path
    """
    fig, ax = plt.subplots(figsize = (12, 6))
    fig.suptitle('Cross-Section #3', fontsize=10)
    for i, pl in enumerate(patches):
        patch_collection = PatchCollection(pl)
        patch_collection.set_linewidth(.08)
        patch_collection.set_facecolor(const.COLORS[i])
        patch_collection.set_label(const.FIG_LABELS[i])
        ax.add_collection(patch_collection)
    for well in const.PUMPING_NODES:
        ax.plot((well[0] * 5280, well[0] * 5280), (dis['top'][well[1] - 1], dis['bot'][well[2] - 1]), c='k')
        ax.annotate(
            'Well field', xy=((well[0] - 1.1) * 5280, dis['bot'][well[2] - 1] + 100),
            rotation='vertical', verticalalignment='bottom'
        )
    for fault in const.FAULT_NODES:
        ax.plot((fault[0] * 5280, fault[0] * 5280), (dis['top'][fault[1] - 1], dis['bot'][fault[2] - 1]), c='r')
        ax.annotate(
            'Fault', xy=((fault[0] - 1.1) * 5280, dis['bot'][fault[2] - 1] + 200),
            rotation='vertical', verticalalignment='bottom'
        )
    ax.set_ylim(-10000, 1000)
    ax.yaxis.set_major_formatter(FuncFormatter(float_format))
    ax.set_xlim(0, 83*5280)
    ax.set_xticks(np.linspace(0, 83*5280, 9))
    ax.set_xticklabels([float_format(x) for x in np.linspace(0, 83, 9)])
    ax.set_xlabel('Distance (miles)')
    ax.set_ylabel('Elevation (feet)')
    ax.legend(const.PROXY, const.FIG_LABELS)
    plt.savefig(figure_path, bbox_inches='tight', dpi=300)
    plt.close()


def get_model_arrays(properties_file: str) -> np.array:
    """
    Parse model properties file and return an array. Specifically for unstructured grids,
    the array will be one dimensional (as opposed to structured 3D arrays)
    Args:
        properties_file: path to properties file

    Returns:
        a numpy array containing a specific property (top/bottom elevation, hydraulic conductivity, etc.)
        for every node location
    """
    props = np.empty(0)
    for layer in range(const.NLAY):
        with open(properties_file.format(layer), 'r') as f:
            props = np.concatenate((props, np.array(f.read().split(), dtype='float')))
    return props


def main():
    if not os.path.exists(const.FIG_DIR):
        os.mkdir(const.FIG_DIR)

    dis = {}
    for k, file_path in const.PROP_FILES.items():
        dis[k] = get_model_arrays(file_path)

    rch = dict.fromkeys(np.loadtxt(const.RCH_FILE, dtype='int'))
    ghb = dict.fromkeys(np.loadtxt(const.GHB_FILE, dtype='int', comments='-1', skiprows=2, usecols=(0,)))

    patch_list = [[], [], []]
    for layer in range(const.NLAY):
        sql = '''
            "layer"={} and "col"={} and "child_loca" in ('', '1', '32', '34', '122', '124', '142', '144', '322', 
            '324', '342', '344', '12', '14', '3') 
        '''.format(layer + 1, const.COLNUM)
        grd = arc.da.FeatureClassToNumPyArray(const.QUADTREE_GRID, ['nodenumber', 'SHAPE@XY', 'delr', 'row'], sql)
        nq = grd['nodenumber'].astype('int') - 1
        centroid = grd['SHAPE@XY']
        offset = (grd['row'][0] - 1) * 5280.
        zipped_data = zip(centroid, grd['delr'], dis['top'][nq], dis['bot'][nq], nq)
        dx = offset
        if nq[0] in rch:
            patch_list[0].append([Rectangle((dx, x[3]), x[1], x[2] - x[3]) for x in zipped_data[:1]][0])
        elif nq[0] in ghb:
            patch_list[1].append([Rectangle((dx, x[3]), x[1], x[2] - x[3]) for x in zipped_data[:1]][0])
        else:
            patch_list[2].append([Rectangle((dx, x[3]), x[1], x[2] - x[3]) for x in zipped_data[:1]][0])
        dx += zipped_data[0][1]
        for g in zipped_data[1:]:
            if g[4] in rch:
                patch_list[0].append(Rectangle((dx, g[3]), g[1], g[2] - g[3]))
            elif g[4] in ghb:
                patch_list[1].append(Rectangle((dx, g[3]), g[1], g[2] - g[3]))
            else:
                patch_list[2].append(Rectangle((dx, g[3]), g[1], g[2] - g[3]))
            dx += g[1]
    fig_file_path = '{}/boundary'.format(const.FIG_DIR)
    plot_properties_full_extent(patch_list, dis, fig_file_path)


if __name__ == '__main__':
    main()
