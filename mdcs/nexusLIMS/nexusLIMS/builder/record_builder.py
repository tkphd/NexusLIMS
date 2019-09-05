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
import logging as _logging
import hyperspy.api_nogui as _hs
from uuid import uuid4 as _uuid4
from datetime import datetime as _datetime
from nexusLIMS.schemas.activity import AcquisitionActivity as _AcqAc
from nexusLIMS.harvester import sharepoint_calendar as _sp_cal
from glob import glob as _glob
from timeit import default_timer as _timer

_logger = _logging.getLogger(__name__)


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
        ***REMOVED*** are read-only, should generally be able to be trusted).
    user : str
        A valid NIST username (the short format: e.g. "ear1"
        instead of ernst.august.ruska@nist.gov). Controls the results
        returned from the calendar - value is as specified in
        :py:func:`~.sharepoint_calendar.get_events`

    Returns
    -------
    xml_record : str
        A formatted string containing a well-formed and valid XML document
        for the data contained in the provided path
    """

    xml_record = ''

    if date is None:
        date = _datetime.fromtimestamp(_os.path.getmtime(path)).strftime(
            '%Y-%m-%d')

    # Insert XML prolog, XSLT reference, and namespaces.
    xml_record += "<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n"
    # TODO: Header elements may be changed once integration into CDCS determined
    xml_record += "<?xml-stylesheet type=\"text/xsl\" href=\"\"?>\n"
    xml_record += "<nx:Experiment xmlns=\"\"\n"
    xml_record += "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
    xml_record += "xmlns:nx=\"" \
                  "https://data.nist.gov/od/dm/nexus/experiment/v1.0\">\n"

    # TODO: Account for results from multiple sessions?
    _logger.info(f"Getting calendar events with instrument: {instrument}, "
                 f"date: {date}, user: {user}")
    xml_record += _sp_cal.get_events(instrument=instrument, date=date,
                                     user=user, wrap=False)
    _logger.info(f"Building acquisition activities for {path}")
    xml_record += build_acq_activities(path=path)

    xml_record += "</nx:Experiment>"  # Add closing tag for root element.

    return xml_record


def build_acq_activities(path):
    """
    Build an XML string representation of each AcquisitionActivity for a
    single microscopy session. This includes setup parameters and metadata
    associated with each dataset obtained during a microscopy session. Unique
    AcquisitionActivities are delimited via comparison of imaging modes (e.g. a
    switch from Imaging to Diffraction mode constitutes 2 unique
    AcquisitionActivities).

    Currently only working for 'FEI-Titan-TEM-635816' .dm3 files...

    Parameters
    ----------
    path : str
        A string file path which points to the file folder in which microscopy
        data is located.

    Returns
    -------
    acq_activities : str
        A string representing the XML output for each AcquisitionActivity
        associated with a given reservation/experiment on a microscope.
    """

    _logger = _logging.getLogger(__name__)
    _logger.setLevel(_logging.INFO)

    _logging.getLogger('hyperspy.io_plugins.digital_micrograph').setLevel(
        _logging.WARNING)

    files = _glob(_os.path.join(path, "**/*.dm3"), recursive=True)

    # sort files by modification time
    files.sort(key=_os.path.getmtime)

    mtimes = [''] * len(files)
    modes = [''] * len(files)
    _logger.info(f'Loading files; getting mtime and modes for this activity')
    start_timer = _timer()
    for i, f in enumerate(files):
        mode = _hs.load(f, lazy=True).original_metadata.\
            ImageList.TagGroup0.ImageTags.Microscope_Info.Imaging_Mode
        mtimes[i] = _datetime.fromtimestamp(_os.path.getmtime(f)).isoformat()
        modes[i] = mode
        this_mtime = _datetime.fromtimestamp(
            _os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
        _logger.info(f'{this_mtime} --- {mode} --- {f}')
    end_timer = _timer()

    _logger.info(f'Loading files took {end_timer - start_timer:.2f} seconds')

    activities = []

    for i, (f, t, m) in enumerate(zip(files, mtimes, modes)):
        # set last_mode to this mode if this is the first iteration;
        # otherwise set it to the last mode that we saw
        last_mode = m if i == 0 else modes[i - 1]

        # if this is the first iteration, start a new AcquisitionActivity and
        # add it to the list of activities
        if i == 0:
            _logger.debug(t)
            start_time = _datetime.fromisoformat(t)
            aa = _AcqAc(start=start_time, mode=m)
            activities.append(aa)

        # if this file's mode is the same as the last, just add it to the
        # current activity's file list
        if m == last_mode:
            _logger.info(f'Adding {f} to activity')
            activities[-1].add_file(f)

        # this file's mode is different, so it belongs to the next
        # AcquisitionActivity. End the current AcquisitionActivity and create
        # a new one with this file's information
        else:
            # AcquisitionActivity end time is previous mtime
            activities[-1].end = _datetime.fromisoformat(mtimes[i - 1])
            # New AcquisitionActivity start time is t
            activities.append(_AcqAc(start=_datetime.fromisoformat(t), mode=m))
            _logger.info(f'Adding {f} to activity')
            activities[-1].add_file(f)

        # We have reached the last file, so end the current activity
        if i == len(files) - 1:
            activities[-1].end = _datetime.fromisoformat(t)

    acq_activities = ''
    _logger.info('Finished detecting activities')
    sample_id = str(_uuid4())       # just a random string for now
    for i, a in enumerate(activities):
        aa_logger = _logging.getLogger('nexusLIMS.schemas.activity')
        # aa_logger.setLevel(_logging.ERROR)
        _logger.info(f'Activity {i}: storing setup parameters')
        a.store_setup_params()
        _logger.info(f'Activity {i}: storing unique metadata values')
        a.store_unique_metadata()

        acq_activities += a.as_xml(i, sample_id,
                                   indent_level=1, print_xml=False)

    return acq_activities


def dump_record(path,
                filename=None,
                instrument=None,
                date=None,
                user=None):
    """
    Writes an XML record composed of information pulled from the Sharepoint
    calendar as well as metadata extracted from the microscope data (e.g. dm3
    files).

    Parameters
    ----------
    path : str
        A string file path which points to the file location of the microscopy
        metadata
    filename : None or str
        The filename of the dumped xml file to write. If none, a d
    instrument : str
        A string which corresponds to the type of microscope used to generate
        the data to be dumped
    date : str
        A string which corresponds to the event date from which events are going
        to be fetched from
    user : str
        A string which corresponds to the NIST user who performed the
        microscopy experiment

    Returns
    -------
    filename : str
        The name of the created record that was returned
    """
    if filename is None:
        filename = 'compiled_record' + \
                   (f'_{instrument}' if instrument else '') + \
                   (f'_{date}' if date else '') + \
                   (f'_{user}' if user else '') + '.xml'
    with open(filename, 'w') as f:
        text = build_record(path=path, instrument=instrument,
                            date=date, user=user)
        f.write(text)
    return filename
