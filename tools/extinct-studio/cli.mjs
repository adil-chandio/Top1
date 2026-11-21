#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import {
  checkTransition,
  scoreIdeas,
  selfCheck,
  validateAnalyticsDocument,
  validateProjectDirectory,
} from './lib.mjs';

function usage() {
  console.error(`Extinct Studio OS\n\nCommands:\n  self-check\n  score <ideas.json>\n  validate <project-directory>\n  check-transition <project-directory> <next-state>\n\nAll commands are read-only. This CLI never uploads, shares, schedules, publishes, or edits a project status.`);
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    throw new Error(`${file}: ${error.message}`);
  }
}

function print(value) {
  console.log(JSON.stringify(value, null, 2));
}

const [command, ...args] = process.argv.slice(2);

try {
  if (command === 'self-check') {
    const result = selfCheck();
    print(result);
    process.exitCode = result.ok ? 0 : 1;
  } else if (command === 'score') {
    if (!args[0]) throw new Error('score requires an ideas JSON file');
    const file = path.resolve(args[0]);
    const result = scoreIdeas(readJson(file));
    print({
      count: result.length,
      ideas: result,
      note: 'Scores are editorial readiness gates, not viral probabilities or view forecasts.',
    });
  } else if (command === 'analytics-check') {
    if (!args[0]) throw new Error('analytics-check requires a redacted Studio JSON file');
    const result = validateAnalyticsDocument(readJson(path.resolve(args[0])));
    print(result);
    process.exitCode = result.ok ? 0 : 1;
  } else if (command === 'validate') {
    if (!args[0]) throw new Error('validate requires a project directory');
    const result = validateProjectDirectory(args[0]);
    print(result);
    process.exitCode = result.ok ? 0 : 1;
  } else if (command === 'check-transition') {
    if (!args[0] || !args[1]) throw new Error('check-transition requires a project directory and target state');
    const result = checkTransition(args[0], args[1]);
    print(result);
    process.exitCode = result.ok ? 0 : 1;
  } else {
    usage();
    process.exitCode = 2;
  }
} catch (error) {
  console.error(`Extinct Studio OS error: ${error.message}`);
  process.exitCode = 2;
}
