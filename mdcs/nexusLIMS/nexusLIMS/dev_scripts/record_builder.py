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


import os as _os
import uuid as _uuid
import pynoid as _pynoid
import logging as _logging
import hyperspy.api_nogui as _hs
from datetime import datetime as _datetime
from nexusLIMS import AcquisitionActivity
from nexusLIMS import sharepoint_calendar as sp_cal
from glob import glob as _glob
import socket as _socket
from timeit import default_timer as _timer

_logger = _logging.getLogger(__name__)
_logger.setLevel(_logging.INFO)


# files = _glob(_os.path.join(path_to_search, "*.dm3"))
# files.sort(key=_os.path.getmtime)
# files = files[:-2]
#
# mtimes = [''] * len(files)
# modes = [''] * len(files)
# start_timer = _timer()
# for i, f in enumerate(files):
#     mode = _hs.load(f, lazy=True).original_metadata.ImageList.TagGroup0.ImageTags.Microscope_Info.Imaging_Mode
#     mtimes[i] = _datetime.fromtimestamp(_os.path.getmtime(f)).isoformat()
#     modes[i] = mode
#     this_mtime = _datetime.fromtimestamp(
#         _os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
#     _logger.info(f'{this_mtime} --- {mode} --- {f}')
# end_timer = _timer()
#
# _logger.info(f'Loading files took {end_timer - start_timer:.2f} seconds')
#
# activities = []
#
# for i, (f, t, m) in enumerate(zip(files, mtimes, modes)):
#     # temporarily ignore files with this year's date
#     if t.startswith('2019'): continue
#
#     # set last_mode to this mode if this is the first iteration; otherwise set
#     # it to the last mode that we saw
#     last_mode = m if i == 0 else modes[i - 1]
#
#     # if this is the first iteration, start a new AcquisitionActivity and
#     # add it to the list of activities
#     if i == 0:
#         _logger.debug(t)
#         start_time = _datetime.fromisoformat(t)
#         aa = AcquisitionActivity(start=start_time, mode=m)
#         activities.append(aa)
#
#     # if this file's mode is the same as the last, just add it to the current
#     # activity's file list
#     if m == last_mode:
#         activities[-1].add_file(f)
#
#     # this file's mode is different, so it belongs to the next
#     # AcquisitionActivity. End the current AcquisitionActivity and create a new
#     # one with this file's information
#     else:
#         # AcquisitionActivty end time is previous mtime
#         activities[-1].end = _datetime.fromisoformat(mtimes[i - 1])
#         # New AcquisitionActivity start time is t
#         activities.append(AcquisitionActivity(start=_datetime.fromisoformat(t),
#                                               mode=m))
#         activities[-1].add_file(f)
#
#     # We have reached the last file, so end the current activity
#     if i == len(files) - 1:
#         activities[-1].end = _datetime.fromisoformat(t)
#
# for i, a in enumerate(activities):
#     AA_logger = _logging.getLogger('nexusLIMS.schemas.activity')
#     AA_logger.setLevel(_logging.ERROR)
#     a.store_setup_params()
#     a.store_unique_metadata()
#
#     a.as_xml(i, 'f81d3518-10af-4fab-9bd3-cfa2b0aea807',
#              indent_level=1, print_xml=True)


def build_record(path, instrument, date, user):
    """
    Construct an XML document conforming to the NexusLIMS schema from a
    directory containing microscopy data files. For calendar parsing,
    currently no logic is implemented for a query that returns multiple records

    Parameters
    ----------
    path : str
        A path containing dataset files to be processed
    instrument : str
        As defined in :py:func:`~.sharepoint_calendar.get_events`
        One of ['msed_titan', 'quanta', 'jeol_sem', 'hitachi_sem',
        'jeol_tem', 'cm30', 'em400', 'hitachi_s5500', 'mmsd_titan',
        'fei_helios_db']. Controls what calendar the events are fetched from.
    date : str or None
        A YYYY-MM-DD date string indicating the date from which events should
        be fetched (note: the start time of each entry is what will be
        compared - as in :py:func:`~.sharepoint_calendar.get_events`). If
        None, the date detected from the modified time of the folder will be
        used (which may or may not be correct, but given that the folders on
        CFS2E are read-only, should generally be able to be trusted).
    user : str
        A valid NIST username (the short format: e.g. "ear1"
***REMOVED***). Controls the results
        returned from the calendar - value is as specified in
        :py:func:`~.sharepoint_calendar.get_events`

    Returns
    -------
    xml_record : str
        A formatted string containing a well-formed and valid XML document
        for the data contained in the provided path
    """
    if date is None:
        date = _datetime.fromtimestamp(_os.path.getmtime(path)).\
               strftime('%Y-%m-%d')


    pass


if __name__ == '__main__':
    """
    These lines are just for testing. For real use, import the methods you
    need and operate from there
    """
    hostname = _socket.gethostname()

    path_roots = dict(
        poole=dict(
            remote='/usr/local/mnt/cfs2e_***REMOVED***/',
            local='***REMOVED***/NexusMicroscopyLIMS/test_data/'
        ),
        ***REMOVED***=dict(
            remote='/mnt/cfs2e_***REMOVED***/',
            local='***REMOVED***/NexusMicroscopyLIMS/test_data/'
        )
    )

    path_root = path_roots[hostname]['remote']
    path_to_search = _os.path.join(path_root,
                                   'mmfnexus/Titan/***REMOVED***/',
                                   '181120 - h-BN 114-a natural isotope - '
                                   'KState - Titan')

    build_record(path=path_to_search,
                 instrument='msed_titan',
                 date='2018-11-13',
                 user='***REMOVED***')
