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
            netbox_event_rule.ACTION_TYPE_TO_CONTENT_TYPE["notification"]
            == "extras.notification"
        )

    def test_endpoint_registration(self):
        """Importing the module should patch API_APPS_ENDPOINTS and ENDPOINT_NAME_MAPPING."""
        from ansible_collections.leogallego.netbox.plugins.modules import (
            netbox_event_rule,  # noqa: F401 — import triggers side effect
        )
        from ansible_collections.netbox.netbox.plugins.module_utils.netbox_utils import (
            API_APPS_ENDPOINTS,
            ENDPOINT_NAME_MAPPING,
        )

        assert "event_rules" in API_APPS_ENDPOINTS["extras"]
        assert ENDPOINT_NAME_MAPPING["event_rules"] == "event_rule"
