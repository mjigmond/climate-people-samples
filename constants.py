from matplotlib.patches import Rectangle
import os
import numpy as np
from datetime import datetime as dt


NOW = dt.now()

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

user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0'
HEADERS = {
    'User-Agent': user_agent,
}

SNOTEL = {
    'sawtooth': 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/hourly/1251:CO:SNTL%7Cid=%22%22%7Cname/-167,0/WTEQ::value,SNWD::value,PREC::value,TOBS::value',
    'grizzly peak': 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/hourly/505:CO:SNTL%7Cid=%22%22%7Cname/-167,0/WTEQ::value,SNWD::value,PREC::value,TOBS::value',
    'loveland basin': 'https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/hourly/602:CO:SNTL%7Cid=%22%22%7Cname/-167,0/WTEQ::value,SNWD::value,PREC::value,TOBS::value',
}

SMTP = {
    'GMAIL': [
        'smtp.gmail.com',
        os.environ.get('GMAIL_USER'),
        os.environ.get('GMAIL_PASS')
    ],
    'HOTMAIL': [
        'smtp-mail.outlook.com',
        os.environ.get('HMAIL_USER'),
        os.environ.get('HMAIL_PASS')
    ]
}

# 10-digit phone number
RECIPIENTS = ['##########@tmomail.net']

precip_palette_indices = [
    44, 74, 104, 132, 162, 190, 219, 249, 277, 307, 337, 366,
    395, 423, 452, 482, 512, 541, 570, 598, 628, 657, 686, 714
]
precip_breaks = np.array([
    .04, .08, .12, .2, .28, .4, .6, .8, 1., 1.2, 1.6, 2,
    2.4, 2.8, 3.2, 3.6, 4, 5, 6, 7, 8, 10, 12, 15, 20
])
PRECIP_MEAN_SCALE = (precip_breaks[:-1] + precip_breaks[1:]) / 2
PRECIP_COLOR_PICKER = [[680] * len(precip_palette_indices), precip_palette_indices]

temp_palette_indices = [
    34, 42, 50, 60, 70, 79, 88, 97, 107, 116, 125, 135, 144, 153, 162, 172, 181, 190, 199, 208, 218, 227, 236, 245,
    254, 264, 274, 282, 291, 301, 310, 319, 329, 338, 347, 356, 366, 375, 384, 394, 403, 412, 421, 430, 439,
    449, 458, 468, 477, 486, 496, 504, 513, 523, 532, 541, 550, 559, 569, 578, 588, 597, 606, 615, 624, 633,
    643, 652, 660, 670, 680, 689, 698, 708, 718, 727, 735, 744
]
temp_breaks = np.array([
    -33, -22, -17, -11, -6, 0, 5, 10, 16, 21, 27, 32, 37, 43, 48, 54, 59, 64, 70, 75, 81, 86, 91, 97, 102, 111, 122
])
temp_indices = np.arange(len(temp_palette_indices) + 1)
temp_interpolated = np.interp(temp_indices, temp_indices[::3], temp_breaks)
TEMP_MEAN_SCALE = (temp_interpolated[:-1] + temp_interpolated[1:]) / 2
TEMP_COLOR_PICKER = [[680] * len(temp_palette_indices), temp_palette_indices]

SNOW_TO_LIQUID = np.interp(temp_indices, [0, 15, 18, 26, 30, 77], [25, 25, 20, 15, 10, 10])

# breckenridge [400:460, 380:430]
# peaceful valley [210:295, 150:265]
# eldora [420:495, 175:260]

SLICES = {
    '1916': {
        'peaceful valley': {
            'row': (210, 295),
            'col': (150, 265),
        },
        'eldora': {
            'row': (420, 495),
            'col': (175, 260),
        },
    },
    '1969': {
        # 'breckenridge': {
        #     'row': (400, 460),
        #     'col': (380, 430),
        # },
        'loveland': {
            'row': (255, 290),
            'col': (490, 515),
        },
        'a-basin': {
            'row': (310, 335),
            'col': (515, 535),
        },
    },
}

HOME = os.environ.get('HOME')

PRECIP_URL = 'https://img{}.weather.us/images/data/cache/model/model_modez_{}{:02d}{:02d}{:02d}_{}_{}_220.png'
TEMP_URL = 'https://img{}.weather.us/images/data/cache/model/model_modez_{}{:02d}{:02d}{:02d}_{}_{}_210.png'

ZONES = {
    # '503': 'colorado',
    '1969': 'summit',
    '1916': 'boulder',
}

DATA_PATH = '/data/ecmwf-forecasts'
