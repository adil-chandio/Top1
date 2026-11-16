# Active Arena session execution

## External daemon ka alternative — implemented

`python -m studio.session step JOB_DIRECTORY` actual active-session tool handoff issue karta hai. Is route ko paid model API, exported Arena credentials ya external worker executable nahi chahiye. Yeh autonomous background worker nahi: equipped active agent request padhta, actual research/production tools chalata, output submit karta hai. Pending task routine user approval nahi.

`python -m studio.session submit JOB_DIRECTORY --result REAL_RESULT.json --executor ACTUAL_EXECUTOR_ID --capability ACTUAL_CAPABILITY` existing validation contract mein result submit karta hai. Response request SHA se bound hota hai; stale response, overwrite aur corrupted artifact reject hote hain. Waiting consumes no retry budget. Rejection creates next attempt without overwriting previous. Worker/reviewer phases durable hain; chat interruption ke baad same pending request recover hoti hai.

Independent review ke liye actual distinct equipped executor/context chahiye. CLI `--independent-context` attestation ko record karta hai; naam badalna real independence establish nahi karta. Active author ne apni research ko khud independent pass nahi diya. No synthetic reviewer auto-approval program installed.

Legacy unstarted blocked job: `python -m studio.session attach JOB_DIRECTORY`. Existing history retained, brief snapshot bound; already produced work cannot silently be rebriefed via attach.

## Connected-app Drive route — implemented

Session delivery stage `connector_delivery.prepare` par jata hai; standalone unattended OAuth credentials required nahi. Task actual MP4 decode + final reviews + binding folder + SHA/MD5/size validate karta hai and connector upload payload deta hai.

Operator sequence:
1. `python -m studio.connector_delivery prepare JOB_DIRECTORY`.
2. Connected google_drive search_files: exact task name and folder. Existing matching object recover karo, uncertain request par blind duplicate nahi.
3. Actual google_drive upload_file using task upload_input, only if absent.
4. Actual get_file fields id,name,size,md5Checksum,parents,trashed. Actual list_permissions all pages. Save real responses, never invent remote metadata.
5. `python -m studio.connector_delivery finalize JOB_DIRECTORY --metadata ACTUAL_GET_FILE.json --permissions ACTUAL_PERMISSIONS.json`.

Finalizer accepts connector file wrapper/snake_case fields and raw Drive camelCase. Wrong hash/size/name/folder, public/domain permissions, missing/incomplete permission evidence and connector failure reject hote hain. Rechecks local artifacts immediately before accepting remote evidence. State becomes awaiting_user_evaluation, never auto-accepted. Caller-supplied evidence consistency check cryptographic remote authenticity proof nahi.

## Actual execution in this pass

- Google Drive live get_file: existing Monarch Cam Production folder exists, not trashed, can_add_children true.
- list_permissions: one owner user; no public/domain entries; no next page.
- No diagnostic/test upload aur no new-video delivery claim.
- Existing pilot attached to session transport; real intelligence request emitted.
- Actual Ordinary Folk process/Creation text fetched; narrowly scoped craft reset artifact authored and submitted with actual source access limitations. Candidate passed normal artifact/research validation and is awaiting a distinct reviewer. No independent approval invented, no creative release gates cleared.
- Automated suite: 71 tests at this point. Includes durable two-phase session execution, actual-fixture subprocess legacy path, rejection/retry semantics and mocked connector integrity/privacy tests. Drive folder access additionally verified live, but final upload path is not claimed live-tested.

## Completion boundary

This closes the dependency on unattended credentials for in-chat work, not the need to execute work. Pending independent research review remains visible; film production still needs actual AV-capable craft/review execution. Do not substitute pending-task machinery or test counts for a finished accepted video.
