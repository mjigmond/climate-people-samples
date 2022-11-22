from typing import Tuple, Dict, List

import numpy as np
import os


def parse_hds(file_path: str, nlay: int, nrow: int, ncol: int) -> Tuple[Dict[Tuple[int, int], np.array], np.array]:
    """
    This function will parse a binary structured *.hds (head) file and will return a tuple with two items.
    The first item is a dictionary containing the head arrays as values and stress periods/time steps tuples as keys.
    The second item is an array of total simulation times matching the length of the dictionary.
    Careful consideration should be given to binary files originating from MODFLOW compiled with non-Intel FORTRAN
    because some compilers will add some padding bytes within the data type defined below.

    Note: many of the variables are named to be consistent with their naming convention in the source code and
          code documentation.

    Args:
        file_path : input HDS file name.
        nlay : number of layers in the model.
        nrow : number of rows in the model.
        ncol : number of columns in the model.

    Returns:
        The first item is a dictionary containing the head arrays as values and stress periods/time steps tuples as keys.
        The second item is an array of total times matching the length of the dictionary.
        {(kper: int, kstp: int): np.array}.
    """
    if file_path is None or nlay == 0 or nrow == 0 or ncol == 0:
        return {}, np.empty(0)
    file_size = os.path.getsize(file_path)
    offset = 0
    hds = {}
    totim = []
    while offset < file_size:
        dt = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('pertim', 'f4'),
            ('totim', 'f4'),
            ('text', 'S16'),
            ('ncol', 'i4'),
            ('nrow', 'i4'),
            ('ilay', 'i4'),
            ('data', 'f4', (nrow, ncol))
        ])
        arr = np.memmap(file_path, mode='r', dtype=dt, offset=offset, shape=nlay)
        offset += dt.itemsize * nlay
        kper = arr['kper'][0]
        kstp = arr['kstp'][0]
        hds[kper, kstp] = arr['data'].copy()
        totim.append(arr['totim'][0])
    return hds, np.asarray(totim)


def parse_cbb(file_path: str, nlay: int, nrow: int, ncol: int, items: List[str] = None) \
        -> Dict[str, Dict[Tuple[int, int], np.array]]:
    """
    This function will parse a binary structured *.cbb (budget) file and will return a dictionary.

    Careful consideration should be given to binary files originating from MODFLOW compiled with non-Intel FORTRAN
    because some compilers will add some padding bytes within the data type defined below.

    Note: many of the variables are named to be consistent with their naming convention in the source code and
          code documentation.

    Args:
        file_path : input HDS file name.
        nlay : number of layers in the model.
        nrow : number of rows in the model.
        ncol : number of columns in the model.
        items: list of budget items to return; large budget files can exceed
               available memory so limit the returned items.

    Returns:
        dictionary with flux items as keys and for values a dictionary similar to the HDS parser,
        the flux arrays as values and stress periods/time steps tuples as keys. Budget terms are stripped of
        white space at the beginning and at the end.
        {'RECHARGE': {(kper: int, kstp: int): np.array}}.
    """
    file_size = os.path.getsize(file_path)
    offset = 0
    cbb = {}
    while offset < file_size:
        dt = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('text', 'S16'),
            ('ncol', 'i4'),
            ('nrow', 'i4'),
            ('nlay', 'i4'),
            ('data', 'f4', (nlay, nrow, ncol))
        ])
        arr = np.memmap(file_path, mode='r', dtype=dt, offset=offset, shape=1)[0]
        offset += dt.itemsize
        text = arr['text'].decode().strip()
        kper = arr['kper']
        kstp = arr['kstp']
        if items and text in items:
            cbb.setdefault(text, {})
            cbb[text][kper, kstp] = arr['data'].copy()
            continue
        elif not items:
            cbb.setdefault(text, {})
            cbb[text][kper, kstp] = arr['data'].copy()

    return cbb


def parse_hdsu(file_path: str) -> Dict[Tuple[int, int], np.array]:
    """
    This function will parse a binary unstructured *.hds (head) file and will return a dictionary
    containing the head arrays as values and stress periods/time steps tuples as keys.

    Careful consideration should be given to binary files originating from MODFLOW compiled with non-Intel FORTRAN
    because some compilers will add some padding bytes within the data type defined below.

    Note: many of the variables are named to be consistent with their naming convention in the source code and
          code documentation. Unlike the structured parser, the data type needs to be changed in-flight as
          the number of nodes varies among layers.

    Args:
        file_path: input unstructured *.hds file name.

    Returns:
        dictionary containing the head arrays as values and stress periods/time steps tuples as keys.
        {(kper: int, kstp: int): np.array}.
    """
    file_size = os.path.getsize(file_path)
    offset = 0
    HDS = {}
    while offset < file_size:
        dtmeta = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('pertim', 'f4'),
            ('totim', 'f4'),
            ('text', 'S16'),
            ('nstrt', 'i4'),
            ('nndlay', 'i4'),
            ('ilay', 'i4')
        ])
        meta = np.memmap(file_path, mode='r', dtype=dtmeta, offset=offset, shape=1)[0]
        nstrt = meta['nstrt']
        nndlay = meta['nndlay']
        kper = meta['kper']
        kstp = meta['kstp']
        ilay = meta['ilay']
        if ilay == 1:
            h = np.empty(0)
        n = nndlay - nstrt + 1
        dt = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('pertim', 'f4'),
            ('totim', 'f4'),
            ('text', 'S16'),
            ('nstrt', 'i4'),
            ('nndlay', 'i4'),
            ('ilay', 'i4'),
            ('data', 'f4', n)
        ])
        arr = np.memmap(file_path, mode='r', dtype=dt, offset=offset, shape=1)[0]
        h = np.concatenate((h, arr['data']))
        offset += dt.itemsize
        HDS[kper, kstp] = h
    return HDS


def parse_cbbu(file_path: str, items: List[str] = None) -> Dict[Tuple[str, int, int, int], np.array]:
    """
    This function will parse a binary unstructured *.cbb (budget) file and will return a dictionary
    containing the flux arrays as values and item/array_size/stress periods/time steps tuples as keys.

    Careful consideration should be given to binary files originating from MODFLOW compiled with non-Intel FORTRAN
    because some compilers will add some padding bytes within the data type defined below.

    Note: many of the variables are named to be consistent with their naming convention in the source code and
          code documentation. Unlike the structured parser, the data type needs to be changed in-flight as
          the number of nodes varies among layers.

    Args:
        file_path: input unstructured *.cbb file name.
        items : list of budget items to return.
                Large budget files can exceed available memory so limit the returned items.

    Returns:
        dictionary of the following type:
            {((item: str, array_size: int), kper: int, kstp: int): np.array}.

    """
    fSize = os.path.getsize(file_path)
    print(fSize)
    ofst = 0
    BUD = {}
    while ofst < fSize:
        dtmeta = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('text', 'S16'),
            ('nval', 'i4'),
            ('one', 'i4'),
            ('icode', 'i4')
        ])
        meta = np.memmap(file_path, mode='r', dtype=dtmeta, offset=ofst, shape=1)[0]
        arr_size = meta['nval']
        dtu = np.dtype([
            ('kstp', 'i4'),
            ('kper', 'i4'),
            ('text', 'S16'),
            ('nval', 'i4'),
            ('one', 'i4'),
            ('icode', 'i4'),
            ('data', 'f4', arr_size)
        ])
        data = np.memmap(file_path, mode='r', dtype=dtu, offset=ofst, shape=1)[0]
        ofst += dtu.itemsize
        kper = data['kper']
        kstp = data['kstp']
        text = data['text'].decode().strip()
        if items and text in items:
            BUD[text, arr_size, kper, kstp] = data['data']
            continue
        elif not items:
            BUD[text, arr_size, kper, kstp] = data['data']

    return BUD


if __name__ == '__main__':
    nlay, nrow, ncol = 7, 368, 410
    file_name = 'data/abr.hds'
    hds = parse_hds(file_name, nlay, nrow, ncol)

    file_name = 'data/abr.cbb'
    cbb = parse_cbb(file_name, nlay, nrow, ncol, items=['ET', 'WELLS', 'RIVER LEAKAGE'])
    print(cbb.keys())

    file_name = 'data/biscayne.hds'
    hds = parse_hdsu(file_name)

    file_name = 'data/biscayne.cbc'
    cbb = parse_cbbu(file_name, items=['ET', 'WELLS', 'RIVER LEAKAGE'])
    print(cbb.keys())
