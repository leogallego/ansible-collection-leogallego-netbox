# leogallego.netbox Collection

Ansible collection for deploying and managing NetBox.

## Included Content

### Roles

| Role | Description |
|---|---|
| `leogallego.netbox.deploy` | Deploy a local NetBox instance via podman/docker compose |

## Requirements

- Ansible >= 2.15.0
- `podman` or `docker` installed on the target host

## Installation

```bash
ansible-galaxy collection install leogallego.netbox
```

Or add to `requirements.yml`:

```yaml
collections:
  - name: leogallego.netbox
```

Then install:

```bash
ansible-galaxy collection install -r requirements.yml
```

### Upgrade

```bash
ansible-galaxy collection install leogallego.netbox --upgrade
```

### Install a specific version

```bash
ansible-galaxy collection install leogallego.netbox:==1.0.0
```

## Usage

```yaml
- name: Deploy local NetBox
  hosts: localhost
  connection: local
  gather_facts: false
  roles:
    - role: leogallego.netbox.deploy
```

See the [deploy role README](roles/deploy/README.md) for full variable reference and examples.

## Release Notes

See the [changelog](CHANGELOG.rst).

## More Information

- [Ansible User Guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [NetBox Documentation](https://docs.netbox.dev/)
- [netbox-docker](https://github.com/netbox-community/netbox-docker)

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).

## Author

Leonardo Andres Gallego (<993814+leogallego@users.noreply.github.com>)

Repository: <https://github.com/leogallego/ansible-collection-leogallego-netbox>
