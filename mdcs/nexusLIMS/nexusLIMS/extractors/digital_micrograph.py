#  NIST Public License - 2019
#
#  This software was developed by employees of the National Institute of
#  Standards and Technology (NIST), an agency of the Federal Government
#  and is being made available as a public service. Pursuant to title 17
#  United States Code Section 105, works of NIST employees are not subject
#  to copyright protection in the United States.  This software may be
#  subject to foreign copyright.  Permission in the United States and in
#  foreign countries, to the extent that NIST may hold copyright, to use,
#  copy, modify, create derivative works, and distribute this software and
#  its documentation without fee is hereby granted on a non-exclusive basis,
#  provided that this notice and disclaimer of warranty appears in all copies.
#
#  THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
#  EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
#  TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
#  IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
#  AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
#  WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
#  ERROR FREE.  IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
#  BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
#  ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
#  WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
#  OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
#  WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF,
#  OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#

# limit our imports to hopefully reduce loading time
import os as _os
import re as _re
import logging as _logging
import shutil as _shutil
import tarfile as _tarfile

from hyperspy.io import load as _hs_load
from hyperspy.exceptions import *
from hyperspy.io_plugins.digital_micrograph import \
    DigitalMicrographReader as _DMReader
from hyperspy.io_plugins.digital_micrograph import ImageObject as _ImageObject

from nexusLIMS.instruments import get_instr_from_filepath as _get_instr
from nexusLIMS.utils import get_nested_dict_key
from nexusLIMS.utils import get_nested_dict_value_by_path
from nexusLIMS.utils import set_nested_dict_value

# from hyperspy.misc.utils import DictionaryTreeBrowser as _DTB
_logger = _logging.getLogger(__name__)


def parse_643_titan(mdict):
    """
    Add/adjust metadata specific to the 643 FEI Titan ('FEI-Titan-STEM-630901
    in ***REMOVED***') to the metadata dictionary

    Parameters
    ----------
    mdict : dict
        "raw" metadata dictionary as parsed by :py:func:`get_dm3_metadata`

    Returns
    -------
    new_mdict : dict
        The original metadata dictionary with added information specific to
        files originating from this microscope with "important" values contained
        under the 'nx_meta' key at the root level
    """
    # TODO: complete 643 titan metadata parsing
    return mdict


def parse_642_titan(mdict):
    """
    Add/adjust metadata specific to the 642 FEI Titan ('FEI-Titan-TEM-635816 in
    ***REMOVED***') to the metadata dictionary

    Parameters
    ----------
    mdict : dict
        "raw" metadata dictionary as parsed by :py:func:`get_dm3_metadata`

    Returns
    -------
    new_mdict : dict
        The original metadata dictionary with added information specific to
        files originating from this microscope with "important" values contained
        under the 'nx_meta' key at the root level
    """
    # DONE: complete 642 titan metadata parsing including Tecnai tag
    path_to_tecnai = get_nested_dict_key(mdict, 'Tecnai')
    tecnai_value = get_nested_dict_value_by_path(mdict, path_to_tecnai)
    microscope_info = tecnai_value['Microscope Info']
    tecnai_value['Microscope Info'] = \
        process_tecnai_microscope_info(microscope_info)
    set_nested_dict_value(mdict, path_to_tecnai, tecnai_value)

    # TODO: move the filtering that is done in
    #  nexusLIMS.schemas.activity.read_metadata() to here, and place under
    #  'nx_meta' key
    return mdict


def parse_642_jeol(mdict):
    """
    Add/adjust metadata specific to the 642 FEI Titan ('JEOL-JEM3010-TEM-565989
    in ***REMOVED***') to the metadata dictionary

    Parameters
    ----------
    mdict : dict
        "raw" metadata dictionary as parsed by :py:func:`get_dm3_metadata`

    Returns
    -------
    new_mdict : dict
        The original metadata dictionary with added information specific to
        files originating from this microscope with "important" values contained
        under the 'nx_meta' key at the root level
    """
    # TODO: complete JEOL metadata parsing
    return mdict


_instr_specific_parsers = {
    'FEI-Titan-STEM-630901': parse_643_titan,
    'FEI-Titan-TEM-635816': parse_642_titan,
    'JEOL-JEM3010-TEM-565989': parse_642_jeol
}


def process_tecnai_microscope_info(microscope_info, delimiter=u'\u2028'):
    """
    Process the Microscope_Info metadata string from an FEI Titan
    TEM into a dictionary of key-value pairs

    Parameters
    ----------
    microscope_info : str
        The string of data obtained from the original_metadata.ImageList.\
        TagGroup0.ImageTags.Tecnai.Microscope_Info leaf of the metadata tree
        obtained when loading a .dm3 file as a HyperSpy signal
    delimiter : str
        The value (a unicode string) used to split the ``microscope_info``
        string. Should not need to be provided (this value is hard-coded in
        DigitalMicrograph), but specified as a parameter for future
        flexibility

    Returns
    -------
    info_dict : dict
        The information contained in the string, in a more easily-digestible
        form.
    """

    def __find_val(s_to_find, list_to_search):
        """
        Return the first value in list_to_search that contains s_to_find, or
        None if it is not found

        Note: If needed, this could be improved to use regex instead, which
              would provide more control over the patterns to return
        """
        res = [x for x in list_to_search if s_to_find in x]
        if len(res) > 0:
            res = res[0]
            # remove the string we searched for from the beginning of the res
            return _re.sub("^" + s_to_find, "", res)
        else:
            return None

    info_dict = {}

    # split the string into a list
    tecnai_info = microscope_info.split(delimiter)

    # String
    info_dict['Microscope_Name'] = \
        __find_val('Microscope ', tecnai_info)

    # String
    info_dict['User'] = __find_val('User ', tecnai_info)

    # String
    tmp = __find_val('Gun ', tecnai_info)
    info_dict['Gun_Name'] = tmp[:tmp.index(' Extr volt')]
    tmp = tmp[tmp.index(info_dict['Gun_Name']) + len(info_dict['Gun_Name']):]

    # Integer (volts)
    tmp = tmp.strip('Extr volt ')
    info_dict['Extractor_Voltage'] = int(tmp.split()[0])

    # Integer
    tmp = tmp[tmp.index('Gun Lens ') + len('Gun Lens '):]
    info_dict['Gun_Lens_No'] = int(tmp.split()[0])

    # Float (microAmps)
    tmp = tmp[tmp.index('Emission ') + len('Emission '):]
    info_dict['Emission_Current'] = float(tmp.split('uA')[0])

    # String
    tmp = __find_val('Mode ', tecnai_info)
    info_dict['Mode'] = tmp[:tmp.index(' Defocus')]
    # 'Mode' should be five terms long, and the last term is either 'Image',
    # 'Diffraction', (or maybe something else)

    # Float (micrometer)
    if 'Magn ' in tmp:  # Imaging mode
        info_dict['Defocus'] = float(tmp.split('Defocus (um) ')[1].split()[0])
    elif 'CL ' in tmp:  # Diffraction mode
        info_dict['Defocus'] = float(tmp.split('Defocus ')[1].split()[0])

    # This value changes based on whether in image or diffraction mode
    # (magnification or camera length)
    # Integer
    if info_dict['Mode'].split()[4] == 'Image':
        info_dict['Magnification'] = int(tmp.split('Magn ')[1].strip('x'))
    # Float
    elif info_dict['Mode'].split()[4] == 'Diffraction':
        info_dict['Camera_Length'] = float(tmp.split('CL ')[1].strip('m'))

    # Integer (1 to 5)
    info_dict['Spot'] = int(__find_val('Spot ', tecnai_info))

    # Float - Lens strengths expressed as a "%" value
    info_dict['C2_Strength'] = float(__find_val('C2 ', tecnai_info).strip('%'))
    info_dict['C3_Strength'] = float(__find_val('C3 ', tecnai_info).strip('%'))
    info_dict['Obj_Strength'] = float(
        __find_val('Obj ', tecnai_info).strip('%'))
    info_dict['Dif_Strength'] = float(
        __find_val('Dif ', tecnai_info).strip('%'))

    # Float (micrometers)
    tmp = __find_val('Image shift ', tecnai_info).strip('um')
    info_dict['Image_Shift_x'] = float(tmp.split('/')[0])
    info_dict['Image_Shift_y'] = float(tmp.split('/')[1])

    # Float values are given in micrometers and degrees
    tmp = __find_val('Stage ', tecnai_info).split(',')
    tmp = [float(t.strip(' umdeg')) for t in tmp]
    info_dict['Stage_Position_x'] = tmp[0]
    info_dict['Stage_Position_y'] = tmp[1]
    info_dict['Stage_Position_z'] = tmp[2]
    info_dict['Stage_Position_theta'] = tmp[3]
    info_dict['Stage_Position_phi'] = tmp[4]

    def __read_aperture(val, tecnai_info_):
        """Helper method to test if aperture has value or is retracted"""
        try:
            value = __find_val(val, tecnai_info_)
            value = value.strip(' um')
            res = int(value)
        except (ValueError, AttributeError):
            res = None
        return res

    # Either an integer value or None (indicating the aperture was not
    # inserted or tag did not exist in the metadata)
    info_dict['C1_Aperture'] = __read_aperture('C1 Aperture: ', tecnai_info)
    info_dict['C2_Aperture'] = __read_aperture('C2 Aperture: ', tecnai_info)
    info_dict['Obj_Aperture'] = __read_aperture('OBJ Aperture: ', tecnai_info)
    info_dict['SA_Aperture'] = __read_aperture('SA Aperture: ', tecnai_info)

    # Nested dictionary
    try:
        info_dict['Filter_Settings'] = {}
        tecnai_filter_info = tecnai_info[tecnai_info.index(
            'Filter related settings:') + 1:]
        # String
        info_dict['Filter_Settings']['Mode'] = __find_val('Mode: ',
                                                          tecnai_filter_info)
        # Float (eV/channel)
        tmp = __find_val('Selected dispersion: ', tecnai_filter_info)
        tmp = _re.sub(r'\[eV/Channel\]', '', tmp)
        info_dict['Filter_Settings']['Dispersion'] = float(tmp)

        # Float (millimeter)
        tmp = __find_val('Selected aperture: ', tecnai_filter_info)
        tmp = tmp.strip('m')
        info_dict['Filter_Settings']['Aperture'] = float(tmp)

        # Float (eV)
        tmp = __find_val('Prism shift: ', tecnai_filter_info)
        tmp = _re.sub(r'\[eV\]', '', tmp)
        info_dict['Filter_Settings']['Prism_Shift'] = float(tmp)

        # Float (eV)
        tmp = __find_val('Drift tube: ', tecnai_filter_info)
        tmp = _re.sub(r'\[eV\]', '', tmp)
        info_dict['Filter_Settings']['Drift_Tube'] = float(tmp)

        # Float (eV)
        tmp = __find_val('Total energy loss: ', tecnai_filter_info)
        tmp = _re.sub(r'\[eV\]', '', tmp)
        info_dict['Filter_Settings']['Total_Energy_Loss'] = float(tmp)
    except ValueError as _:
        _logger.info('Filter settings not found in Tecnai microscope info')

    return info_dict


def get_dm3_metadata(filename):
    """
    Returns the metadata (as a dict) from a .dm3 file saved by the Gatan's
    Digital Micrograph in the Nexus Microscopy Facility, with some
    non-relevant information stripped out, and instrument specific metadata
    parsed and added by one of the instrument-specific parsers.

    Parameters
    ----------
    filename : str
        path to a .dm3 file saved by Gatan's Digital Micrograph

    Returns
    -------
    metadata : dict or None
        The metadata of interest extracted from the file. If None, the file
        could not be opened
    """
    # We do lazy loading so we don't actually read the data from the disk to
    # save time and memory.
    try:
        s = _hs_load(filename, lazy=True)
    except (DM3DataTypeError, DM3FileVersionError, DM3TagError,
            DM3TagIDError, DM3TagTypeError) as e:
        _logger.warning(f'File reader could not open {filename}, received '
                        f'exception: {e.__repr__()}')
        return None

    if isinstance(s, list):
        # s is a list, rather than a single signal
        m_list = [{}] * len(s)
        for i in range(len(s)):
            m_list[i] = s[i].original_metadata
    else:
        m_list = [s.original_metadata]

    for i, m_tree in enumerate(m_list):
        # Important trees:
        #   DocumentObjectList
        #     Contains information about the display of the information,
        #     including bits about annotations that are included on top of the
        #     image data, the CLUT (color look-up table), data min/max.
        #
        #   ImageList
        #     Contains the actual image information

        # Remove the trees that are not of interest:
        for t in ['ApplicationBounds', 'DocumentTags', 'HasWindowPosition',
                  'ImageSourceList',  'Image_Behavior', 'InImageMode',
                  'MinVersionList', 'NextDocumentObjectID', 'PageSetup',
                  'Page_Behavior', 'SentinelList', 'Thumbnails',
                  'WindowPosition', 'root']:
            m_tree = _remove_dtb_element(m_tree, t)

        # Within the DocumentObjectList tree, we really only care about the
        # AnnotationGroupList for each TagGroup, so go into each TagGroup and
        # delete everything but that...
        # NB: the hyperspy DictionaryTreeBrowser __iter__ function returns each
        #   tree element as a tuple containing the tree name and the actual
        #   tree, so we loop through the tag names by taking the first part
        #   of the tuple:
        for tg_name, tg in m_tree.DocumentObjectList:
            # tg_name should be 'TagGroup0', 'TagGroup1', etc.
            keys = tg.keys()
            # we want to keep this, so remove from the list to loop through
            keys.remove('AnnotationGroupList')
            for k in keys:
                # k should be in ['AnnotationType', 'BackgroundColor',
                # 'BackgroundMode', 'FillMode', etc.]
                m_tree = _remove_dtb_element(m_tree, 'DocumentObjectList.'
                                                     '{}.{}'.format(tg_name, k))

        for tg_name, tg in m_tree.ImageList:
            # tg_name should be 'TagGroup0', 'TagGroup1', etc.
            keys = tg.keys()
            # We want to keep 'ImageTags' and 'Name', so remove from list
            keys.remove('ImageTags')
            keys.remove('Name')
            for k in keys:
                # k should be in ['ImageData', 'UniqueID']
                m_tree = _remove_dtb_element(m_tree, 'ImageList.'
                                                     '{}.{}'.format(tg_name, k))

        m_list[i] = m_tree.as_dictionary()

        # Get the instrument object associated with this file
        instr = _get_instr(filename)
        # if we found the instrument, then store the name as string, else None
        instr_name = instr.name if instr is not None else None

        # if the instrument name is None, this check will be false, otherwise
        # look for the instrument in our list of instrument-specific parsers:
        if instr_name in _instr_specific_parsers.keys():
            m_list[i] = _instr_specific_parsers[instr_name](m_list[i])

    if len(m_list) == 1:
        return m_list[0]
    else:
        m_list_dict = {}
        for i in range(len(m_list)):
            m_list_dict[f'Signal {i}'] = m_list[i]
        return m_list_dict


def _remove_dtb_element(tree, path):
    """
    Helper method that uses exec to delete a specific leaf of a
    DictionaryTreeBrowser using a string

    Parameters
    ----------
    tree : :py:class:`~hyperspy.misc.utils.DictionaryTreeBrowser`
        the ``DictionaryTreeBrowser`` object to remove the object from
    path : str
        period-delimited path to a DTB element

    Returns
    -------
    tree : :py:class:`~hyperspy.misc.utils.DictionaryTreeBrowser`
    """
    to_del = 'tree.{}'.format(path)
    try:

        exec('del {}'.format(to_del))
    except AttributeError as _:
        # Log the failure and continue
        _logger.info('_remove_dtb_element: Could not find {}'.format(to_del))

    return tree


def _zero_data_in_dm3(filename, out_filename=None, compress=True):
    """
    Helper method that will overwrite the data in a dm3 image file  with
    zeros and save it as either another dm3, or as a compressed archive (used
    for creating files for the test suite that don't take up tons of space).
    Since the resulting file is just some text metadata and zeros, it should
    be highly compressible (initial tests allowed for a 16MB file to be
    compressed to ~100KB).

    Parameters
    ----------
    filename : str
        Path to file to be modified
    out_filename : None or str
        Name with which to save the output file. If None, it will be
        automatically generated from the ``filename``.
    compress : bool
        Whether or not to compress the files into a tar.gz file

    Returns
    -------
    out_fname : str
        The path of the compressed (or zeroed) file
    """
    # zero out extent of data in DM3 file and compress to tar.gz:
    splitext = _os.path.splitext(filename)
    if not out_filename:
        mod_fname = splitext[0] + '_dataZeroed' + splitext[1]
    else:
        mod_fname = out_filename

    _shutil.copyfile(filename, mod_fname)

    # Do some lower-level reading on the .dm3 file to get the ImageObject refs
    with open(filename, 'rb') as f:
        dm = _DMReader(f)
        dm.parse_file()
        images = [_ImageObject(im_dict, f) for im_dict in
                  dm.get_image_dictionaries()]

    # write zeros to the file in the data block (offset + size in bytes
    # information is obtained from the ImageObject ref)
    # NB: currently this is just tested for single-image .dm3 files. Spectra
    # and image stacks will probably work differently.
    with open(mod_fname, 'r+b') as f:
        f.seek(images[0].imdict.ImageData.Data.offset)
        f.write(b'\x00' * images[0].imdict.ImageData.Data.size_bytes)

    # compress the output, if requested
    if compress:
        with _tarfile.open('{}.tar.gz'.format(mod_fname), 'w:gz') as tar:
            tar.add(mod_fname)
        out_fname = '{}.tar.gz'.format(mod_fname)
        _os.remove(mod_fname)
    else:
        out_fname = mod_fname

    return out_fname
