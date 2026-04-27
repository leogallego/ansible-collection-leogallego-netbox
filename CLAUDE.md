# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Collection

- **FQCN:** leogallego.netbox
- **Version:** 1.0.0 (see `galaxy.yml`)
- **License:** GPL-3.0-or-later
- **Requires:** Ansible >= 2.15.0

## Commands

All commands run from the repo root unless noted.

```bash
# Build collection artifact
ansible-galaxy collection build .

# Lint
ansible-lint

# Run sanity tests (must be inside collection namespace path)
ansible-test sanity --docker

# Run pre-commit hooks
pre-commit run --all-files

# Python formatting/linting (line length 100)
black .
isort --filter-files .
flake8

# Run unit tests
pytest tests/unit/

# Run molecule integration tests
pytest tests/integration/ -k "test_integration"

# Generate changelog (requires fragments in changelogs/fragments/)
antsibull-changelog release
```

## CI Pipeline

GitHub Actions (`.github/workflows/tests.yml`) runs on PRs to `main`: changelog fragment check, ansible-lint, ansible-test sanity, and collection build+import. PRs require a changelog fragment file in `changelogs/fragments/`. Releases to Galaxy are triggered by publishing a GitHub release (`.github/workflows/release.yml`).

## Architecture

The collection currently has one role (`deploy`) and empty plugin stubs. The deploy role orchestrates a full NetBox stack lifecycle:

```
roles/deploy/tasks/main.yml
  ├── state=absent → teardown/compose.yml (compose down, optional dir cleanup)
  └── state=present →
        preflight.yml      (detect podman or docker)
        deploy/compose.yml (git clone netbox-docker, template port override, compose up)
        healthcheck.yml    (poll /login/ until ready, 30 retries × 10s)
        superuser.yml      (compose exec to create admin via Django management command)
        token.yml          (POST /api/users/tokens/provision/, verify via /api/status/)
```

The role exports two facts for downstream use: `netbox_deploy_url` and `netbox_deploy_api_token`.

## Conventions

- All role variables prefixed `netbox_deploy_`; internal variables prefixed `__netbox_deploy_`
- All modules use FQCNs (`ansible.builtin.*`)
- Task file paths use `{{ role_path }}/tasks/...` (never relative paths)
- ansible-lint skips `var-naming[no-role-prefix]` because variables use the collection-scoped prefix `netbox_deploy_` rather than the bare role name `deploy_`
- Role inputs are validated via `meta/argument_specs.yml`; user-facing defaults live in `defaults/main.yml`, internal constants in `vars/main.yml`
- Provider auto-detection prefers podman over docker; expose `netbox_deploy_provider` to override
- CoP rules from the global CLAUDE.md apply (Red Hat CoP automation good practices)

## Testing

- **Unit tests:** `tests/unit/` — run with pytest
- **Integration tests:** `tests/integration/` — uses pytest-ansible to drive Molecule scenarios defined in `extensions/molecule/`
- **Molecule scenarios:** `extensions/molecule/integration_hello_world/` — shared converge playbook at `extensions/molecule/utils/playbooks/converge.yml`
- Test Python dependencies: pytest-ansible, pytest-xdist, molecule (see `test-requirements.txt`)

## Adding a New Role

1. Create `roles/<name>/` with standard Ansible role structure
2. Prefix all variables with `netbox_<name>_` (internal: `__netbox_<name>_`)
3. Add `meta/argument_specs.yml` for input validation
4. Add a Molecule scenario in `extensions/molecule/`
5. Update this file's Roles section
