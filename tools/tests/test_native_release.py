import ast
import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[2]
workflow = yaml.safe_load((root / 'templates/coworld-release.yml').read_text())
steps = workflow['jobs']['release']['steps']
assert not any(step.get('name') == 'Put the Coworld secret' for step in steps)
for step in steps:
    script = step.get('run', '')
    if "<<'PY'" in script:
        ast.parse(script.split("<<'PY'", 1)[1].split('\nPY')[0])
script = next(step['run'] for step in steps if step.get('name') == 'Upload the policies')
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)
    (path / 'policies_input.json').write_text(json.dumps([
        {'name': 'native', 'run': ['python', '-m', 'player'], 'use_llm': True, 'llm_model': 'anthropic/claude-haiku-4.5'},
        {'name': 'scripted', 'run': '/bin/baseline'},
    ]))
    (path / 'uvx').write_text('''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['COMMANDS'],'a') as f:f.write(json.dumps(sys.argv[1:])+'\\n')
if 'upload-policy' in sys.argv:print('Upload complete: '+sys.argv[sys.argv.index('--name')+1]+':v1')
''')
    (path / 'uvx').chmod(0o755)
    env = dict(os.environ, PATH=f'{tmp}:{os.environ["PATH"]}', COMMANDS=str(path / 'commands'), RR=tmp, IMAGE='fixture', COWORLD_PKG='coworld[auth]==0.1.56')
    subprocess.run(['bash', '-c', script], cwd=root, env=env, check=True)
    commands = [json.loads(line) for line in (path / 'commands').read_text().splitlines()]
    uploads = [command for command in commands if 'upload-policy' in command]
    assert len(uploads) == 2
    assert uploads[0][uploads[0].index('--llm-model')+1] == 'anthropic/claude-haiku-4.5'
    assert '--use-llm' in uploads[0]
    assert '--use-llm' not in uploads[1]
    assert all('--use-bedrock' not in command for command in commands)
    assert len(json.loads((path / 'policies.json').read_text())) == 2
print('Native and scripted release policy commands passed')
