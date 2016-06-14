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

# Find TRIAL accounts with positive balance or credit flag enabled and execute activation process
#
# python bulk_activate_tenant.py ADMIN_PASSWORD [email]
#
# If added 'email', then the email is sent. Otherwise, only reported on screen.
#

import sys
import logging
import logging.config
import subprocess
import ConfigParser

from openstacklibs.chargeback import Account
from openstacklibs.keystone import Keystone

numargs = len(sys.argv)
if numargs > 3:
    initfile = str(sys.argv[3])
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
regexp = config.get('chargeback', 'regexp')
path = config.get('app', 'path')

logger_.debug("USERNAME:%s" % usr)
logger_.debug("TENANT:%s" % admin_tenant_name)
logger_.debug("URL:%s" % keystone_url)
logger_.debug("CH_URL:%s" % chargeback_url)
logger_.debug("REGEXP:%s" % regexp)

total = len(sys.argv)
cmdargs = str(sys.argv)
passw = str(sys.argv[1])
balance = str(sys.argv[2])

keystoneObj = Keystone(keystone_url, usr, passw, admin_tenant_name)
accountObj = Account(keystoneObj.getToken(), chargeback_url, filter=regexp)

tenants = keystoneObj.getTenants()["tenants"]
accounts = accountObj.getAll(status="TRIAL")

negative_balances = []
emails_csv_es = []
emails_csv_en = []
for account in accounts:
    emails = []
    country = "es"
    id = account["id"]
    state = account["status"]
    name = account["name"]
    allow_credit = account["allowCredit"]
    if state == "TRIAL":
        status = accountObj.getStatus(id)
        usage = status["bag"]["usage"]
        if usage is None:
            usage = 0.0
        total = status["bag"]["total"]
        logger_.info("Account=%s, Total=%s, Usage=%s, Balance=%s" % (name, total, usage, (total - usage)))
        if int(total) >= int(balance) or allow_credit:
            my_tenant = [x for x in tenants if x["name"] == name][0]
            if (int(total) >= int(balance) or allow_credit) and my_tenant["enabled"]:
                logger_.info("Account=%s, Total=%s, Usage=%s, Balance=%s" % (name, total, usage, (total - usage)))
                subprocess.call("python %s/activate_tenant.py %s %s %s" % (path, passw, name, initfile), shell=True)
