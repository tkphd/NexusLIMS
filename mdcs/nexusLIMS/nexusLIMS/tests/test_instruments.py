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

from nexusLIMS.instruments import Instrument


class TestInstruments:
    def test_getting_instruments(self):
        from nexusLIMS.instruments import instrument_db
        assert isinstance(instrument_db, dict)

    def test_database_contains_instruments(self):
        from nexusLIMS.instruments import instrument_db
        instruments_to_test = ['***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***',
                               '***REMOVED***']
        for i in instruments_to_test:
            assert i in instrument_db
            assert isinstance(instrument_db[i], Instrument)

        assert 'some_random_instrument' not in instrument_db

    def test_instrument_str(self):
        from nexusLIMS.instruments import instrument_db
        assert \
            str(instrument_db['***REMOVED***']) == \
            '***REMOVED*** in ***REMOVED***'

    def test_instrument_repr(self):
        from nexusLIMS.instruments import instrument_db
        api_url = 'https://***REMOVED***/***REMOVED***/' \
                  '_vti_bin/ListData.svc/***REMOVED***'
        cal_url = 'https://***REMOVED***/***REMOVED***/' \
                  'Lists/***REMOVED***/calendar.aspx'

        assert \
            repr(instrument_db['***REMOVED***']) == \
            'Nexus Instrument:\t***REMOVED***\n' + \
            f'API url:\t\t{api_url}\n' + \
            'Calendar name:\t\tFEI Titan TEM\n' + \
            f'Calendar url:\t\t{cal_url}\n' + \
            'Schema name:\t\tFEI Titan TEM\n' \
            'Location:\t\t***REMOVED***\n' \
            'Property tag:\t\t***REMOVED***\n' \
            'Filestore path:\t\t./Titan\n' \
            'Computer IP:\t\t***REMOVED***\n' \
            'Computer name:\t\t***REMOVED***\n' \
            'Computer mount:\t\tM:/\n'
