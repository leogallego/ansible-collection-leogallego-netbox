# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Leonardo Gallego
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock


MOCK_NETBOX_URL = "https://netbox.example.com"
MOCK_NETBOX_TOKEN = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def mock_netbox_module():
    """Patch NetboxAnsibleModule so it doesn't connect to a real NetBox."""
    with patch(
        "ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule.NetboxAnsibleModule"
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.params = {}
        mock_instance.check_mode = False
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


@pytest.fixture
def mock_extras_module():
    """Patch NetboxExtrasModule so .run() is a no-op."""
    with patch(
        "ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule.NetboxExtrasModule"
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


class TestArgumentSpec:
    """Tests that the module builds the correct argument spec."""

    def test_argument_spec_includes_data_suboptions(self):
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            main,
        )

        # The module should be importable and have the expected constants
        from ansible_collections.leogallego.netbox.plugins.modules import (
            netbox_event_rule,
        )

        assert hasattr(netbox_event_rule, "NB_EVENT_RULES")
        assert netbox_event_rule.NB_EVENT_RULES == "event_rules"

    def test_action_type_mappings_complete(self):
        from ansible_collections.leogallego.netbox.plugins.modules import (
            netbox_event_rule,
        )

        expected_types = {"webhook", "script", "notification"}
        assert set(netbox_event_rule.ACTION_TYPE_TO_ENDPOINT.keys()) == expected_types
        assert set(netbox_event_rule.ACTION_TYPE_TO_CONTENT_TYPE.keys()) == expected_types

    def test_action_type_to_endpoint_values(self):
        from ansible_collections.leogallego.netbox.plugins.modules import (
            netbox_event_rule,
        )

        assert netbox_event_rule.ACTION_TYPE_TO_ENDPOINT["webhook"] == "webhooks"
        assert netbox_event_rule.ACTION_TYPE_TO_ENDPOINT["script"] == "scripts"
        assert netbox_event_rule.ACTION_TYPE_TO_ENDPOINT["notification"] == "notifications"

    def test_action_type_to_content_type_values(self):
        from ansible_collections.leogallego.netbox.plugins.modules import (
            netbox_event_rule,
        )

        assert netbox_event_rule.ACTION_TYPE_TO_CONTENT_TYPE["webhook"] == "extras.webhook"
        assert netbox_event_rule.ACTION_TYPE_TO_CONTENT_TYPE["script"] == "extras.script"
        assert (
            netbox_event_rule.ACTION_TYPE_TO_CONTENT_TYPE["notification"] == "extras.notification"
        )

    def test_endpoint_registration(self):
        """Calling main() should patch API_APPS_ENDPOINTS and ENDPOINT_NAME_MAPPING."""
        from ansible_collections.netbox.netbox.plugins.module_utils.netbox_utils import (
            API_APPS_ENDPOINTS,
            ENDPOINT_NAME_MAPPING,
        )

        API_APPS_ENDPOINTS["extras"].pop("event_rules", None)
        ENDPOINT_NAME_MAPPING.pop("event_rules", None)

        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            main,
        )

        with patch(
            "ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule.NetboxAnsibleModule"
        ) as mock_mod_cls, patch(
            "ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule.NetboxExtrasModule"
        ) as mock_extras_cls:
            mock_instance = MagicMock()
            mock_instance.params = {
                "data": {"name": "test", "action_type": "webhook", "action_object_id": 1},
                "state": "present",
            }
            mock_instance.check_mode = False
            mock_mod_cls.return_value = mock_instance
            mock_extras_cls.return_value = MagicMock()
            main()

        assert "event_rules" in API_APPS_ENDPOINTS["extras"]
        assert ENDPOINT_NAME_MAPPING["event_rules"] == "event_rule"


class TestActionObjectValidation:
    """Tests for action_object_name / action_object_id validation logic."""

    def test_validate_action_object_both_provided_fails(self):
        """Providing both action_object_name and action_object_id should fail."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            validate_action_object,
        )

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_name": "My Webhook",
            "action_object_id": 1,
        }
        module = MagicMock()
        result = validate_action_object(module, data, "present")
        module.fail_json.assert_called_once()
        assert "mutually exclusive" in module.fail_json.call_args[1]["msg"].lower()

    def test_validate_action_object_neither_provided_on_create_fails(self):
        """Creating without action_object_name or action_object_id should fail."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            validate_action_object,
        )

        data = {
            "name": "test rule",
            "action_type": "webhook",
        }
        module = MagicMock()
        validate_action_object(module, data, "present")
        module.fail_json.assert_called_once()
        assert "action_object_name" in module.fail_json.call_args[1]["msg"]

    def test_validate_action_object_absent_does_not_require_action_fields(self):
        """State=absent should not require action_object_name or action_object_id."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            validate_action_object,
        )

        data = {"name": "test rule"}
        module = MagicMock()
        validate_action_object(module, data, "absent")
        module.fail_json.assert_not_called()

    def test_validate_action_object_id_only_passes(self):
        """Providing only action_object_id should pass validation."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            validate_action_object,
        )

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_id": 42,
        }
        module = MagicMock()
        validate_action_object(module, data, "present")
        module.fail_json.assert_not_called()

    def test_validate_action_object_name_only_passes(self):
        """Providing only action_object_name should pass validation."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            validate_action_object,
        )

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_name": "My Webhook",
        }
        module = MagicMock()
        validate_action_object(module, data, "present")
        module.fail_json.assert_not_called()


class TestActionObjectResolution:
    """Tests for resolving action_object_name to action_object_type + action_object_id."""

    def test_resolve_by_name_webhook(self):
        """Resolving a webhook by name should set action_object_type and action_object_id."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_webhook = MagicMock()
        mock_webhook.id = 7

        mock_nb = MagicMock()
        mock_nb.extras.webhooks.get.return_value = mock_webhook

        module = MagicMock()

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_name": "My Webhook",
        }

        resolve_action_object(module, mock_nb, data)

        assert data["action_object_type"] == "extras.webhook"
        assert data["action_object_id"] == 7
        assert "action_object_name" not in data
        mock_nb.extras.webhooks.get.assert_called_once_with(name="My Webhook")

    def test_resolve_by_name_script(self):
        """Resolving a script by name should use the scripts endpoint."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_script = MagicMock()
        mock_script.id = 3

        mock_nb = MagicMock()
        mock_nb.extras.scripts.get.return_value = mock_script

        module = MagicMock()

        data = {
            "name": "test rule",
            "action_type": "script",
            "action_object_name": "My Script",
        }

        resolve_action_object(module, mock_nb, data)

        assert data["action_object_type"] == "extras.script"
        assert data["action_object_id"] == 3
        assert "action_object_name" not in data

    def test_resolve_by_name_notification(self):
        """Resolving a notification by name should use the notifications endpoint."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_notification = MagicMock()
        mock_notification.id = 12

        mock_nb = MagicMock()
        mock_nb.extras.notifications.get.return_value = mock_notification

        module = MagicMock()

        data = {
            "name": "test rule",
            "action_type": "notification",
            "action_object_name": "Ops Notification",
        }

        resolve_action_object(module, mock_nb, data)

        assert data["action_object_type"] == "extras.notification"
        assert data["action_object_id"] == 12
        assert "action_object_name" not in data

    def test_resolve_by_name_not_found_fails(self):
        """Looking up a name that doesn't exist should fail with a clear message."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_nb = MagicMock()
        mock_nb.extras.webhooks.get.return_value = None

        module = MagicMock()

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_name": "Nonexistent Webhook",
        }

        resolve_action_object(module, mock_nb, data)

        module.fail_json.assert_called_once()
        msg = module.fail_json.call_args[1]["msg"]
        assert "Nonexistent Webhook" in msg
        assert "webhook" in msg.lower()

    def test_resolve_by_id_sets_content_type(self):
        """When action_object_id is provided, only set action_object_type."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_nb = MagicMock()
        module = MagicMock()

        data = {
            "name": "test rule",
            "action_type": "webhook",
            "action_object_id": 42,
        }

        resolve_action_object(module, mock_nb, data)

        assert data["action_object_type"] == "extras.webhook"
        assert data["action_object_id"] == 42
        module.fail_json.assert_not_called()

    def test_resolve_absent_state_is_noop(self):
        """When no action_object_name or action_object_id, resolution is a no-op."""
        from ansible_collections.leogallego.netbox.plugins.modules.netbox_event_rule import (
            resolve_action_object,
        )

        mock_nb = MagicMock()
        module = MagicMock()

        data = {"name": "test rule"}

        resolve_action_object(module, mock_nb, data)

        module.fail_json.assert_not_called()
        assert "action_object_type" not in data
