import assert from 'node:assert/strict';
import { spawnSync, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { REFLECTOR } from '../src/reflector.js';

const file = process.argv[2] ?? fileURLToPath(new URL(`../public/demos/${REFLECTOR.asset}.mp4`, import.meta.url));
const probe = JSON.parse(execFileSync(process.env.FFPROBE ?? 'ffprobe', [
  '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', file,
], { encoding: 'utf8' }));
const [video, audio] = probe.streams;
assert.equal(probe.streams.length, 2);
assert.equal(Number(probe.format.duration), REFLECTOR.duration);
assert.equal(Number(video.duration), REFLECTOR.duration);
assert.equal(Number(audio.duration), REFLECTOR.duration);
assert.equal(Number(video.nb_read_frames), REFLECTOR.duration * 24);
assert.equal(video.avg_frame_rate, '24/1');
assert.equal(video.r_frame_rate, '24/1');
assert.deepEqual([video.width, video.height], [REFLECTOR.width, REFLECTOR.height]);
assert.equal(video.codec_name, 'h264');
assert.equal(video.profile, 'High');
assert.equal(video.level, 40);
assert.equal(video.pix_fmt, 'yuv420p');
assert.equal(video.color_range, 'tv');
assert.equal(video.color_space, 'bt709');
assert.equal(video.color_primaries, 'bt709');
assert.equal(video.color_transfer, 'bt709');
assert.equal(audio.codec_name, 'aac');
assert.equal(audio.profile, 'LC');
assert.equal(audio.channels, 2);
assert.equal(audio.sample_rate, '48000');

const bytes = readFileSync(file);
const boxes = [];
for (let i = 0; i + 8 <= bytes.length;) {
  const size = bytes.readUInt32BE(i);
  assert.ok(size >= 8 && i + size <= bytes.length, `Unexpected MP4 box at ${i}`);
  boxes.push(bytes.toString('ascii', i + 4, i + 8));
  i += size;
}
assert.equal(boxes[0], 'ftyp');
assert.ok(boxes.indexOf('moov') > 0 && boxes.indexOf('moov') < boxes.indexOf('mdat'), 'moov must precede mdat for fast start');

// Fail on any decode error, not just malformed headers. Measure after AAC decoding.
const decode = spawnSync(process.env.FFMPEG ?? 'ffmpeg', [
  '-nostdin', '-hide_banner', '-xerror', '-err_detect', 'explode', '-threads', '2', '-i', file,
  '-map', '0:v:0', '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-',
], { encoding: 'utf8', maxBuffer: 2_000_000 });
if (decode.error) throw decode.error;
assert.equal(decode.status, 0, decode.stderr);
const summary = decode.stderr.split('Summary:').at(-1);
const integrated = Number(summary.match(/\bI:\s*(-?[\d.]+) LUFS/)?.[1]);
const range = Number(summary.match(/\bLRA:\s*([\d.]+) LU/)?.[1]);
const peak = Number(summary.match(/\bPeak:\s*(-?[\d.]+) dBFS/)?.[1]);
assert.ok(integrated >= -16 && integrated <= -13, `Integrated loudness ${integrated} LUFS`);
assert.ok(Number.isFinite(range) && peak <= -1, `True peak ${peak} dBTP`);
console.log(JSON.stringify({
  file, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex'),
  seconds: Number(probe.format.duration), frames: Number(video.nb_read_frames),
  resolution: [video.width, video.height], fps: video.avg_frame_rate,
  video: `${video.codec_name} ${video.profile} ${video.level / 10}, ${video.pix_fmt}, ${video.color_space} ${video.color_range}`,
  audio: `${audio.codec_name} ${audio.profile}, ${audio.sample_rate} Hz, ${audio.channels}ch`,
  integratedLUFS: integrated, loudnessRangeLU: range, truePeakDBTP: peak, fastStart: true, fullDecode: true,
}, null, 2));
