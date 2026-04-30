#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Leonardo Gallego
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: netbox_event_rule
short_description: Creates, updates, or deletes event rules within NetBox
description:
  - Creates, updates, or removes event rules within NetBox
  - Event rules trigger actions (webhooks, scripts, notifications) in response to object changes
notes:
  - This should be ran with connection C(local) and hosts C(localhost)
  - Requires NetBox >= 3.6 (when event rules were split from webhooks)
author:
  - Leonardo Gallego (@leogallego)
requirements:
  - pynetbox
version_added: "1.1.0"
extends_documentation_fragment:
  - netbox.netbox.common
options:
  data:
    type: dict
    description:
      - Defines the event rule configuration
    suboptions:
      name:
        description:
          - Unique name for the event rule
        required: true
        type: str
      object_types:
        description:
          - Content types to watch for changes (e.g., C(dcim.device), C(circuits.circuit))
          - Required when I(state=present)
        required: false
        type: list
        elements: str
      event_types:
        description:
          - "Events to trigger on: C(object_created), C(object_updated), C(object_deleted),
            C(job_started), C(job_completed), C(job_failed), C(job_errored)"
          - Required when I(state=present)
        required: false
        type: list
        elements: str
      enabled:
        description:
          - Whether the event rule is active
        required: false
        type: bool
      action_type:
        description:
          - Type of action to trigger
          - One of C(webhook), C(script), C(notification)
          - Required when I(state=present)
        required: false
        type: str
        choices:
          - webhook
          - script
          - notification
      action_object_name:
        description:
          - Name of the webhook, script, or notification to trigger
          - Mutually exclusive with I(action_object_id)
          - Exactly one of I(action_object_name) or I(action_object_id) is required when I(state=present)
        required: false
        type: str
      action_object_id:
        description:
          - Database ID of the webhook, script, or notification to trigger
          - Mutually exclusive with I(action_object_name)
          - Exactly one of I(action_object_name) or I(action_object_id) is required when I(state=present)
        required: false
        type: int
      conditions:
        description:
          - JSON conditions for selective triggering
        required: false
        type: dict
      action_data:
        description:
          - Additional JSON data passed to the action
        required: false
        type: dict
      description:
        description:
          - Description of the event rule
        required: false
        type: str
      comments:
        description:
          - Comments about the event rule
        required: false
        type: str
      tags:
        description:
          - Tags to apply to the event rule
        required: false
        type: list
        elements: raw
      custom_fields:
        description:
          - Custom field values for the event rule
        required: false
        type: dict
    required: true
"""

EXAMPLES = r"""
- name: Create event rule for device changes (webhook by name)
  leogallego.netbox.netbox_event_rule:
    netbox_url: http://netbox.local
    netbox_token: thisIsMyToken
    data:
      name: Device change alert
      object_types:
        - dcim.device
      event_types:
        - object_created
        - object_updated
        - object_deleted
      enabled: true
      action_type: webhook
      action_object_name: My Webhook
      description: "Alert on any device change"
      tags:
        - automation
    state: present

- name: Create event rule for circuit deletion (script by ID)
  leogallego.netbox.netbox_event_rule:
    netbox_url: http://netbox.local
    netbox_token: thisIsMyToken
    data:
      name: Script on circuit delete
      object_types:
        - circuits.circuit
      event_types:
        - object_deleted
      action_type: script
      action_object_id: 42
    state: present

- name: Create event rule with notification action
  leogallego.netbox.netbox_event_rule:
    netbox_url: http://netbox.local
    netbox_token: thisIsMyToken
    data:
      name: Notify on prefix creation
      object_types:
        - ipam.prefix
      event_types:
        - object_created
      action_type: notification
      action_object_name: Ops Team Notification
    state: present

- name: Delete an event rule
  leogallego.netbox.netbox_event_rule:
    netbox_url: http://netbox.local
    netbox_token: thisIsMyToken
    data:
      name: Device change alert
    state: absent
"""

RETURN = r"""
event_rule:
  description: Serialized object as created/existent/updated/deleted within NetBox
  returned: always
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
"""

from ansible_collections.netbox.netbox.plugins.module_utils.netbox_utils import (
    NetboxAnsibleModule,
    NETBOX_ARG_SPEC,
    API_APPS_ENDPOINTS,
    ENDPOINT_NAME_MAPPING,
)
from ansible_collections.netbox.netbox.plugins.module_utils.netbox_extras import (
    NetboxExtrasModule,
)
from copy import deepcopy


NB_EVENT_RULES = "event_rules"

API_APPS_ENDPOINTS["extras"]["event_rules"] = {}
ENDPOINT_NAME_MAPPING["event_rules"] = "event_rule"

ACTION_TYPE_TO_ENDPOINT = {
    "webhook": "webhooks",
    "script": "scripts",
    "notification": "notifications",
}

ACTION_TYPE_TO_CONTENT_TYPE = {
    "webhook": "extras.webhook",
    "script": "extras.script",
    "notification": "extras.notification",
}


def validate_action_object(module, data, state):
    """Validate action_object_name / action_object_id mutual exclusion and presence."""
    if state == "absent":
        return

    has_name = data.get("action_object_name") is not None
    has_id = data.get("action_object_id") is not None

    if has_name and has_id:
        module.fail_json(
            msg="action_object_name and action_object_id are mutually exclusive. Provide only one."
        )
        return

    if not has_name and not has_id:
        module.fail_json(
            msg="One of action_object_name or action_object_id is required when state=present."
        )


def resolve_action_object(module, nb, data):
    """Resolve action_object_name to action_object_type + action_object_id via pynetbox.

    When action_object_id is provided directly, just set action_object_type.
    When neither is present (state=absent), this is a no-op.
    """
    action_type = data.get("action_type")
    has_name = data.get("action_object_name") is not None
    has_id = data.get("action_object_id") is not None

    if not has_name and not has_id:
        return

    if has_name:
        endpoint_name = ACTION_TYPE_TO_ENDPOINT[action_type]
        nb_app = getattr(nb, "extras")
        nb_endpoint = getattr(nb_app, endpoint_name)

        try:
            action_object = nb_endpoint.get(name=data["action_object_name"])
        except Exception as e:
            module.fail_json(
                msg="Error querying NetBox for %s '%s': %s"
                % (action_type, data["action_object_name"], e)
            )
            return

        if not action_object:
            module.fail_json(
                msg="Could not find %s with name '%s'." % (action_type, data["action_object_name"])
            )
            return

        data["action_object_id"] = action_object.id
        del data["action_object_name"]

    data["action_object_type"] = ACTION_TYPE_TO_CONTENT_TYPE[action_type]


def main():
    """Main entry point for module execution."""
    argument_spec = deepcopy(NETBOX_ARG_SPEC)
    argument_spec.update(
        dict(
            data=dict(
                type="dict",
                required=True,
                options=dict(
                    name=dict(required=True, type="str"),
                    object_types=dict(required=False, type="list", elements="str"),
                    event_types=dict(required=False, type="list", elements="str"),
                    enabled=dict(required=False, type="bool"),
                    action_type=dict(
                        required=False,
                        type="str",
                        choices=["webhook", "script", "notification"],
                    ),
                    action_object_name=dict(required=False, type="str"),
                    action_object_id=dict(required=False, type="int"),
                    conditions=dict(required=False, type="dict"),
                    action_data=dict(required=False, type="dict"),
                    description=dict(required=False, type="str"),
                    comments=dict(required=False, type="str"),
                    tags=dict(required=False, type="list", elements="raw"),
                    custom_fields=dict(required=False, type="dict"),
                ),
            ),
        )
    )

    required_if = [
        ("state", "present", ["name", "object_types", "event_types", "action_type"], False),
        ("state", "absent", ["name"]),
    ]

    mutually_exclusive = [("action_object_name", "action_object_id")]

    module = NetboxAnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
    )

    data = module.params["data"]
    state = module.params["state"]

    validate_action_object(module, data, state)

    netbox_event_rule = NetboxExtrasModule(module, NB_EVENT_RULES)

    resolve_action_object(module, netbox_event_rule.nb, data)

    netbox_event_rule.run()


if __name__ == "__main__":  # pragma: no cover
    main()
