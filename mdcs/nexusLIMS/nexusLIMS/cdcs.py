#  NIST Public License - 2020
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


import os as _os
import requests as _requests
from glob import glob as _glob
from urllib.parse import urljoin as _urljoin
import sys
import argparse
from nexusLIMS._urls import cdcs_url as _cdcs_url
from nexusLIMS.utils import nexus_req as _nx_req
from tqdm import tqdm as _tqdm
import logging as _logging

_logging.basicConfig()
_logger = _logging.getLogger(__name__)
_logger.setLevel(_logging.INFO)

# assuming there's only one workspace for this user (that is the public
# workspace)
_endpoint = _urljoin(_cdcs_url, 'rest/workspace/read_access')
_r = _nx_req(_endpoint, _requests.get, basic_auth=True)
workspace_id = _r.json()[0]['id']

# get the current template (XSD) id value:
_endpoint = _urljoin(_cdcs_url, 'rest/template-version-manager/global')
_r = _nx_req(_endpoint, _requests.get, basic_auth=True)
template_id = _r.json()[0]['current']


def upload_record_content(xml_content, title):
    """
    Upload a single XML record to the NexusLIMS CDCS instance.

    Parameters
    ----------
    xml_content : str
        The actual content of an XML record (rather than a file)
    title : str
        The title to give to the record in CDCS

    Returns
    -------
    post_r : ~requests.Response
        The REST response returned from the CDCS instance after attempting
        the upload
    """
    endpoint = _urljoin(_cdcs_url, 'rest/data/')

    payload = {
        'template': template_id,
        'title': title,
        'xml_content': xml_content
    }

    post_r = _nx_req(endpoint, _requests.post, json=payload, basic_auth=True)

    if post_r.status_code != 201:
        # anything other than 201 status means something went wrong
        _logger.error(f'Got error while uploading {title}:\n'
                      f'{post_r.text}')
        return post_r

    # assign this record to the public workspace
    record_id = post_r.json()['id']
    wrk_endpoint = _urljoin(_cdcs_url,
                            f'rest/data/{record_id}/assign/{workspace_id}')

    r = _nx_req(wrk_endpoint, _requests.patch, basic_auth=True)

    return post_r


def upload_record_files(files_to_upload):
    """
    Upload a list of .xml files (or all .xml files in the current directory)
    to the NexusLIMS CDCS instance using :py:meth:`upload_record_content`

    Parameters
    ----------
    files_to_upload : list or None
        The list of .xml files to upload. If ``None``, all .xml files in the
        current directory will be used instead.

    Returns
    -------
    files_uploaded : list
        A list of the files that were successfully uploaded
    """
    if files_to_upload is None:
        _logger.info('Using all .xml files in this directory')
        files_to_upload = _glob('*.xml')
    else:
        _logger.info('Using .xml files from command line')

    _logger.info(f'Found {len(files_to_upload)} files to upload\n')
    if len(files_to_upload) == 0:
        raise ValueError('No .xml files were found (please specify on the '
                         'command line, or run this script from a directory '
                         'containing one or more .xml files')

    files_uploaded = []
    for f in _tqdm(files_to_upload):
        with open(f, 'r') as xml_file:
            xml_content = xml_file.read()

        title = _os.path.basename(f)
        r = upload_record_content(xml_content, title)

        if r.status_code != 201:
            continue
        else:
            files_uploaded.append(f)

    _logger.info(f'Successfully uploaded {len(files_uploaded)} of '
                 f'{len(files_to_upload)} files')

    return files_uploaded


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Communicate with the Nexus CDCS instance')
    parser.add_argument('--upload-records',
                        help='Upload .xml records to the the Nexus CDCS',
                        action='store_true')
    parser.add_argument('xml',
                        nargs='*',
                        help='(used with --upload-records) '
                             'Files to upload (separated by space and '
                             'surrounded by quotes, if needed). If no files '
                             'are specified, all .xml files in the current '
                             'directory will be used instead.')

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()

    if args.upload_records:
        if len(sys.argv) == 2:
            # no files were provided, so assume the user wanted to glob all
            # .xml files in the current directory
            upload_record_files(None)
        elif len(sys.argv) > 2:
            upload_record_files(args.xml)
