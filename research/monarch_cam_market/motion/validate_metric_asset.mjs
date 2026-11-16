// Official Khronos glTF Validator; technical schema check, not creative approval.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import validator from './out/tools/node_modules/gltf-validator/index.js';
const base=path.dirname(fileURLToPath(import.meta.url));
const data=fs.readFileSync(path.join(base,'out/orca/orca_metric_rig.glb'));
const report=await validator.validateBytes(new Uint8Array(data),{uri:'orca_metric_rig.glb',maxIssues:500});
const result={asset_sha256:crypto.createHash('sha256').update(data).digest('hex'),validator:'Khronos glTF Validator 2.0.0-dev.3.10',...report};
fs.writeFileSync(path.join(base,'out/orca/metric_gltf_validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos,sha256:result.asset_sha256},null,2));
if(report.issues.numErrors)process.exitCode=1;
