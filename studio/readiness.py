"""Configuration readiness, deliberately not a claim of creative/AV capability."""
import os,shlex,shutil
from pathlib import Path
from studio.media import ffmpeg_command

def inspect():
    from studio.pipeline import CONFIG
    checks={};commands={}
    for role,key in [('worker',CONFIG['worker_command_env']),('reviewer',CONFIG['reviewer_command_env'])]:
        try:
            argv=shlex.split(os.getenv(key,''));commands[role]=argv
            checks[role+'_executable']=bool(argv and shutil.which(argv[0]))
        except ValueError:commands[role]=[];checks[role+'_executable']=False
    checks['distinct_review_command']=bool(commands['worker'] and commands['reviewer'] and commands['worker']!=commands['reviewer'])
    credential=os.getenv('STUDIO_DRIVE_CREDENTIALS_FILE')
    checks['drive_credentials_file']=bool(credential and Path(credential).is_file())
    checks['drive_folder']=bool(os.getenv('STUDIO_DRIVE_FOLDER_ID'))
    checks['ffmpeg']=bool(ffmpeg_command())
    return {'configuration_ready':all(checks.values()),'checks':checks,'missing':[k for k,v in checks.items() if not v],'note':'Configuration only. Requires real worker execution, actual audiovisual review and a successful pilot to establish operations.'}
