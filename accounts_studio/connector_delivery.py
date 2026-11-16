"""Arena Drive connector handoff. OAuth stays inside the connected app.

Prepare -> actual upload_file -> actual get_file/list_permissions -> finalize.
Never treats an upload request, a local receipt or a link as proof of delivery.

Isolated from the three-channel system: separate job marker, separate folder
id in `accounts_studio/creative_brief.json`, and `ACCOUNTS_*` configuration.
"""
import fcntl
import hashlib
import json
import subprocess
from pathlib import Path

from accounts_studio.guards import delivery_preflight
from accounts_studio.pipeline import save

MAX_CONNECTOR_BYTES = 100 * 1024 * 1024


def prepare(job):
    """Write the exact upload task an equipped agent must perform."""
    from accounts_studio.media import ffmpeg_command
    from accounts_studio.pipeline import CONFIG
    job = Path(job).resolve()
    with (job / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
        if state['account'] != CONFIG['active_account']:
            raise ValueError('inactive account')
        if CONFIG['stages'][state['stage']] != 'delivery':
            raise ValueError('job not ready for delivery')
        if state['status'] not in ('queued', 'blocked', 'awaiting_connector'):
            raise ValueError('job not ready for delivery')
        delivery_preflight(job, state)
        from accounts_studio.lifecycle import validate_upstream
        validate_upstream(job, state)
        brief_path = job / 'creative_brief.json'
        if not brief_path.is_file():
            raise ValueError('creative_brief.json with drive_folder_id required')
        brief = json.loads(brief_path.read_text(encoding='utf-8'))
        folder = brief.get('drive_folder_id') or (brief.get('scope') or {}).get('drive_folder_id')
        if not folder:
            raise ValueError('creative_brief.json has no drive_folder_id')
        item = next(a for a in state['outputs']['production']['artifacts']
                    if a['path'].lower().endswith('.mp4'))
        video = job / item['path']
        data = video.read_bytes()
        if len(data) > MAX_CONNECTOR_BYTES:
            raise ValueError('connector size limit; do not upload')
        exe = ffmpeg_command()
        if not exe:
            raise ValueError('FFmpeg required to decode the file before delivery')
        subprocess.run([exe, '-v', 'error', '-xerror', '-i', str(video),
                        '-f', 'null', '-'], check=True, timeout=600,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        name = state['id'] + '-r' + str(len(state.get('revisions', []))) + '.mp4'
        task = {
            'name': name,
            'file_path': str(video),
            'folder': folder,
            'bytes': len(data),
            'sha256': item['sha256'],
            'md5': hashlib.md5(data).hexdigest(),
            'instructions': (
                'Search the exact name in the folder before uploading. Recover a '
                'matching existing file; do not duplicate on an uncertain upload. '
                'Then get_file metadata and every list_permissions page. Never '
                'create a public permission.'),
            'upload_input': {
                'name': name,
                'file_path': str(video),
                'parents': [folder],
                'content_mime_type': 'video/mp4',
                'target_mime_type': None,
                'description': state['outputs']['production'].get('attribution', ''),
                'starred': False,
                'fields': 'id,name,size,md5Checksum,parents,webViewLink',
                'supports_all_drives': True,
            },
        }
        save(job / 'connector_delivery_task.json', task)
        state['status'] = 'awaiting_connector'
        save(job / 'state.json', state)
        return task


def finalize(job, metadata, permissions):
    """Operator supplies unmodified actual connector get_file and permission results.

    Local checks prove consistency, not the authenticity of an arbitrary
    caller's dict. That is why the receipt records the transport by name.
    """
    job = Path(job).resolve()
    with (job / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if metadata.get('success') is False or permissions.get('success') is False:
            raise ValueError('connector returned failure')
        metadata = metadata.get('file', metadata)
        metadata = {**metadata,
                    'md5Checksum': metadata.get('md5Checksum',
                                                metadata.get('md5_checksum'))}
        state = json.loads((job / 'state.json').read_text(encoding='utf-8'))
        if state['status'] != 'awaiting_connector':
            raise ValueError('no pending connector upload')
        delivery_preflight(job, state)
        from accounts_studio.lifecycle import validate_upstream
        validate_upstream(job, state)
        task = json.loads((job / 'connector_delivery_task.json').read_text(encoding='utf-8'))
        brief = json.loads((job / 'creative_brief.json').read_text(encoding='utf-8'))
        video = next(a for a in state['outputs']['production']['artifacts']
                     if a['path'].lower().endswith('.mp4'))
        if task['sha256'] != video['sha256']:
            raise ValueError('stale delivery task')
        folder = brief.get('drive_folder_id') or (brief.get('scope') or {}).get('drive_folder_id')
        if task['folder'] != folder:
            raise ValueError('stale delivery task')
        if metadata.get('name') != task['name']:
            raise ValueError('wrong destination/name')
        if metadata.get('parents') != [task['folder']]:
            raise ValueError('wrong destination/name')
        if metadata.get('md5Checksum') != task['md5']:
            raise ValueError('remote integrity mismatch')
        if int(metadata.get('size', -1)) != task['bytes']:
            raise ValueError('remote integrity mismatch')
        if not metadata.get('id') or metadata.get('trashed'):
            raise ValueError('invalid remote file')
        if 'permissions' not in permissions:
            raise ValueError('complete permission evidence required')
        if permissions.get('nextPageToken') or permissions.get('next_page_token'):
            raise ValueError('complete permission evidence required')
        if any(p.get('type') in ('anyone', 'domain')
               for p in permissions['permissions']):
            raise ValueError('private delivery required')
        receipt = {'file_id': metadata['id'],
                   'link': 'https://drive.google.com/file/d/' + metadata['id'] + '/view',
                   'sha256': video['sha256'],
                   'bytes': task['bytes'],
                   'public_sharing_enabled': False,
                   'transport': 'arena_google_drive_connector'}
        save(job / 'connector_delivery_evidence.json',
             {'metadata': metadata, 'permissions': permissions})
        save(job / 'delivery.json', receipt)
        state['delivery'] = receipt
        state['status'] = 'awaiting_user_evaluation'
        state['blocker'] = None
        save(job / 'state.json', state)
        return receipt


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('prepare')
    a.add_argument('job')
    a = sub.add_parser('finalize')
    a.add_argument('job')
    a.add_argument('--metadata', required=True)
    a.add_argument('--permissions', required=True)
    args = parser.parse_args()
    if args.cmd == 'prepare':
        result = prepare(args.job)
    else:
        result = finalize(args.job,
                          json.loads(Path(args.metadata).read_text(encoding='utf-8')),
                          json.loads(Path(args.permissions).read_text(encoding='utf-8')))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
