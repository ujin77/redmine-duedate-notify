#!/usr/bin/python
# -*- coding: utf-8
#

import argparse
import os
import sys
import mysql.connector
from mysql.connector import errorcode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ConfigParser
import json


PROG = os.path.basename(sys.argv[0]).rstrip('.py')
PROG_DESC = 'Send notification for redmine issue due date'

DEFAULT_CONFIG = {
    'name': PROG,
    'mail': {
        'to':   'test@domain.local',
        'from': 'test@domain.local',
        'host': 'smtp.domain.local',
        'user': 'test@domain.local',
        'password': 'password',
        'port': 465,
        'subject': 'TEST'
    },
    'redmine': {
        'host': 'localhost',
        'password': 'password',
        'user': 'user',
        'database': 'redmine'
    }
}

QUERY_HOSTNAME = "SELECT `value` FROM `settings` WHERE `name` = 'host_name'"
QUERY_PROTOCOL = "SELECT `value` FROM `settings` WHERE `name` = 'protocol'"

QUERY_24X7 = """
SELECT `issues`.`id`,
`issues`.`subject` AS 'Issue',
`issue_statuses`.`name` AS 'Status',
`custom_values`.`value` AS 'SLA',
`issues`.`created_on` AS 'Created',
DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR) AS 'SLA_due_time',
`issues`.`due_date`
FROM `issues`, `issue_statuses`, `custom_values`, `custom_fields`
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '24x7' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND 
DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR) < NOW()
"""
QUERY_5X8="""
SELECT `issues`.`id`,
`issues`.`subject` AS 'Issue',
`issue_statuses`.`name` AS 'Status',
`custom_values`.`value` AS 'SLA',
`issues`.`created_on` AS 'Created',
DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY) AS 'SLA_due_time',
`issues`.`due_date`
FROM `issues`, `issue_statuses`, `custom_values`, `custom_fields`
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '5x8' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND 
DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY) < NOW()
"""

HTML_STYLE = """
<style>
table { border-collapse: collapse; }
th, td {
    border: 1px solid gray;
    padding-right: 6px;
    padding-left: 6px;
}
a {text-decoration: none}
</style>
"""

HTML_FORMAT = """
<html>
<head>
{STYLE}
</head>
<body>
<p>
<ul>
<li>SLA: 24x7 - Not closed problems for more than 2 hours
<li>SLA: 5x8 - Not closed problems for more than 1 day
</ul>
</p>
{DATA}
</body></html>
"""
EMAIL_FORMAT = 'From: {}\r\nTo: {}\r\nSubject: {}\r\n\r\n{}'
QUERY_HEAD_FORMAT = u'| {:>6s} | {:25.25s} | {:20.20s} | {:5} | {:16s} | {:16s} |'
QUERY_DATA_FORMAT = u'| {:6d} | {:25.25s} | {:20.20s} | {:5} | {:%Y-%m-%d %H:%M} | {:%Y-%m-%d %H:%M} |'
REPORT_HEAD = u'<TABLE>\n<TR><TD>{}</TD><TD>{}</TD><TD>{}</TD><TD>{}</TD><TD>{}</TD></TR>\n'
REPORT_DATA = u"""<TR>
<TD><A href={url}{id}>{issue} <b>#{id}</b></A></TD>
<TD>{status}</TD>
<TD>{sla}</TD>
<TD>{created}</TD>
<TD>{duetime}</TD>
</TR>\n"""
REPORT_FOOT = u'</TABLE>\n'

QUERY_REPORT = """%s
UNION
%s
ORDER BY `SLA`, `Created`
""" % (QUERY_24X7, QUERY_5X8)

# QUERY_REPORT = QUERY_24X7


class RmClient(object):

    cnx = None
    cursor = None
    issue_url = ''

    def __init__(self, _config):
        super(RmClient, self).__init__()
        self._config = _config
        try:
            self.cnx = mysql.connector.connect(**self._config['redmine'])
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            self.cursor = self.cnx.cursor()
            self._get_url()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.cnx:
            self.cnx.close()

    def _get_url(self):
        self.cursor.execute(QUERY_HOSTNAME)
        host = ''.join(self.cursor.fetchone())
        self.cursor.execute(QUERY_PROTOCOL)
        proto = ''.join(self.cursor.fetchone())
        self.issue_url = "%s://%s/issues/" % (proto, host)

    def send_notifications(self):
        result = False
        self.cursor.execute(QUERY_REPORT)
        message = REPORT_HEAD.format(
                                     self.cursor.column_names[1],
                                     self.cursor.column_names[2],
                                     self.cursor.column_names[3],
                                     self.cursor.column_names[4],
                                     self.cursor.column_names[5]
                                     )
        for data in self.cursor:
            result = True
            message += REPORT_DATA.format(url=self.issue_url,
                                          id=data[0],
                                          issue=data[1],
                                          status=data[2],
                                          sla=data[3],
                                          created=data[4],
                                          duetime=data[5]
                                          )
            if self._config['verbose']:
                print(QUERY_DATA_FORMAT.format(data[0],
                                     data[1],
                                     data[2],
                                     data[3],
                                     data[4],data[5]))

        if result:
            message += REPORT_FOOT
            if self._config['debug']:
                print message
            self._send_mail(message.encode('utf-8'))
        else:
            if self._config['verbose']:
                print('No issues')

    def _send_mail(self, message):
        html = HTML_FORMAT.format(STYLE=HTML_STYLE, DATA=message)
        msg = MIMEMultipart('alternative', None, [MIMEText(html, 'html','utf-8')])
        msg['Subject'] = self._config['mail']['subject']
        msg['From'] = self._config['mail']['from']
        msg['To'] = self._config['mail']['to']
        server = smtplib.SMTP_SSL(self._config['mail']['host'],self._config['mail']['port'])
        if self._config['debug']:
            server.set_debuglevel(1)
        server.login(self._config['mail']['user'], self._config['mail']['password'])
        server.sendmail(self._config['mail']['from'], self._config['mail']['to'].split(','), msg.as_string())
        server.quit()

def load_config(fname):
    if os.path.isfile(fname):
        config = ConfigParser.ConfigParser(allow_no_value=True)
        try:
            config.readfp(open(fname))
            for section in config.sections():
                for (name, value) in config.items(section):
                    if not DEFAULT_CONFIG.get(section): DEFAULT_CONFIG[section]={}
                    DEFAULT_CONFIG[section][name] = value.strip("'\"")
        except ConfigParser.MissingSectionHeaderError as e:
            print e
        except Exception as e:
            print e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=PROG_DESC)
    parser.add_argument('-c', '--config', default='/etc/'+ PROG +'.conf')
    parser.add_argument('-f', '--fix', action='store_true', help="Fix the due date")
    parser.add_argument('-s', '--send', action='store_true', help="Send notifications")
    parser.add_argument('-d', '--debug', action='store_true', help="Debug output")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose output")
    args = parser.parse_args()

    if args.config: load_config(args.config)
    DEFAULT_CONFIG['verbose'] = args.verbose
    DEFAULT_CONFIG['debug'] = args.debug
    if args.debug:
        print 'CONFIG:', json.dumps(DEFAULT_CONFIG, indent=2)

    if args.fix or args.send:
        client = RmClient(DEFAULT_CONFIG)
        if args.fix:
            pass
        if args.send:
            client.send_notifications()

        client.close()
    else:
        parser.print_help()
