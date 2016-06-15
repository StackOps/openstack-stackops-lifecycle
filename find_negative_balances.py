# coding=utf-8

"""
   Copyright 2011-2016 STACKOPS TECHNOLOGIES S.L.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
# Find accounts with negative balance and no credit allowed and send a warning email
#
# python find_negative_balances.py ADMIN_PASSWORD
#
#

import sys
import logging
import logging.config
import ConfigParser
import re
import time
import json

from openstacklibs.chargeback import Account
from openstacklibs.keystone import Keystone
from openstacklibs.mailing import Email
from openstacklibs.mailing import TemplateText
from openstacklibs.database import Portal

numargs = len(sys.argv)
if numargs>2:
    initfile = str(sys.argv[2])
else:
    initfile = "./stackops.ini"

logging.config.fileConfig(initfile)
logger_ = logging.getLogger(__name__)

config = ConfigParser.ConfigParser()
config.read(initfile)

usr = config.get('keystone', 'username')
admin_tenant_name = config.get('keystone', 'tenant')
keystone_url = config.get('keystone', 'url')

chargeback_url = config.get('chargeback', 'url')
regexpStr = config.get('find_negative_balances', 'regexp')

mail_server = config.get('email', 'server')
mail_username = config.get('email', 'username')
mail_password = config.get('email', 'password')
mail_bcc = config.get('email', 'bcc')
mail_from = config.get('email', 'from')

template_portal_url = config.get('templates', 'portal_url')
template_folder = config.get('templates', 'folder')
template_subject_es = config.get('find_negative_balances', 'find_negative_subject_es')
template_subject_en = config.get('find_negative_balances', 'find_negative_subject_en')
template_file_es = config.get('find_negative_balances', 'find_negative_file_es')
template_file_en = config.get('find_negative_balances', 'find_negative_file_en')

database_server = config.get('portal_database', 'server')
database_username = config.get('portal_database', 'username')
database_password = config.get('portal_database', 'password')
database_schema = config.get('portal_database', 'schema')

folder_out = config.get('find_negative_balances','folder_out')

cmdargs = str(sys.argv)
passw = str(sys.argv[1])
regexp = re.compile(regexpStr)

logger_.debug("USERNAME:%s" % usr)
logger_.debug("TENANT:%s" % admin_tenant_name)
logger_.debug("URL:%s" % keystone_url)
logger_.debug("CH_URL:%s" % chargeback_url)
logger_.debug("REGEXP:%s" % regexpStr)
logger_.debug("MAIL_SERVER:%s" % mail_server)
logger_.debug("MAIL_USERNAME:%s" % mail_username)
logger_.debug("MAIL_BCC:%s" % mail_bcc)
logger_.debug("MAIL_FROM:%s" % mail_from)
logger_.debug("TEMPLATE_PORTAL_URL:%s" % template_portal_url)
logger_.debug("TEMPLATE_SUBJECT_ES:%s" % template_subject_es)
logger_.debug("TEMPLATE_SUBJECT_EN:%s" % template_subject_en)
logger_.debug("TEMPLATE_FILE_ES:%s" % template_file_es)
logger_.debug("TEMPLATE_FILE_EN:%s" % template_file_en)

keystoneObj = Keystone(keystone_url, usr, passw, admin_tenant_name)
accountObj = Account(keystoneObj.getToken(), chargeback_url, filter=regexp)
emailObj = Email(mail_username, mail_password, mail_from, mail_bcc, mail_server)
templateObj = TemplateText(template_folder)
databaseObj = Portal(database_server, database_username, database_password, schema=database_schema)

tenants = keystoneObj.getTenants()["tenants"]
accounts1 = accountObj.getAll(status="ACTIVE")
accounts2 = accountObj.getAll(status="TRIAL")

accounts = accounts1 + accounts2

negative_balances = []
for billable_account in accounts:
    emails = []
    country = "es"
    id = billable_account["id"]
    if billable_account["accountBilling"] is not None:
        emails.append(billable_account["accountBilling"]["contactEmail"])
        country = billable_account["accountBilling"]["country"]
    else:
        keystoneObj = Keystone(keystone_url, usr, passw, billable_account["name"])
        users = keystoneObj.getTenantUsersNonAdmin()
        emails = []
        for user in users:
            email = user["email"]
            if len(email)>0:
                emails.append(email)
                country = databaseObj.getUserLanguage(email)
    status = accountObj.getStatus(id)
    usage = status["bag"]["usage"]
    total = status["bag"]["total"]
    name = billable_account["name"]
    allow_credit = billable_account["allowCredit"]
    if allow_credit is None:
        allow_credit = False
    if not allow_credit:
        if usage > total:
            negative_balances.append({"account":name,"emails":emails,"country":country, "total":total, "usage":usage, "balance": "{:1.2f}".format(total - usage)})
            usage_ = "%s not enough funds (%s). Country=%s Balance=%s Total=%s" % (name, emails, country, total, "{:1.2f}".format(usage))
            logger_.info(usage_)
            params = {'account':name.encode('ascii', 'ignore'), 'balance':"{:1.2f}".format(total), 'usage':"{:1.2f}".format(usage)}
            if country.lower() == "es":
                subj = template_subject_es
                msg = templateObj.substitute(template_file_es,params)
            else:
                subj = template_subject_en
                msg = templateObj.substitute(template_file_en,params)
            if len(emails)>0:
                emailObj.send(emails, subj, msg)

with open('%s/negative_balances-%s.json' % (folder_out, time.strftime("%Y-%m-%d")), 'w') as outfile:
  json.dump(negative_balances, outfile, sort_keys=True, indent=4, separators=(',', ': '))
