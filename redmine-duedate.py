#!/usr/bin/python
# -*- coding: utf-8
#

import argparse
import os
import sys
import mysql.connector
from mysql.connector import errorcode


PROG = os.path.basename(sys.argv[0]).rstrip('.py')
PROG_DESC = 'Send notification for redmine issue due date'

QUERY_24X7 = """
SELECT `issues`.`id`,
`issues`.`subject` AS 'Issue',
`issue_statuses`.`name` AS 'Status',
`custom_values`.`value` AS 'SLA',
`issues`.`created_on` AS 'Created',
DATE_ADD(`issues`.`created_on`, INTERVAL 2 HOUR) AS 'sla_due_time',
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
DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY) AS 'sla_due_time',
`issues`.`due_date`
FROM `issues`, `issue_statuses`, `custom_values`, `custom_fields`
WHERE
`issue_statuses`.`id`=`issues`.`status_id` AND `issue_statuses`.`is_closed`=0 AND
`custom_values`.`customized_id`=`issues`.`project_id` AND `custom_values`.`value`= '5x8' AND
`custom_fields`.`id`=`custom_values`.`custom_field_id` AND `custom_fields`.`name`='SLA' AND 
DATE_ADD(`issues`.`created_on`, INTERVAL 1 DAY) < NOW()
"""

QUERY_HEAD_FORMAT = u'| {:>6s} | {:25.25s} | {:10.10s} | {:5} | {:16s} | {:16s} |'
QUERY_DATA_FORMAT = u'| {:6d} | {:25.25s} | {:10.10s} | {:5} | {:%Y-%m-%d %H:%M} | {:%Y-%m-%d %H:%M} |'
QUERY_REPORT = """%s
UNION
%s
ORDER BY `SLA`, `Created`
""" % (QUERY_24X7, QUERY_5X8)

def send_notifications(config):
    print("Send")
    try:
        cnx = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cursor = cnx.cursor()
        cursor.execute(SELECT_5x8)
        for data in cursor:
            print data
        cursor.close()
        cnx.close()


class RmClient(object):

    cnx = None
    cursor = None

    def __init__(self, my_config):
        super(RmClient, self).__init__()
        try:
            self.cnx = mysql.connector.connect(**my_config)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            self.cursor = self.cnx.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.cnx:
            self.cnx.close()

    def send_notifications(self):
        print("Send")
        self.cursor.execute(QUERY_REPORT)
        print(QUERY_HEAD_FORMAT.format('ID', 'Subject', 'Status', 'SLA', 'Created', 'Due time'))
        for data in self.cursor:
            print(QUERY_DATA_FORMAT.format(data[0], data[1], data[2], data[3], data[4], data[5]))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=PROG_DESC)
    parser.add_argument('-r', '--redmine')
    parser.add_argument('-u', '--username')
    parser.add_argument('-p', '--password')
    parser.add_argument('-d', '--database', default='redmine')
    parser.add_argument('-f', '--fix', action='store_true', help="Fix the due date")
    parser.add_argument('-s', '--send', action='store_true', help="Send notifications")

    args = parser.parse_args()

    if args.redmine and args.username and args.password:
        config = {
            'user': args.username,
            'password': args.password,
            'host': args.redmine,
            'database': args.database,
            'raise_on_warnings': True,
        }
        client=RmClient(config)
        if args.fix:
            pass
        if args.send:
            client.send_notifications()

        client.close()
    else:
        parser.print_help()

