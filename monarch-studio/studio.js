import './studio.css';
import { AIR_CRUSH } from '../src/air-crush.js';
import { mountScreening } from './screening.js';
import productionNotes from './PRODUCTION.md?url';

const notesLink = document.querySelector('#production-file');
notesLink.href = productionNotes;
notesLink.download = 'monarch-studio-production.md';

mountScreening(AIR_CRUSH);
