#!/usr/bin/python

# Copyright: (c) 2019, Christian Sandrini <mail@chrissandrini.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: serviceguard_node

short_description: HP ServiceGuard node package

version_added: "2.7"

description:
  - This package controls nodes of a HP ServiceGuard cluster. It allows to start / stop a cluster node

options:
    name:
        description:
            - Name of the node
        required: true
    state:
        description:
          - Desired state of the node
        choices: ["started","stopped"]
        required: true
    path:
        description:
            - Path of the cm* binaries
        required: false
        default: /usr/local/cmcluster/bin
    force:
        description:
            - Forces the shutdown of the node, even if packages are running on it
        required: false
        type: bool

author:
    - Christian Sandrini (@sandrich)
    - Sergio Perez Fernandez (@sergioperez)
'''

EXAMPLES = '''
# Starts the node
- name: Starts node01
  serviceguard_node:
    name: node01
    state: started

# Stops the node
- name: Stops node01
  serviceguard_node:
    name: node01
    state: stopped

# Stops the node forcefully
- name: Stops node01
  serviceguard_node:
    name: node01
    state: stopped
    force: true
'''

RETURN = '''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.serviceguard import parse_cluster_state


def start_node(module):
    state = parse_cluster_state(module)

    node_name = module.params['name']
    current_state = state['nodes'][node_name]['state']
    cmd_params = [module.params['path'] + '/cmrunnode', node_name]

    # Start if system is halted and started is requested
    if current_state == 'unknown':
        (rc, out, err) = module.run_command(cmd_params)

        if rc != 0:
            module.fail_json(msg="Node could not be started: %s%s" % (out, err))

    return node_name


def stop_node(module):
    state = parse_cluster_state(module)

    node = module.params['name']
    node_state = state['nodes'][node]['state']
    cmd_params = [module.params['path'] + '/cmhaltnode', node]

    if module.params['force']:
        cmd_params.append('-f')

    if node_state == 'running':
        (rc, out, err) = module.run_command(cmd_params)

        if rc != 0:
            module.fail_json(msg="Node %s could not be stopped: %s%s" % (node, out, err))

    return True


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=True, choices=['started', 'stopped']),
        path=dict(type='str', required=False, default='/usr/local/cmcluster/bin'),
        force=(dict(type='bool', required=False, default=False))
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    state = parse_cluster_state(module)

    if module.params['state'] == 'started':
        start_node(module)
    elif module.params['state'] == 'stopped':
        stop_node(module)

    result = parse_cluster_state(module)

    if state == result:
        result['changed'] = False
    else:
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
