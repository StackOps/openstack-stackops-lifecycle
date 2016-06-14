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

# Find CREATED accounts enabled and execute change to TRIAL process
#
# python bulk_trial_tenant.py ADMIN_PASSWORD
#
#

import sys
import logging
import logging.config
import subprocess
import ConfigParser

from openstacklibs.chargeback import Account
from openstacklibs.keystone import Keystone

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
regexp = config.get('chargeback', 'regexp')
path = config.get('app', 'path')

logger_.debug("USERNAME:%s" % usr)
logger_.debug("TENANT:%s" % admin_tenant_name)
logger_.debug("URL:%s" % keystone_url)
logger_.debug("CH_URL:%s" % chargeback_url)
logger_.debug("REGEXP:%s" % regexp)

passw = str(sys.argv[1])

keystoneObj = Keystone(keystone_url, usr, passw, admin_tenant_name)
accountObj = Account(keystoneObj.getToken(), chargeback_url, filter=regexp)

tenants = keystoneObj.getTenants()
accounts = accountObj.getAll()

tarray = []
for t in tenants["tenants"]:
    if t["enabled"]:
        tarray.append(t["name"])

for account in accounts:
    state = account["status"]
    name = account["name"]
    if state=="CREATED" and name in tarray:
        logger_.info("Account=%s" % name)
        subprocess.call("python %s/trial_tenant.py %s %s %s" % (path,passw,name,initfile), shell=True)
