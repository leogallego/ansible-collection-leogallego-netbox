# leogallego.netbox.deploy

Deploy a local NetBox instance using podman compose or docker compose. Creates a superuser account, provisions an API token, and exports connection facts for downstream automation.

## Requirements

- `podman` (preferred) or `docker` installed and on the PATH
- `git` installed (to clone the netbox-docker repository)
- Internet access to pull container images on first run

## Role Variables

### User-facing defaults (`defaults/main.yml`)

| Variable | Default | Description |
|---|---|---|
| `netbox_deploy_provider` | *(auto-detect)* | Container engine: `podman` or `docker`. Auto-detected if not set. |
| `netbox_deploy_state` | `present` | `present` to deploy, `absent` to tear down. |
| `netbox_deploy_netbox_docker_repo` | `https://github.com/netbox-community/netbox-docker.git` | Git URL for netbox-docker. |
| `netbox_deploy_netbox_docker_version` | `HEAD` | Git ref to clone. |
| `netbox_deploy_netbox_docker_dir` | `~/netbox-docker` | Directory to clone into. |
| `netbox_deploy_port` | `8000` | Host port to expose NetBox on. |
| `netbox_deploy_admin_user` | `admin` | Superuser username. |
| `netbox_deploy_admin_password` | `admin` | Superuser password. |
| `netbox_deploy_admin_email` | `admin@example.com` | Superuser email. |
| `netbox_deploy_token` | *(empty)* | API token value. Leave empty to auto-generate. |
| `netbox_deploy_cleanup_dir` | `false` | Remove cloned netbox-docker directory on teardown. |
| `netbox_deploy_validate_certs` | `false` | Validate TLS certs on API calls. |

### Exported facts

After successful deployment, the role sets:

- `netbox_deploy_url` — base URL (e.g., `http://localhost:8000`)
- `netbox_deploy_api_token` — provisioned API token

These are available to subsequent plays/roles without passing credentials manually.

## Dependencies

None.

## Example Playbooks

### Deploy NetBox

```yaml
- name: Deploy local NetBox
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: leogallego.netbox.deploy
```

### Deploy with custom settings

```yaml
- name: Deploy local NetBox with custom port
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: leogallego.netbox.deploy
      netbox_deploy_port: 8080
      netbox_deploy_provider: docker
```

### Use exported facts in a follow-up play

```yaml
- name: Deploy NetBox
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: leogallego.netbox.deploy

- name: Seed data into NetBox
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Create a site
      netbox.netbox.netbox_site:
        netbox_url: "{{ netbox_deploy_url }}"
        netbox_token: "{{ netbox_deploy_api_token }}"
        data:
          name: London
          slug: london
```

### Tear down

```yaml
- name: Remove local NetBox
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: leogallego.netbox.deploy
      netbox_deploy_state: absent
      netbox_deploy_cleanup_dir: true
```

## Idempotency

This role is idempotent. Running it twice with the same parameters produces no changes on the second run:

- Git clone skips if the directory already exists
- Compose up recreates only changed containers
- Superuser creation detects "already taken" and reports ok
- Token provisioning reuses existing tokens

## Rollback

Set `netbox_deploy_state: absent` to tear down the deployment. Add `netbox_deploy_cleanup_dir: true` to also remove the cloned repository.

## License

GPL-3.0-or-later

## Author

Leonardo Andres Gallego (<993814+leogallego@users.noreply.github.com>)

Repository: <https://github.com/leogallego/ansible-collection-leogallego-netbox>
