# Extinct Channel — project workspace

A separate workspace for evidence-led documentaries about extinct life. Current project: [Huayuan](projects/huayuan/PROJECT-STATUS.md). This is a folder in this repository, not a separate website, YouTube account, or autonomous agent. It does not activate automatically in another conversation: paste [ACTIVATION-PROMPT.md](ACTIVATION-PROMPT.md) into the new chat and give it access to this repository and the correct branch.

## Operating principles

- Follow the current repository `AGENTS.md` and V6.2 production playbook. Do not use deprecated pipelines or modify `README.md` files. Sync latest main into the active branch only when safe, respecting current session branch rules.
- Separate known evidence, inference, generic illustration and hypothesis. Cite primary science and verify asset rights/attribution for each project. Do not present speculative behavior or reconstructions as observed fact.
- Get user authorization before generating new audio or video. If a voice is approved, keep it at 1.000× speed and track its identity and provenance. Do not substitute an unverified voice. Existing mixed audio is not an isolated narration stem.
- Before presentation inspect multiple preflight passes and a decoded proof, and run applicable technical checks. Visual artistry, narration intelligibility and factual accuracy need human judgment; a technical pass is not a creative pass. Never claim universal retention, certification or scientific validation without evidence.
- Keep private audio, captions, rendered videos and large intermediates outside Git. Use the repository's ignored `exports/` or external Drive delivery. Drive links may require access and are not permanent backups. Keep model licenses and credits with every applicable release.

## Project layout

- `projects/huayuan/film.html`, `film.js` — experimental 60-second scene and timeline.
- `projects/huayuan/assets/` — six attributed 3D assets required by this source; see project credits and hashes.
- `projects/huayuan/notes/` — previous critiques, source provenance and decoded review proof.
- `projects/huayuan/PROJECT-STATUS.md` — actual current status and runnable commands.
- `ACTIVATION-PROMPT.md` — copyable prompt for a new chat; no secret key or external activation mechanism.
