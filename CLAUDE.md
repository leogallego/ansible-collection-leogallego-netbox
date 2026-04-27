# CLAUDE.md

## Collection

- **Namespace:** leogallego
- **Name:** netbox
- **FQCN:** leogallego.netbox

## Roles

- **deploy** — Deploy a local NetBox instance via podman/docker compose, create superuser, provision API token, export connection facts.

## Commands

```bash
# Build collection artifact
ansible-galaxy collection build collections/ansible_collections/leogallego/netbox

# Run sanity tests
cd collections/ansible_collections/leogallego/netbox && ansible-test sanity

# Release changelog
cd collections/ansible_collections/leogallego/netbox && antsibull-changelog release
```

## Conventions

- All role variables prefixed `netbox_deploy_`
- Internal variables prefixed `__netbox_deploy_`
- All modules use FQCNs (`ansible.builtin.*`)
- CoP rules from the parent project's CLAUDE.md apply here
