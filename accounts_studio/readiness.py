"""Configuration readiness, deliberately not a claim of creative/AV capability.

Readiness answers one narrow question: are the *configuration inputs* present?
It is not a claim that the system can make a good film, and every caller is
expected to say so.
"""
import os
import shlex
import shutil

from accounts_studio.media import ffmpeg_command

NOTE = ('Configuration only. Requires real worker execution, actual audiovisual '
        'review and a successful pilot to establish operations.')


def inspect():
    from accounts_studio.pipeline import CONFIG
    checks = {}
    commands = {}
    for role, key in [('worker', CONFIG['worker_command_env']),
                      ('reviewer', CONFIG['reviewer_command_env'])]:
        raw = os.getenv(key, '')
        try:
            argv = shlex.split(raw)
        except ValueError:
            argv = []
        commands[role] = argv
        if argv and len(argv) == 1:
            # A session role is not a PATH executable; it is handed to an agent.
            from accounts_studio.session import COMMANDS
            checks[role + '_executable'] = argv[0] in COMMANDS
        else:
            checks[role + '_executable'] = bool(argv and shutil.which(argv[0]))
    checks['distinct_review_command'] = bool(
        commands['worker'] and commands['reviewer']
        and commands['worker'] != commands['reviewer'])
    credential = os.getenv('ACCOUNTS_DRIVE_CREDENTIALS_FILE')
    from pathlib import Path
    checks['drive_credentials_file'] = bool(credential and Path(credential).is_file())
    checks['drive_folder'] = bool(os.getenv('ACCOUNTS_DRIVE_FOLDER_ID'))
    checks['ffmpeg'] = bool(ffmpeg_command())
    return {
        'configuration_ready': all(checks.values()),
        'checks': checks,
        'missing': [k for k, v in checks.items() if not v],
        'note': NOTE,
    }
