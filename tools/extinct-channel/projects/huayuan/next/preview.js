// Preview absolute frames 390..479, the first radiodont close shot.
await import('./scene.js');
const stream = window.streamFramesWS;
const still = window.renderFramePNG;
window.streamFramesWS = (start, end) => stream(start + 390, end + 390);
window.renderFramePNG = (frame) => still(frame + 390);
window.renderCoverPNG = () => still(425);
