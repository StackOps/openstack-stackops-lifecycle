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

#  Change to trial account adding PROMO code and creating zendesk support account
#
#  python trial_tenant.py PASSWORD TENANT_NAME
#

import sys
import logging
import logging.config
import ConfigParser
import re

from openstacklibs.chargeback import Account
from openstacklibs.keystone import Keystone
from openstacklibs.zendesk import Zendesk

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

zendesk_url = config.get('zendesk', 'url')
zendesk_username = config.get('zendesk', 'username')
zendesk_password = config.get('zendesk', 'password')

cmdargs = str(sys.argv)
pasw = str(sys.argv[1])
os_tenant_name = str(sys.argv[2])
regexp = re.compile(regexpStr)

logger_.debug("USERNAME:%s" % usr)
logger_.debug("TENANT:%s" % os_tenant_name)
logger_.debug("URL:%s" % keystone_url)
logger_.debug("CH_URL:%s" % chargeback_url)
logger_.debug("REGEXP:%s" % regexpStr)
logger_.debug("ZENDESK_USERNAME:%s" % zendesk_username)
logger_.debug("ZENDESK_URL:%s" % zendesk_url)

PROMO_CODE="TRIAL10"

keystoneObj = Keystone(keystone_url, usr, pasw, os_tenant_name)
accountObj = Account(keystoneObj.getToken(), chargeback_url, filter=regexp)
zendeskObj = Zendesk(zendesk_url, zendesk_username, zendesk_password)

account = accountObj.getCurrent()

if regexp.match(account["account"]["name"]):
    emails = []
    users = keystoneObj.getTenantUsersNonAdmin()
    for user in users:
        email = user["email"]
        if len(email)>0:
            emails.append(email)
    if len(emails)>0:
        account["account"]["status"] = "TRIAL"
        account_id = account["account"]["id"]
        result = accountObj.update(account_id, account)
        result = accountObj.enterPromoCurrent(PROMO_CODE)
        organization_id = zendeskObj.createOrganization(os_tenant_name)
        user_id = zendeskObj.createUser(emails[0],emails[0],organization_id)
