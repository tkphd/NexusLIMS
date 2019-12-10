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

# Code must be able to work under Python 3.4 (32-bit) due to limitations of
# the Windows XP-based microscope PCs. Using this version of Python with
# pyinstaller 3.5 seems to work on the 642 Titan

import sqlite3
import re
import datetime
import os
import argparse
import subprocess
from uuid import uuid4


class DBSessionLogger:
    ip_regex = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}' \
               r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'

    def __init__(self,
                 verbosity=0,
                 testing=False,
                 db_name='nexuslims_db.sqlite',
                 user=None,
                 hostname='***REMOVED***'):
        """

        Parameters
        ----------
        verbosity : int
        testing
        db_name
        user : str
            The user to attach to this record
        """
        self.log_text = ""
        self.verbosity = verbosity
        self.testing = testing
        self.db_name = db_name
        self.user = user
        self.hostname = hostname

        if self.testing:
            # Values for testing from local machine
            self.db_path = '/mnt/cfs2e_nexuslims/'
            self.password = None
            self.full_path = os.path.join(self.db_path, self.db_name)
            self.cpu_name = "***REMOVED***"
            self.user = '***REMOVED***'
            self.log('TEST: Using {} as path to db'.format(self.full_path), 2)
            self.log('TEST: Using {} as cpu name'.format(self.cpu_name), 2)
        else:
            # actual values to use in production
            self.db_path = '\\***REMOVED***\\nexuslims'
            self.password = os.environ['MMFQUANT_PASS']
            self.full_path = "N:\\{}".format(db_name)
            self.cpu_name = os.environ['COMPUTERNAME']

        self.session_id = str(uuid4())
        self.instr_pid = None

    def log(self, to_print, this_verbosity):
        """
        Log a message to the console, only printing if the given verbosity is
        equal to or lower than the global threshold. Also save it in this
        instance's ``log`` attribute (regardless of verbosity)

        Parameters
        ----------
        to_print : str
            The message to log
        this_verbosity : int
            The verbosity level (higher is more verbose)
        """
        level_dict = {0: 'WARN', 1: 'INFO', 2: 'DEBUG'}
        str_to_log = '{}'.format(datetime.datetime.now().isoformat()) + \
                     ':{}: '.format(level_dict[this_verbosity]) + \
                     '{}'.format(to_print)
        if this_verbosity <= self.verbosity:
            print(str_to_log)
        self.log_text += str_to_log + '\n'

    def run_cmd(self, cmd):
        """
        Run a command using the subprocess module and return the output

        Parameters
        ----------
        cmd : str
            The command to run (will be run in a new Windows `cmd` shell).
            ``stderr`` will be redirected for ``stdout`` and included in the
            returned output

        Returns
        -------
        p : str
            The output of ``cmd``
        """
        try:
            p = subprocess.check_output(cmd,
                                        shell=True,
                                        stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError as e:
            p = e.output.decode()
            self.log('command {} returned with error (code {}): {}'.format(
                e.cmd.replace(self.password, '**************'),
                e.returncode,
                e.output), 0)
        return p

    def mount_network_share(self):
        """
        Mount the path containing the database to the N: drive (forcefully
        unmounting anything present there) using Windows `cmd`. Due to some
        Windows limitations, this requires looking up the server's IP address
        and mounting using the IP rather than the actual domain name
        """
        # disconnect anything mounted at "N:/"
        self.log('unmounting existing N:', 2)
        _ = self.run_cmd(r'net use N: /delete /y')

        # Connect to shared drive, windows does not allow multiple connections
        # to the same server, but you can trick it by using IP address
        # instead of DNS name... nslookup command sometimes fails,
        # but parsing the output of ping seems to work
        self.log('getting ip of {}'.format(self.hostname), 2)
        p = self.run_cmd(r'ping {} -n 1'.format(self.hostname))
        self.log('output of ping: {}'.format(p), 2)

        # The second line contains "pinging hostname [ip]..."
        ip = None
        have_ip = False
        try:
            ip_line = p.split('\r\n')[1]
            ips = re.findall(DBSessionLogger.ip_regex, ip_line)
            have_ip = True
            if len(ips) == 1:
                ip = ips[0]
            else:
                raise EnvironmentError('Could not find IP of network share in '
                                       'output of nslookup command')
            self.log('found cfs2e at {}'.format(ip), 2)
        except ValueError as e:
            self.log('nslookup command failed; using hostname instead', 0)

        mount_command = 'net use N: \\\\{}{} '.format(ip if have_ip else
                                                      self.hostname,
                                                      self.db_path) + \
                        '/user:***REMOVED*** {}'.format(self.password)
        if self.testing:
            mount_command = 'net use N: \\\\{}{} ' \
                            '/user:NIST\\***REMOVED***'.format(ip if have_ip else
                                                     self.hostname,
                                                     self.db_path)
        self.log('mounting N:', 2)

        # mounting requires a security policy:
        # https://support.microsoft.com/en-us/help/968264/error-message-when-
        # you-try-to-map-to-a-network-drive-of-a-dfs-share-by

        self.log('using "{}'.format(mount_command).replace(self.password,
                                                           '**************'), 2)
        p = self.run_cmd(mount_command)

        if 'error' in str(p):
            if '1312' in str(p):
                self.log('Visit https://support.microsoft.com/en-us/help/'
                         '968264/error-message-when-you-try-to-map-to-a-'
                         'network-drive-of-a-dfs-share-by\n'
                         'to see how to allow mounting network drives as '
                         'another user.\n'
                         '(You\'ll need to change HKLM\\System\\'
                         'CurrentControlSet\\Control\\Lsa\\DisableDomanCreds '
                         'to 0 in the registry)', 0)
            raise ConnectionError('Could not mount network share to access '
                                  'database')

    def umount_network_share(self):
        """
        Unmount the network share at N: using the Windows `cmd`
        """
        self.log('unmounting N:', 2)
        p = self.run_cmd(r'net use N: /del /y')
        if 'error' in str(p):
            self.log(str(p), 0)

    def get_instr_pid(self):
        """
        Using the name of this computer, get the matching instrument PID from
        the database

        Returns
        -------
        instrument_pid : str
            The PID for the instrument corresponding to this computer
        """
        # Get the instrument pid from the computer name of this computer
        with sqlite3.connect(self.full_path) as con:
            res = con.execute('SELECT instrument_pid from instruments WHERE '
                              'computer_name is \'{}\''.format(self.cpu_name))
            instrument_pid = res.fetchone()[0]
            self.log('Found instrument ID: {} using '.format(instrument_pid) +
                     '{}'.format(self.cpu_name), 1)
        return instrument_pid

    def process_start(self):
        """
        Insert a session `'START'` log for this computer's instrument
        """
        insert_statement = "INSERT INTO session_log (instrument, " \
                           " event_type, session_identifier" + \
                           (", user)" if self.user else ") ") + \
                           "VALUES ('{}', 'START', ".format(self.instr_pid) + \
                           "'{}'".format(self.session_id) + \
                           (", '{}');".format(self.user) if self.user else ");")

        self.log('insert_statement: {}'.format(insert_statement), 2)

        # Get last entered row with this session_id (to make sure it's correct)
        with sqlite3.connect(self.full_path) as con:
            _ = con.execute(insert_statement)
            r = con.execute("SELECT * FROM session_log WHERE "
                            "session_identifier='{}' ".format(self.session_id) +
                            "AND event_type = 'START'"
                            "ORDER BY timestamp DESC " +
                            "LIMIT 1;")
            id_session_log = r.fetchone()
            self.log('Inserted row {}'.format(id_session_log), 1)

    def process_end(self):
        """
        Insert a session `'END'` log for this computer's instrument,
        and change the status of the corresponding `'START'` entry from
        `'WAITING_FOR_END'` to `'TO_BE_BUILT'`
        """
        user_string = "AND user='{}'".format(self.user) if self.user else ''

        insert_statement = "INSERT INTO session_log " \
                           "(instrument, event_type, " \
                           "record_status, session_identifier" + \
                           (", user) " if self.user else ") ") + \
                           "VALUES ('{}',".format(self.instr_pid) + \
                           "'END', 'TO_BE_BUILT', " + \
                           "'{}'".format(self.session_id) + \
                           (", '{}');".format(self.user) if self.user else ");")

        # Get the most 'START' entry for this instrument and session id
        get_last_start_id_query = "SELECT id_session_log FROM session_log " + \
                                  "WHERE instrument = " + \
                                  "'{}' ".format(self.instr_pid) + \
                                  "AND event_type = 'START' " + \
                                  "{} ".format(user_string) + \
                                  "AND session_identifier = " + \
                                  "'{}'".format(self.session_id) + \
                                  "AND record_status = 'WAITING_FOR_END';"
        self.log('query: {}'.format(get_last_start_id_query), 2)

        with sqlite3.connect(self.full_path) as con:
            self.log('Inserting END; insert_statement: {}'.format(
                insert_statement), 2)
            _ = con.execute(insert_statement)

            res = con.execute('SELECT * FROM session_log WHERE '
                              'id_session_log = last_insert_rowid();')
            id_session_log = res.fetchone()
            self.log('Inserted row {}'.format(id_session_log), 1)

            res = con.execute(get_last_start_id_query)
            results = res.fetchall()
            if len(results) == 0:
                raise LookupError("No matching 'START' event found")
            elif len(results) > 1:
                raise LookupError("More than one 'START' event found with "
                                  "session_identifier = "
                                  "'{}'".format(self.session_id))
            last_start_id = results[-1][0]
            self.log('SELECT instrument results: {}'.format(last_start_id), 2)

            # Update previous START event record status
            res = con.execute("SELECT * FROM session_log WHERE " +
                              "id_session_log = {}".format(last_start_id))
            self.log('Row to be updated: {}'.format(res.fetchone()), 1)
            update_statement = "UPDATE session_log SET " + \
                               "record_status = 'TO_BE_BUILT' WHERE " + \
                               "id_session_log = {}".format(last_start_id)
            _ = con.execute(update_statement)

            res = con.execute("SELECT * FROM session_log WHERE " +
                              "id_session_log = {}".format(last_start_id))

            self.log('Row after updating: {}'.format(res.fetchone()), 1)

    def callback_setup(self):
        self.log('username is {}'.format(self.user), 1)
        self.log('running `mount_network_share()`', 2)
        self.mount_network_share()
        self.log('running `get_instr_pid()`', 2)
        self.instr_pid = self.get_instr_pid()

    def callback_teardown(self):
        self.log('running `umount_network_share()`', 2)
        self.umount_network_share()


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(
        description="""This program will mount the nexuslims directory
                       on CFS2E, connect to the nexuslims_db.sqlite
                       database, and insert an entry into the 
                       session log.""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    p.add_argument("event_type", type=str,
                   help="the type of event")
    p.add_argument("user", type=str, nargs='?',
                   help="NIST username associated with this session (current "
                        "windows logon name will be used if not provided)",
                   default=None)
    p.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2], default=0,
                   help="increase output verbosity")

    return p.parse_args()


def gui_start_callback(verbosity=2, testing=False):
    """
    Process the start of a session when the GUI is opened

    Returns
    -------
    db_logger : DBSessionLogger
        The session logger instance for this session (contains all the
        information about instrument, computer, session_id, etc.)
    """
    db_logger = DBSessionLogger(verbosity=verbosity,
                                testing=testing,
                                user=None if testing else
                                os.environ['username'])
    db_logger.callback_setup()
    db_logger.process_start()
    db_logger.callback_teardown()

    return db_logger


def gui_end_callback(db_logger):
    """
    Process the end of a session when the button is clicked or the GUI window
    is closed.

    Parameters
    ----------
    db_logger : DBSessionLogger
        The session logger instance for this session (contains all the
        information about instrument, computer, session_id, etc.)
    """
    db_logger.callback_setup()
    db_logger.process_end()
    db_logger.callback_teardown()


# if __name__ == '__main__':
#
#     log('parsing arguments', 2)
#     args = cmdline_args()
#     verbosity = args.verbosity
#     if not args.user:
#         username = os.environ['username']
#     else:
#         username = args.user
#
#     log('username is {}'.format(username), 1)
#
#     log('running `mount_network_share()`', 2)
#     mount_network_share()
#
#     log('running `get_instr_pid()`', 2)
#     instr_pid = get_instr_pid()
#
#     if args.event_type == 'START':
#         process_start(instr_pid, user=username)
#     elif args.event_type == 'END':
#         process_end(instr_pid, user=username)
#     else:
#         log('running `umount_network_share()`', 2)
#         umount_network_share()
#         error_string = "event_type must be either 'START' or" + \
#                        " 'END'; '{}' provided".format(args.event_type)
#         raise ValueError(error_string)
#
#     log('running `umount_network_share()`', 2)
#     umount_network_share()
