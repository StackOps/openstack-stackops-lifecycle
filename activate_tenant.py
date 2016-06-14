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
#
#  Change to ACTIVE account and send welcome email
#
#  python activate_tenant.py PASSWORD TENANT_NAME
#


import sys
import logging
import logging.config
import ConfigParser
import re

from openstacklibs.chargeback import Account
from openstacklibs.keystone import Keystone
from openstacklibs.mailing import Email
from openstacklibs.mailing import TemplateText
from openstacklibs.database import Portal

numargs = len(sys.argv)
if numargs>3:
    initfile = str(sys.argv[3])
else:
    initfile = "./stackops.ini"

logging.config.fileConfig(initfile)
logger_ = logging.getLogger(__name__)

config = ConfigParser.ConfigParser()
config.read(initfile)

usr = config.get('keystone', 'username')
keystone_url = config.get('keystone', 'url')

chargeback_url = config.get('chargeback', 'url')
regexpStr = config.get('chargeback', 'regexp')

mail_server = config.get('email', 'server')
mail_username = config.get('email', 'username')
mail_password = config.get('email', 'password')
mail_bcc = config.get('email', 'bcc')
mail_from = config.get('email', 'from')

template_portal_url = config.get('templates', 'portal_url')
template_folder = config.get('templates', 'folder')
template_subject_es = config.get('templates', 'activate_subject_es')
template_subject_en = config.get('templates', 'activate_subject_en')
template_file_es = config.get('templates', 'activate_file_es')
template_file_en = config.get('templates', 'activate_file_en')

database_server = config.get('portal_database', 'server')
database_username = config.get('portal_database', 'username')
database_password = config.get('portal_database', 'password')
database_schema = config.get('portal_database', 'schema')

cmdargs = str(sys.argv)
pasw = str(sys.argv[1])
os_tenant_name = str(sys.argv[2])
regexp = re.compile(regexpStr)

logger_.debug("USERNAME:%s" % usr)
logger_.debug("TENANT:%s" % os_tenant_name)
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

keystoneObj = Keystone(keystone_url, usr, pasw, os_tenant_name)
accountObj = Account(keystoneObj.getToken(), chargeback_url, filter=regexp)
emailObj = Email(mail_username, mail_password, mail_from, mail_bcc, mail_server)
templateObj = TemplateText(template_folder)
databaseObj = Portal(database_server, database_username, database_password, schema=database_schema)

account = accountObj.getCurrent()

account["account"]["status"] = "ACTIVE"
account_id = account["account"]["id"]
result = accountObj.update(account_id, account)

if regexp.match(account["account"]["name"]):
    country = "es"
    users = keystoneObj.getTenantUsersNonAdmin()
    emails = []
    for user in users:
        email = user["email"]
        if len(email)>0:
            emails.append(email)
            country = databaseObj.getUserLanguage(email)
    if country.lower() == "es":
        subj = template_subject_es
        msg = templateObj.substitute(template_file_es,{'portal':template_portal_url})
    else:
        subj = template_subject_en
        msg = templateObj.substitute(template_file_en,{'portal':template_portal_url})
    emailObj.send(emails, subj, msg)
