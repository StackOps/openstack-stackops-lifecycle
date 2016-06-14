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
