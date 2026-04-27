# Seed Role Design Spec

**Date:** 2026-04-27
**Collection:** leogallego.netbox
**Role FQCN:** leogallego.netbox.seed
**Status:** Draft

## Purpose

Create a `seed` role that populates a fresh NetBox instance with baseline data — sites, providers, circuits, devices, interfaces, prefixes, IPs, VLANs, and more. The role produces a realistic small-enterprise topology suitable for multiple demo scenarios (circuit failover, banner management, NTP configuration, VLAN assignment).

Ported from the summit demo at `/home/lgallego/Claude/summit-netbox-circuits-demo/ansible/pb_seed_netbox.yml`, expanded to cover a full lab seed rather than circuits-only.

## State Model

- **`netbox_seed_state: present`** — creates all objects in dependency order.
- **`netbox_seed_state: absent`** — deletes all objects in reverse dependency order. True teardown (objects are removed, not reset).

The demo-specific reset logic from `pb_reset_demo.yml` is NOT ported — it was too demo-specific (resetting circuit statuses to initial state without deleting objects).

## Credentials

Connection variables chain from the deploy role's exported facts, with fallback defaults:

```yaml
netbox_seed_url: "{{ netbox_deploy_url | default('http://localhost:8000') }}"
netbox_seed_token: "{{ netbox_deploy_api_token | default('') }}"
netbox_seed_validate_certs: "{{ netbox_deploy_validate_certs | default(false) }}"
```

This makes `deploy` -> `seed` chaining seamless while keeping the role independently usable.

## Data Model

### Anchor Variables

Names that appear in more than one data list are defined as anchor variables. This provides a single source of truth — rename once, propagates everywhere.

Naming convention: `netbox_seed_{object_type}_{qualifier}_{field}`
- `{qualifier}` distinguishes multiple instances of the same type (omitted for singletons)
- `{field}` matches the NetBox API field name (`name`, `model`, `cid`)

```yaml
# Sites
netbox_seed_site_a_name: NYC-DC1
netbox_seed_site_z_name: LON-DC2

# Provider (singleton — no qualifier)
netbox_seed_provider_name: Acme Telecom

# Circuit type (singleton)
netbox_seed_circuit_type_name: IPLC

# Manufacturer (singleton)
netbox_seed_manufacturer_name: Cisco

# Device types (qualifier: router vs switch; field: model)
netbox_seed_device_type_router_model: ISR4451
netbox_seed_device_type_switch_model: C9300

# Device roles (qualifier: router vs switch; field: name)
netbox_seed_device_role_router_name: router
netbox_seed_device_role_switch_name: switch

# Circuits (qualifier: pri vs sec; field: cid)
netbox_seed_circuit_pri_cid: IPLC-NYC-LON-PRI
netbox_seed_circuit_sec_cid: IPLC-NYC-LON-SEC

# Prefixes (qualifier: supernet / site_a / site_z)
netbox_seed_prefix_supernet: "10.0.0.0/8"
netbox_seed_prefix_site_a: "10.1.0.0/24"
netbox_seed_prefix_site_z: "10.2.0.0/24"
```

### Data Lists

Each object type gets its own flat list in `defaults/main.yml`. Lists reference anchor variables via Jinja2 for cross-type consistency.

The role ships with demo data pre-filled (original content, not the summit demo data) so it works out of the box. Users override with their own data in inventory.

| # | Data list | NetBox module (FQCN) | Anchor vars referenced |
|---|-----------|---------------------|----------------------|
| 1 | `netbox_seed_tags` | `netbox.netbox.netbox_tag` | — |
| 2 | `netbox_seed_sites` | `netbox.netbox.netbox_site` | `site_a_name`, `site_z_name` |
| 3 | `netbox_seed_providers` | `netbox.netbox.netbox_provider` | `provider_name` |
| 4 | `netbox_seed_circuit_types` | `netbox.netbox.netbox_circuit_type` | `circuit_type_name` |
| 5 | `netbox_seed_manufacturers` | `netbox.netbox.netbox_manufacturer` | `manufacturer_name` |
| 6 | `netbox_seed_device_types` | `netbox.netbox.netbox_device_type` | `device_type_router_model`, `device_type_switch_model`, `manufacturer_name` |
| 7 | `netbox_seed_device_roles` | `netbox.netbox.netbox_device_role` | `device_role_router_name`, `device_role_switch_name` |
| 8 | `netbox_seed_devices` | `netbox.netbox.netbox_device` | `site_*_name`, `device_type_*_model`, `device_role_*_name` |
| 9 | `netbox_seed_device_interfaces` | `netbox.netbox.netbox_device_interface` | device names |
| 10 | `netbox_seed_prefixes` | `netbox.netbox.netbox_prefix` | `prefix_supernet`, `prefix_site_a`, `prefix_site_z` |
| 11 | `netbox_seed_ip_addresses` | `netbox.netbox.netbox_ip_address` | `prefix_site_*` |
| 12 | `netbox_seed_vlan_groups` | `netbox.netbox.netbox_vlan_group` | `site_*_name` |
| 13 | `netbox_seed_vlans` | `netbox.netbox.netbox_vlan` | `site_*_name` |
| 14 | `netbox_seed_circuits` | `netbox.netbox.netbox_circuit` | `circuit_*_cid`, `provider_name`, `circuit_type_name` |
| 15 | `netbox_seed_circuit_terminations` | `netbox.netbox.netbox_circuit_termination` | `circuit_*_cid`, `site_*_name` |

## Role Structure

```
roles/seed/
  defaults/main.yml
  vars/main.yml
  meta/main.yml
  meta/argument_specs.yml
  tasks/
    main.yml
    tags.yml
    sites.yml
    providers.yml
    circuit_types.yml
    manufacturers.yml
    device_types.yml
    device_roles.yml
    devices.yml
    device_interfaces.yml
    prefixes.yml
    ip_addresses.yml
    vlan_groups.yml
    vlans.yml
    circuits.yml
    terminations.yml
    teardown.yml
  README.md
```

## Task File Behavior

### Orchestration

`tasks/main.yml` dispatches based on `netbox_seed_state`:
- `present` — includes each object-type file in dependency order (1-15 as listed above)
- `absent` — includes `teardown.yml`, which includes the same files in reverse order (15-1)

Each per-object task file uses `netbox_seed_state` as the module's `state:` parameter, so the same file handles both create and delete.

### Standard Pattern

Every task file follows this pattern:

```yaml
- name: Manage sites
  netbox.netbox.netbox_site:
    netbox_url: "{{ netbox_seed_url }}"
    netbox_token: "{{ netbox_seed_token }}"
    validate_certs: "{{ netbox_seed_validate_certs }}"
    data:
      name: "{{ item.name }}"
      status: "{{ item.status | default(omit) }}"
    state: "{{ netbox_seed_state }}"
  loop: "{{ netbox_seed_sites }}"
  loop_control:
    label: "{{ item.name }}"
  when: netbox_seed_sites | length > 0
```

### Special Cases

- **`terminations.yml`** — on `state: present`, performs an `nb_lookup` to build a site name-to-ID map (`__netbox_seed_site_ids`) before creating terminations. Uses `termination_type: dcim.site` and `termination_id` (NetBox 4.2+ format). On `state: absent`, terminations are deleted by circuit+side without needing the lookup.
- **`ip_addresses.yml`** — references interfaces by device+name. On teardown, IPs are deleted before interfaces.

### Empty List Skip

Each task file wraps its tasks in `when: netbox_seed_<type> | default([]) | length > 0` so users can set any list to `[]` (or leave it undefined) to skip that object type entirely.

## Default Data: Full Lab Topology

The role ships with this topology pre-filled in `defaults/main.yml`:

- **2 sites:** NYC-DC1, LON-DC2
- **1 provider:** Acme Telecom
- **1 circuit type:** IPLC
- **1 manufacturer:** Cisco
- **2 device types:** ISR4451 (router), C9300 (switch)
- **2 device roles:** router, switch
- **4 devices:** 1 router + 1 switch per site, all tagged `seed`
- **Device interfaces:** management + loopback on each device
- **Prefix hierarchy:** 10.0.0.0/8 supernet, 10.1.0.0/24 (NYC), 10.2.0.0/24 (LON)
- **Management IPs:** assigned to management interfaces
- **VLAN groups:** 1 per site
- **VLANs:** mgmt, users, servers per site
- **2 circuits:** IPLC-NYC-LON-PRI (Active), IPLC-NYC-LON-SEC (Offline)
- **4 circuit terminations:** A-side and Z-side for each circuit
- **1 tag:** `seed` (applied to all devices and circuits)

## Dependencies

**`galaxy.yml`** — add collection dependency:

```yaml
dependencies:
  netbox.netbox: ">=3.22.0"
```

## Input Validation

`meta/argument_specs.yml` validates:
- Connection vars: `netbox_seed_url` (str), `netbox_seed_token` (str), `netbox_seed_validate_certs` (bool)
- `netbox_seed_state` (str, choices: present/absent)
- All anchor vars: type str, with defaults
- All data lists: type `list`, elements type `dict`

Individual dict keys within data lists are NOT validated in argument_specs — the upstream `netbox.netbox` modules already validate their inputs and provide clear error messages. Mirroring their schemas would create a maintenance burden.

## Exported Facts

None. Unlike the deploy role (which exports `netbox_deploy_url` and `netbox_deploy_api_token`), the seed role is a data-seeding operation with no outputs needed by downstream roles.

## README.md

Example playbook sections:
1. Standalone usage (user provides URL + token)
2. Chained after deploy role (automatic credential passthrough)
3. Custom data override (user replaces default lists in inventory)
4. Teardown (`state: absent`)

## Conventions

Follows all collection conventions from CLAUDE.md:
- All variables prefixed `netbox_seed_`; internal variables prefixed `__netbox_seed_`
- All modules use FQCNs (`ansible.builtin.*`, `netbox.netbox.*`)
- Task file paths use `{{ role_path }}/tasks/...`
- Role inputs validated via `meta/argument_specs.yml`
- User-facing defaults in `defaults/main.yml`, internal constants in `vars/main.yml`
- CoP rules from global CLAUDE.md apply

## Decisions Not Made Here

- Exact interface names and types for devices (will be determined during implementation based on device type capabilities)
- VLAN IDs for the default VLANs (will pick sensible defaults during implementation)
- Whether the `seed` tag description should reference the collection name or be generic
