import json
import sys
from collections import Counter, defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else 'flows-grade10.json'
with open(path) as fh:
    flow = json.load(fh)

ids = [node['id'] for node in flow]
counts = Counter(ids)
errors = []
for node_id, count in counts.items():
    if count > 1:
        errors.append(f'duplicate node id: {node_id}')

tabs = {node['id'] for node in flow if node['type'] == 'tab'}
subflows = {node['id'] for node in flow if node['type'] == 'subflow'}
config_nodes = {node['id'] for node in flow if node.get('z') is None and node['type'] not in {'tab', 'subflow', 'group'}}

node_lookup = {node['id']: node for node in flow}

for node in flow:
    ntype = node['type']
    if ntype in {'tab', 'subflow', 'group'}:
        continue
    z = node.get('z')
    if z is not None and z not in tabs and z not in subflows:
        errors.append(f'node {node["id"]} ({ntype}) references missing tab/subflow {z}')
    # Validate wires
    for port, targets in enumerate(node.get('wires', [])):
        for target in targets:
            if target not in node_lookup:
                errors.append(f'node {node["id"]} ({ntype}) has wire to missing node {target}')

    # Validate config node references (properties ending with _config etc)
    for key, value in node.items():
        if key in {'id', 'type', 'name', 'z', 'x', 'y', 'wires', 'info', 'l'}:
            continue
        if isinstance(value, str) and value in config_nodes:
            continue
        if isinstance(value, str) and value in node_lookup and node_lookup[value]['type'] in {'tab', 'subflow'}:
            continue
        if isinstance(value, str) and value not in {'', 'global', 'flow'}:
            if value in node_lookup and node_lookup[value].get('z') is None and node_lookup[value]['type'] not in {'tab', 'subflow', 'group'}:
                continue

# Style checks: ensure function nodes avoid console/node logging
for node in flow:
    if node['type'] == 'function':
        func = node.get('func', '')
        if 'console.' in func or 'node.warn' in func or 'node.error' in func or 'node.log' in func:
            errors.append(f'function node {node["id"]} uses logging API')

if errors:
    print('FAIL')
    for err in errors:
        print(' -', err)
    sys.exit(1)
print('PASS')
