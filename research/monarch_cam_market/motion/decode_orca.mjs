// npm dependencies installed under ignored out/tools; no downloaded code is executed as a shell script.
import { NodeIO } from './out/tools/node_modules/@gltf-transform/core/dist/index.js';
import { ALL_EXTENSIONS } from './out/tools/node_modules/@gltf-transform/extensions/dist/index.js';
import { MeshoptDecoder } from './out/tools/node_modules/meshoptimizer/index.js';
await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const doc=await io.read(new URL('./out/orca/orca.glb',import.meta.url).pathname);
for(const ext of doc.getRoot().listExtensionsUsed()) if(ext.extensionName==='EXT_meshopt_compression') ext.dispose();
await io.write(new URL('./out/orca/orca_decoded.glb',import.meta.url).pathname,doc);
console.log('Decoded orca written, transforms/materials retained.');
