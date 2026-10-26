# Synora samples for every source

All people, organizations, emails and project statements in this pack are fictional. The files intentionally disagree about the **same first internal pilot**, so a scope/version difference cannot silently explain the dates. They contain unresolved proposals; none is an automatic source of truth.

## Files and planted issues

| File | Content and expected issues |
|---|---|
| `01-product-brief.md` | Synora AI project-intelligence workspace; December 7, 2026; Google Meet, selected WhatsApp and manual uploads; Atlas read-only; canvas edits NOT evidence; review-first memory; human routing; no named final approver. |
| `02-architecture-notes.md` | January 18, 2027 for the same pilot; requirement changes pending until member review; ambiguous evidence in Unknown Context; no named policy/release approvers. |
| `03-meeting-notes.md` | Both dates disputed; saved Atlas edits SHOULD become evidence versus read-only; memory approval left open; auto-routing disputed; no owner named; no decision. |
| `04-release-checklist.md` | January 18, 2027; every item unchecked; all policy checks pending; no owners, completion evidence or sign-off. |
| `05-integration-scope.md` | Direct Atlas-edit ingestion and auto-routing explicitly OUT; review gate and Unknown Context; scope-change approver missing. |
| `06-project-lead-email.md` | Fictional lead proposes December 7, 2026, automatic requirement-memory writes and auto-routing; approval and ownership still unresolved. |
| `07-synora-pilot-discussion.mp3` | Three synthetic speakers argue all five issues, then end without a decision and request lead confirmation. Use for an audio transcription step. |
| `07-synora-pilot-discussion.wav` | The same complete discussion as uncompressed mono PCM. Use where WAV input is preferred. |
| `07-synora-pilot-discussion-transcript.txt` | Exact text supplied to speech synthesis, speaker names and approximate timestamps; planted-conflict answer key at the end is NOT spoken. |
| `verification.json` | File checks, hashes, voice settings, turn boundaries, synthesis input and conflict coverage. Validation material; do not upload as source evidence. |
| `README.md` | This file and the manual test steps. Validation material; do not upload as evidence. |

Meera uses the local female `slt` voice; Aarav uses male `rms`; Rohan uses male `awb` at a slower pace. Each introduces themselves. Only these three voices speak. All utterances are synthesized locally with FFmpeg/libflite. The target audio duration is three minutes thirty seconds. Check verification.json for measured durations.

## Expected findings and supporting pairs

1. **Pilot date:** brief/email December 7, 2026 versus architecture/checklist January 18, 2027.
2. **Atlas edits:** brief/scope say read-only and not evidence; meeting notes argue saved edits should become evidence.
3. **Memory approval:** architecture requires pending/member review; lead email proposes automatic writes without review; meeting outcome is open.
4. **Routing:** architecture/scope require Unknown Context and exclude auto-routing; lead email/meeting proposal prefer nearest-project auto-routing.
5. **Missing owners/approval:** meeting names no accountable owner; checklist has no owners, checked items, completion evidence or signed approval; email has no accepted follow-up owner.

The spoken discussion includes all five with opposing statements. Missing owners/approval is a gap, not proof that two factual statements contradict. A proposal or speaker's attendance does not prove authority. Synora's Unknown Context behavior in these fixtures describes the source project's disputed policy; it is not an instruction to change ContextGuard.

## Manual tests in ContextGuard

1. Create/select your **Synora** test project. A useful goal is: "Is the first Synora pilot ready? Check its date, Atlas evidence policy, requirement-memory approval, project routing, and accountable owners." Use fictional data only.
2. **Documents:** upload only `01` through `06` together (six supported Markdown documents). Confirm permission and process them. Check all five categories, open each finding and follow its citations to the exact original passages. The date finding should reference opposite dates; other policy findings should show both sides and retain uncertainty about approval.
3. **Transcript text:** run a separate review with the transcript's spoken section. Copy from the first timestamp through the last utterance; exclude the header, BEGIN/END markers and planted-conflict answer key. Keep speaker names and timestamps. Check whether findings cite the actual spoken passages and preserve the unresolved ending.
4. **Audio/transcription:** use the MP3 (or WAV) in your transcription tool, then compare its output to the spoken section of the supplied transcript before processing it. ContextGuard's current document form accepts TXT/MD/PDF/DOCX; these audio files are not document uploads. An audio input path must actually support transcription before using it.
5. **Vexa/meeting path:** in an authorized test meeting, let Vexa join explicitly and ensure it can hear the discussion (read the script, or share/play the audio through a meeting input that reaches the bot). Fetch its actual transcript and review it. Confirm real speaker/timestamp coverage before treating this as a meeting-source test; playing an MP3 locally alone does not establish that Vexa heard it.
6. **WhatsApp:** in a selected authorized test chat, manually post the fictional discussion turns with speaker labels, or use a text export of that test conversation. Collect new messages only after selecting the chat, then process in Project Reviews. Verify citations use the actual imported message/chat identifiers. The fictional names in message bodies are not account identities.
7. **Slack:** manually post the fictional turns or relevant document passages in a dedicated test channel/thread the connector is authorized to read. Import that selected conversation and inspect citations to its actual Slack messages. Do not assume private-channel access or permissions that have not been granted.
8. Compare findings across separate source tests. Do not resolve them just because the newest message makes a proposal. If you intentionally answer a finding later, inspect the authorized confirmation and saved decision separately.

Use the planted-conflict list only to judge results. Do not include README.md, verification.json or the transcript answer key in analysis input; doing so would hand the detector the answers. Automatic result quality and live connectors have not been tested by creating this pack.

## File verification and reproduction

The generator is `../../scripts/generate_synora_source_samples.py` relative to this sample folder. Run from `contextguard-rebuild`:

```powershell
.\.venv\Scripts\python.exe scripts/generate_synora_source_samples.py --verify-only
```

Omit `--verify-only` to regenerate this dedicated sample folder with installed FFmpeg/libflite and ffprobe. Regeneration overwrites this pack's generated files; copy it first if you have edited them.

Checks include complete MP3/WAV decode with FFmpeg, ffprobe durations, three-to-four-minute bounds, exactly three named speakers/intros, exact transcript-to-synthesis-text equality, every complete spoken PCM segment's hash and location in the WAV, MP3/WAV audio correlation, and opposing conflict phrases in multiple documents and in the audio script. This is verification by deterministic synthesis and file integrity; no independent speech-recognition accuracy claim is made. The validation key at the end of the transcript is intentionally not audio.

**No ContextGuard app was started and no review was run or claimed to pass.**
