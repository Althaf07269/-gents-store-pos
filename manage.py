#!/usr/bin/env python
import os
import sys


def _use_project_venv():
    """Re-launch with venv Python when system Python lacks project deps."""
    if sys.prefix != sys.base_prefix:
        return
    root = os.path.dirname(os.path.abspath(__file__))
    if os.name == 'nt':
        venv_python = os.path.join(root, 'venv', 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(root, 'venv', 'bin', 'python')
    if os.path.isfile(venv_python):
        os.execv(venv_python, [venv_python, *sys.argv])


_use_project_venv()

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gents_pos.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
