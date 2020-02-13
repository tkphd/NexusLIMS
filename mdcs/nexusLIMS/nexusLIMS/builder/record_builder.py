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
import pathlib as _pathlib
from uuid import uuid4 as _uuid4
from datetime import datetime as _datetime
from nexusLIMS import mmf_nexus_root_path as _mmf_path
from nexusLIMS.schemas.activity import AcquisitionActivity as _AcqAc
from nexusLIMS.schemas.activity import cluster_filelist_mtimes
from nexusLIMS.harvester import sharepoint_calendar as _sp_cal
from nexusLIMS.utils import parse_xml as _parse_xml
from nexusLIMS.utils import find_files_by_mtime as _find_files
from nexusLIMS.extractors import extension_reader_map as _ext
from glob import glob as _glob
from timeit import default_timer as _timer

_logger = _logging.getLogger(__name__)
XSLT_PATH = _os.path.join(_os.path.dirname(__file__),
                          "cal_events_to_nx_record.xsl")


def build_record(instrument, dt_from, dt_to, date, user):
    """
    Construct an XML document conforming to the NexusLIMS schema from a
    directory containing microscopy data files. For calendar parsing,
    currently no logic is implemented for a query that returns multiple records

    Parameters
    ----------
    instrument : :py:class:`~nexusLIMS.instruments.Instrument`
        One of the NexusLIMS instruments contained in the
        :py:attr:`~nexusLIMS.instruments.instrument_db` database.
        Controls what instrument calendar is used to get events.
    dt_from : datetime.datetime
        The starting timestamp that will be used to determine which files go
        in this record
    dt_to : datetime.datetime
        The ending timestamp used to determine the last point in time for
        which files should be associated with this record
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

    xml_record = ''

    # if an explicit date is not provided, use the start of the timespan
    if date is None:
        date = dt_from.strftime('%Y-%m-%d')

    # Insert XML prolog, XSLT reference, and namespaces.
    xml_record += "<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n"
    # TODO: Header elements may be changed once integration into CDCS determined
    xml_record += "<?xml-stylesheet type=\"text/xsl\" href=\"\"?>\n"
    xml_record += "<nx:Experiment xmlns=\"\"\n"
    xml_record += "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
    xml_record += "xmlns:nx=\"" \
                  "https://data.nist.gov/od/dm/nexus/experiment/v1.0\">\n"

    _logger.info(f"Getting calendar events with instrument: {instrument.name}, "
                 f"date: {date}, user: {user}")
    events_str = _sp_cal.get_events(instrument=instrument, date=date,
                                    user=user, wrap=True)
    # TODO: Account for results from multiple sessions? This should only
    #  happen if one user has multiple reservations on the same date. For now,
    #  assume the first record is the right one:
    # Apply XSLT to transform calendar events to single record format:
    output = _parse_xml(events_str, XSLT_PATH,
                        instrument_PID=instrument.name,
                        instrument_name=instrument.schema_name,
                        experiment_id=str(_uuid4()),
                        collaborator=None,
                        sample_id=str(_uuid4()))

    # No calendar events were found
    if str(output) == '':
        output = f'<title>Experiment on the {instrument.schema_name}' \
                 f' on {dt_from.strftime("%A %b. %d, %Y")}</title>\n' + \
                 '<id/>\n' + \
                 '<summary>\n' + \
                 f'    <instrument pid="{instrument.name}">' \
                 f'{instrument.schema_name}</instrument>\n' + \
                 '</summary>\n'

    xml_record += str(output)

    _logger.info(f"Building acquisition activities for timespan from "
                 f"{dt_from.isoformat()} to {dt_to.isoformat()}")
    xml_record += build_acq_activities(instrument, dt_from, dt_to)

    xml_record += "</nx:Experiment>"  # Add closing tag for root element.

    return xml_record


def build_acq_activities(instrument, dt_from, dt_to):
    """
    Build an XML string representation of each AcquisitionActivity for a
    single microscopy session. This includes setup parameters and metadata
    associated with each dataset obtained during a microscopy session. Unique
    AcquisitionActivities are delimited via comparison of imaging modes (e.g. a
    switch from Imaging to Diffraction mode constitutes 2 unique
    AcquisitionActivities).

    Currently only working for '***REMOVED***' .dm3 files...

    Parameters
    ----------
    instrument : :py:class:`~nexusLIMS.instruments.Instrument`
        One of the NexusLIMS instruments contained in the
        :py:attr:`~nexusLIMS.instruments.instrument_db` database.
        Controls what instrument calendar is used to get events.
    dt_from : datetime.datetime
        The starting timestamp that will be used to determine which files go
        in this record
    dt_to : datetime.datetime
        The ending timestamp used to determine the last point in time for
        which files should be associated with this record

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

    start_timer = _timer()
    path = _os.path.abspath(_os.path.join(_mmf_path, instrument.filestore_path))
    _logger.info(f'Starting new file-finding in {path}')
    files = _find_files(path, dt_from, dt_to)
    end_timer = _timer()
    _logger.info(f'Found {len(files)} files in'
                 f' {end_timer - start_timer:.2f} seconds')

    # remove all files but those supported by nexusLIMS.extractors
    files = [f for f in files if _os.path.splitext(f)[1].strip('.') in
             _ext.keys()]

    # get the timestamp boundaries of acquisition activities
    aa_bounds = cluster_filelist_mtimes(files)

    # add the last file's modification time to the boundaries list to make
    # the loop below easier to process
    aa_bounds.append(_os.path.getmtime(files[-1]))

    activities = [None] * len(aa_bounds)

    i = 0
    aa_idx = 0
    while i < len(files):
        f = files[i]
        mtime = _os.path.getmtime(f)

        # check this file's mtime, if it is less than this iteration's value
        # in the AA bounds, then it belongs to this iteration's AA
        # if not, then we should move to the next activity
        if mtime <= aa_bounds[aa_idx]:
            # if current activity index is None, we need to start a new AA:
            if activities[aa_idx] is None:
                start_time = _datetime.fromtimestamp(mtime)
                activities[aa_idx] = _AcqAc(start=start_time)

            # add this file to the AA
            _logger.info(f'Adding file {i} {f.replace(_mmf_path,"")} to activity'
                         f' {aa_idx}')
            activities[aa_idx].add_file(f)
            # assume this file is the last one in the activity (this will be
            # true on the last iteration where mtime is <= to the
            # aa_bounds value)
            activities[aa_idx].end = _datetime.fromtimestamp(mtime)
            i += 1
        else:
            # this file's mtime is after the boundary and is thus part of the
            # next activity, so increment AA counter and reprocess file (do
            # not increment i)
            aa_idx += 1

    acq_activities_str = ''
    _logger.info('Finished detecting activities')
    sample_id = str(_uuid4())       # just a random string for now
    for i, a in enumerate(activities):
        aa_logger = _logging.getLogger('nexusLIMS.schemas.activity')
        # aa_logger.setLevel(_logging.ERROR)
        _logger.info(f'Activity {i}: storing setup parameters')
        a.store_setup_params()
        _logger.info(f'Activity {i}: storing unique metadata values')
        a.store_unique_metadata()

        acq_activities_str += a.as_xml(i, sample_id,
                                       indent_level=1, print_xml=False)

    return acq_activities_str


def dump_record(instrument,
                dt_from,
                dt_to,
                filename=None,
                date=None,
                user=None):
    """
    Writes an XML record composed of information pulled from the Sharepoint
    calendar as well as metadata extracted from the microscope data (e.g. dm3
    files).

    Parameters
    ----------
    instrument : :py:class:`~nexusLIMS.instruments.Instrument`
        One of the NexusLIMS instruments contained in the
        :py:attr:`~nexusLIMS.instruments.instrument_db` database.
        Controls what instrument calendar is used to get events.
    dt_from : datetime.datetime
        The starting timestamp that will be used to determine which files go
        in this record
    dt_to : datetime.datetime
        The ending timestamp used to determine the last point in time for
        which files should be associated with this record
    filename : None or str
        The filename of the dumped xml file to write. If None, a default name
        will be generated from the other parameters
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
                   (f'_{instrument.name}' if instrument else '') + \
                   (f'_{date}' if date else dt_from.strftime('_%Y-%m-%d')) + \
                   (f'_{user}' if user else '') + '.xml'
    _pathlib.Path(_os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as f:
        text = build_record(instrument, dt_from, dt_to,
                            date=date, user=user)
        f.write(text)
    return filename
