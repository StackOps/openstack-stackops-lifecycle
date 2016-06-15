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
# Find accounts with the trial close to expire and send an email reporting it
#
# python find_trial_expire_soon.py ADMIN_PASSWORD
#
#

import sys
import logging
import logging.config
import ConfigParser
import re
import time
import datetime
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
regexpStr = config.get('find_trial_expire_soon', 'regexp')

mail_server = config.get('email', 'server')
mail_username = config.get('email', 'username')
mail_password = config.get('email', 'password')
mail_bcc = config.get('email', 'bcc')
mail_from = config.get('email', 'from')

template_portal_url = config.get('templates', 'portal_url')
template_folder = config.get('templates', 'folder')
template_subject_es = config.get('find_trial_expire_soon', 'subject_es')
template_subject_en = config.get('find_trial_expire_soon', 'subject_en')
template_file_es = config.get('find_trial_expire_soon', 'file_es')
template_file_en = config.get('find_trial_expire_soon', 'file_en')

database_server = config.get('portal_database', 'server')
database_username = config.get('portal_database', 'username')
database_password = config.get('portal_database', 'password')
database_schema = config.get('portal_database', 'schema')

folder_out = config.get('find_trial_expire_soon','folder_out')
warning_days = config.get('find_trial_expire_soon','warning_days')
expired_days = config.get('find_trial_expire_soon','expired_days')
marketing_email = config.get('find_trial_expire_soon','email')

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
accounts = accountObj.getAll(status="TRIAL")

expired_trial = []
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
    history = status["bag"]["history"]
    promo = [x for x in history if "TRIAL10" in x["description"]]
    if len(promo)>0:
        w_days =  ((int(datetime.datetime.now().strftime('%s')) - promo[0]["timestamp"]) / 86400) - int(warning_days)
        toexpire_days = int(expired_days) - ((int(datetime.datetime.now().strftime('%s')) - promo[0]["timestamp"]) / 86400)
        expired_trial.append({"days":toexpire_days, "account":name,"emails":emails,"country":country, "total":total, "usage":usage, "balance": "{:1.2f}".format(total - usage)})
        params = {'account':name.encode('ascii', 'ignore'), 'balance':"{:1.2f}".format(total), 'usage':"{:1.2f}".format(usage), "days":toexpire_days}
        if w_days==0:
            if country.lower() == "es":
                subj = template_subject_es
                msg = templateObj.substitute(template_file_es,params)
            else:
                subj = template_subject_en
                msg = templateObj.substitute(template_file_en,params)
            if len(emails)>0:
                if len(marketing_email)>0:
                    emailObj.send(emails, subj, msg)

            with open('%s/trial_expire_soon-%s.json' % (folder_out, time.strftime("%Y-%m-%d")), 'w') as outfile:
                json.dump(expired_trial, outfile, sort_keys=True, indent=4, separators=(',', ': '))
