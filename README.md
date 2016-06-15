# openstack-stackops-lifecycle
## What is openstack-stackops-lifecycle

When a new user is registered in StackOps Portal, it enables the first available disabled tenant. Then the following process starts.

## Trial creation

When a user a is assigned to a newly enabled tenant, then the status in Chargeback is changed to TRIAL, and a promo code is assigned.

The user can use the platform for the credit in the promo code.

The process that checks what accounts are in CREATED state is **bulk_trial_tenant.py**. If in created state, then **trial_tenant.py** is executed.


## Activation

When a user increases its balance, or the 'credit' flag in Chargeback is enabled (for example after registering a credit  card), then the process changes the status to ACTIVE.

The process that checks what accounts are in TRIAL state is **bulk_activate_tenant.py**. If in trial state, then **activate_tenant.py** is executed.

## Check if trial is going to expire soon

If the trial is close to its expiration date, the system can send an email to the user reminding her to active the service.

The process name is **find_trial_expire_soon.py**

## Check if trial is expired

If the trial is expired, the system can send an email to the user warning of it as a last action call.

The process name is **find_trial_expired.py**

## Find negative balances

Checks the list of prepaid mode users and sends an email if the balance is negative. It does not suspend the service, this is an action performed in a different process.

The process name is **find_negative_balances.py**
