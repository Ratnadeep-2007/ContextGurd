"""Create/check fictional source files only. Never imports or starts ContextGuard."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'samples/synora-all-sources'
BUILD = ROOT / 'artifacts/synora-sample-build'
STEM = '07-synora-pilot-discussion'
RATE = 24000
GAP = 0.32
VOICES = {'Meera': ('slt', 1.0, 'female'), 'Aarav': ('rms', 1.0, 'male'), 'Rohan': ('awb', 0.81, 'male, slower pace')}

DOCUMENTS = {
    '01-product-brief.md': '''# Synora product brief

Fictional test material. Project: Synora. Release: the first internal pilot.
Record date: November 2, 2026. Status: product baseline supplied for review; formal sign-off is not attached.

## Purpose and pilot date

Synora is an AI project-intelligence workspace that brings project conversations and documents into shared project context. It helps members understand decisions, requirements, dependencies and uncertainty. The first internal pilot is planned for **December 7, 2026**. This date refers to the same pilot discussed in the architecture notes, not a separate preview or milestone.

## Sources and Atlas

The pilot input scope is Google Meet transcripts, explicitly selected WhatsApp conversations, and manual document or text uploads. The Excalidraw Atlas is a **read-only generated view** of retained project context. **Canvas edits are NOT evidence.** Saving or rearranging the generated canvas must not create a source passage or change an approved requirement. Source-linked project records remain the basis of the view.

## Decisions, routing and responsibility

Changes to approved requirements should be reviewed by an authorized member before they enter approved project memory. Unclear project references must wait for human routing confirmation; similarity alone does not prove a project match. The first pilot does not include automatic routing of uncertain evidence.

The project lead must confirm the date, memory-approval policy and release readiness. No named approver, accountable release owner, approval record or completed readiness evidence is included with this brief. Treat the date as a plan awaiting that confirmation.
''',
    '02-architecture-notes.md': '''# Synora architecture notes

Fictional test material. Project: Synora. Release: the first internal pilot.
Record date: November 2, 2026. Status: working architecture proposal; no approval signature.

## Pilot schedule

The working architecture plan targets **January 18, 2027** for the first internal pilot. This is the same pilot named in the product brief. The notes do not explain or approve a move from the brief's December date. No scope or version distinction is offered to reconcile the dates.

## Evidence and approved memory

Google Meet, selected WhatsApp conversations and manual uploads feed one shared evidence pipeline. Excalidraw Atlas remains a read-only generated view; saved canvas edits are not source evidence.

**Changes to an approved requirement stay pending until a member reviews them.** The system may propose a replacement requirement, but it must not automatically write the replacement into approved project memory. A reviewer must record approval before that requirement changes. Whether this review gate is the final pilot policy is still awaiting the project lead's confirmation.

## Project routing

**Ambiguous evidence stays in Unknown Context** until a member confirms the project. Never choose the nearest project automatically merely to empty that queue. Explicit source authorization and workspace boundaries must be respected.

## Open responsibilities

The memory-policy approver, routing reviewer and release approver have not been named. There is no attached decision log, approval response or completion evidence. These notes are not proof that the pilot is ready.
''',
    '03-meeting-notes.md': '''# Synora pilot discussion notes

Fictional test material. Meeting date: November 3, 2026.
Participants: Meera, Aarav and Rohan. These are sample speakers, not actual ContextGuard accounts.
Scope: the same first internal Synora pilot covered by the brief and architecture notes.

## Disagreements recorded

Meera defended **December 7, 2026** as the pilot date in the product brief. Aarav argued that **January 18, 2027** in the architecture plan is the date engineering can support. Rohan asked for a decision record; none was supplied.

Aarav argued that **canvas edits SHOULD become evidence after save**, including direct Atlas edits to requirement text. Meera objected that Atlas is a read-only generated view and canvas edits are not evidence. This disagreement was not resolved.

Meera proposed that new requirement changes should write into approved memory automatically to avoid a queue. Aarav argued for the review-first gate: approved-requirement changes must remain pending until a member reviews them. **The memory-approval decision was left open.**

Meera also proposed auto-routing uncertain references to the closest project. Aarav objected that ambiguous evidence belongs in Unknown Context until routing is confirmed. Rohan noted that auto-routing and direct Atlas-edit ingestion are outside the documented pilot scope.

## Outcome and follow-up

**No decision was taken. No owner was named** for the date, Atlas policy, memory review, routing review or release approval. Rohan requested confirmation with the project lead. Nobody accepted responsibility for that action, and no due date or approval response was recorded. Attendance does not establish decision authority. Do not mark any disagreement resolved based on these notes.
''',
    '04-release-checklist.md': '''# Synora first-pilot readiness checklist

Fictional test material. Target: **January 18, 2027**.
Record date: November 3, 2026. This targets the same first pilot as the brief.
Status: not signed off. All boxes below are deliberately unchecked.

- [ ] Confirm the pilot date with the project lead and reconcile the December 7, 2026 product brief.
- [ ] Confirm that Excalidraw Atlas is read-only and that canvas edits are not evidence, or formally approve a scope change.
- [ ] Confirm whether approved-requirement changes use review-first approval or automatic writes to project memory.
- [ ] Confirm that ambiguous evidence stays in Unknown Context and that auto-routing is excluded, or formally approve an exception.
- [ ] Name the person accountable for each unresolved policy and release decision.
- [ ] Name the member authorized to approve requirement changes.
- [ ] Name the member who can confirm ambiguous project routing.
- [ ] Attach successful Google Meet, selected WhatsApp and manual-upload completion evidence.
- [ ] Attach the project lead's final release approval and its date.

Every checklist item has **no assigned owner**, no completion date, no linked test result and no attached approval. There are no completed subtasks hidden behind these boxes. An unchecked target-date checklist is not evidence of readiness or approval.
''',
    '05-integration-scope.md': '''# Synora first-pilot integration scope

Fictional test material. Record date: November 2, 2026.
Status: scope boundary supplied for review; the final approver is not identified.

## Included

- Authorized Google Meet transcripts, preserving speakers and timestamps.
- Explicitly selected WhatsApp conversations, preserving message provenance.
- Manual text and document uploads.
- Shared project context with links back to the original evidence.
- An Excalidraw Atlas rendered as a read-only generated view.

## Explicitly outside this pilot

**Direct Atlas-edit ingestion is OUT of the pilot.** Saving canvas edits must not turn them into evidence or update requirements. The generated Atlas is a view; approved source records feed it.

**Auto-routing is OUT of the pilot.** Ambiguous evidence must remain in Unknown Context until a member confirms its project. There is no approved exception permitting a nearest-project guess.

Automatic writes that replace approved requirements without member review are not approved by this scope note. The memory-approval policy still needs confirmation, and the architecture review-first gate must not be silently bypassed.

## Approval gap

No owner is assigned to approve a scope change, review ambiguous routing or settle the memory policy. No signed exception, project-lead approval or release-readiness result is attached. A meeting suggestion alone does not establish an approved scope change.
''',
    '06-project-lead-email.md': '''# Fictional email from the Synora project lead

Fictional test material. This is an invented email; no real message was sent.
From: Synora Project Lead <lead@synora.example>
To: Pilot discussion group <pilot@synora.example>
Date: November 3, 2026
Subject: Proposal to keep the first pilot on December 7

Team,

I propose we keep the first internal Synora pilot on **December 7, 2026**. I understand the architecture notes and release checklist say January 18, 2027. I am referring to the same pilot, not an earlier demonstration. Please reconcile the dates with me before treating either one as final approval.

To reduce review queues, I also propose **automatically writing approved-requirement changes into project memory without a member review**. That differs from the architecture note that keeps changes pending until reviewed. Please bring the disagreement back for an explicit policy decision; this email does not record a completed approval.

For routing, I would prefer **auto-routing ambiguous evidence to the closest project**, rather than leaving it in Unknown Context. I know the integration scope excludes auto-routing. Treat this as a proposed exception that still needs to be considered.

The Atlas policy also remains disputed: the brief says canvas edits are not evidence, while the meeting suggestion would ingest them after save. I have not approved direct Atlas-edit ingestion.

Who is accountable for reconciling these policies and signing off the pilot? No owner has accepted that work, and I have not received completion evidence or a signed checklist. Arrange a confirmation discussion with me. Until then, the date, memory policy, routing exception and Atlas treatment remain unresolved.

Synora Project Lead (fictional role; individual identity deliberately unspecified)
''',
}

# Only these utterances are synthesized. Labels/timestamps and the answer key are not spoken.
TURNS = [
    ('Meera', "I am Meera. I am speaking from product planning, but I cannot approve this pilot. The brief says December seventh, twenty twenty-six. Why are the architecture notes planning January eighteenth, twenty twenty-seven?"),
    ('Aarav', "I am Aarav. I am reviewing the architecture, and I disagree with that December date. January eighteenth, twenty twenty-seven is the working plan. This is the same Synora pilot, not a different release."),
    ('Rohan', "I am Rohan. I am checking release readiness. Neither date has a signed approval. The January checklist is completely unchecked, and nobody is named as its owner. A calendar target is not completion evidence."),
    ('Meera', "The lead's email proposes December seventh. Waiting until January eighteenth changes our pilot commitment. I want the earlier date, but the email also asks us to confirm it. We cannot call it a final decision."),
    ('Aarav', "I still support January eighteenth. The email is a proposal, and it does not override the architecture plan. We need the project lead to settle this date conflict explicitly."),
    ('Rohan', "Then stop presenting either date as agreed. Who will ask the lead? No one has accepted that action, and we still have no release approver or completion results."),
    ('Aarav', "I also want saved Atlas edits to become evidence. When a member changes a requirement on the canvas and saves it, Synora should ingest that change. A read-only Atlas feels too restrictive."),
    ('Meera', "I disagree. The product brief makes Excalidraw Atlas a read-only generated view. Canvas edits are not evidence. Saving a drawing cannot establish an approved requirement or replace an original source."),
    ('Rohan', "The integration scope explicitly excludes direct Atlas-edit ingestion. Aarav is proposing a scope change. We have neither an owner nor an approval record for that change."),
    ('Aarav', "I understand the exclusion, but I still think a saved Atlas edit should count as evidence. I am arguing for changing the policy, not claiming that anybody has approved it."),
    ('Meera', "For project memory, I support the lead's separate proposal. Requirement changes should write into memory automatically. A queue for every change will slow the pilot, and I want that queue removed."),
    ('Aarav', "No. The architecture notes require changes to approved requirements to stay pending until a member reviews them. Automatically writing them into approved memory removes the review-first gate. I oppose that."),
    ('Rohan', "We left the memory-approval decision open in the meeting notes. Nobody is named to approve those changes. Neither an email proposal nor a missing owner gives the system authority to choose."),
    ('Meera', "I also prefer auto-routing ambiguous evidence to the closest project. Leaving it in Unknown Context feels like lost work. The lead suggested this too, although I know the scope excludes auto-routing."),
    ('Aarav', "I disagree again. Ambiguous evidence must stay in Unknown Context until a member confirms the project. Similar wording does not establish project identity. Auto-routing would violate the pilot's stated scope."),
    ('Rohan', "A conversation can mention several projects or no project at all. We have no named routing reviewer. Until an authorized person resolves that, the routing conflict and its owner are both open."),
    ('Meera', "So I still want December, automatic memory writes, and a proposed routing exception. Aarav wants January, review-first memory, and Unknown Context. We also disagree about saved Atlas edits. We have not reached agreement."),
    ('Rohan', "No decision has been taken. The next action is to confirm the pilot date, Atlas policy, memory approval, routing policy, and accountable owners with the project lead. Nobody has accepted ownership of that action yet."),
]

CONFLICTS = {
    'pilot_date': {'description': 'December 7, 2026 versus January 18, 2027 for the same first pilot.',
                   'anchors': ['December 7, 2026', 'January 18, 2027']},
    'atlas_edits': {'description': 'Saved canvas edits become evidence versus Atlas stays read-only and edits are not evidence.',
                    'anchors': ['canvas edits are not evidence', 'canvas edits should become evidence after save']},
    'memory_approval': {'description': 'Automatic approved-requirement memory writes versus pending until member review.',
                        'anchors': ['changes to an approved requirement stay pending until a member reviews them', 'automatically writing approved-requirement changes into project memory without a member review']},
    'routing': {'description': 'Auto-route ambiguous evidence versus retain it in Unknown Context until human confirmation.',
                'anchors': ['ambiguous evidence stays in unknown context', 'auto-routing ambiguous evidence to the closest project']},
    'missing_owners_approval': {'description': 'No accountable owners, accepted follow-up, signed policy approval or readiness evidence.',
                                'anchors': ['no owner was named', 'no assigned owner', 'no owner has accepted']},
}


def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError('File-only command failed: ' + ' '.join(map(str, args)) + '\n' + result.stderr[-2000:])
    return result.stdout


def pcm(path):
    with wave.open(str(path), 'rb') as source:
        assert (source.getnchannels(), source.getsampwidth(), source.getframerate()) == (1, 2, RATE)
        return source.readframes(source.getnframes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    return f'{milliseconds // 60000:02}:{milliseconds // 1000 % 60:02}.{milliseconds % 1000:03}'


def generate():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    for name, content in DOCUMENTS.items():
        (OUTPUT / name).write_text(content, encoding='utf-8')
    segments = []
    for index, (speaker, text) in enumerate(TURNS, 1):
        name = f'turn-{index:02}'
        (BUILD / (name + '.txt')).write_text(text, encoding='ascii')
        voice, tempo, gender = VOICES[speaker]
        run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
             '-i', f'flite=textfile={name}.txt:voice={voice}', '-ar', str(RATE), '-ac', '1',
             '-c:a', 'pcm_s16le', name + '-raw.wav'], BUILD)
        segments.append({'speaker': speaker, 'text': text, 'voice': voice, 'gender': gender, 'tempo': tempo,
                         'raw_name': name + '-raw.wav', 'render_name': name + '.wav'})
    estimated = sum(len(pcm(BUILD / row['raw_name'])) / (RATE * 2 * row['tempo']) for row in segments) + GAP * (len(segments) - 1)
    global_tempo = (estimated - GAP * (len(segments) - 1)) / (210 - GAP * (len(segments) - 1))
    # Rate adjustment preserves the wording and Rohan's slower relative delivery.
    position = 0
    audio = bytearray()
    turn_data = []
    for index, row in enumerate(segments):
        factor = row['tempo'] * global_tempo
        assert .5 <= factor <= 2, 'Unexpected speech rate: inspect script rather than truncate it.'
        run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', row['raw_name'],
             '-af', f'atempo={factor:.9f}', '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le', row['render_name']], BUILD)
        content = pcm(BUILD / row['render_name'])
        frames = len(content) // 2
        turn_data.append({k: row[k] for k in ('speaker', 'text', 'voice', 'gender')} |
                         {'start_frame': position, 'frame_count': frames, 'start_seconds': position / RATE,
                          'end_seconds': (position + frames) / RATE, 'tempo_factor': factor,
                          'pcm_sha256': digest(content)})
        audio.extend(content)
        position += frames
        if index < len(segments) - 1:
            gap_frames = round(GAP * RATE)
            audio.extend(bytes(gap_frames * 2))
            position += gap_frames
    wav_path = OUTPUT / (STEM + '.wav')
    with wave.open(str(wav_path), 'wb') as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(RATE)
        target.writeframes(audio)
    run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav_path),
         '-codec:a', 'libmp3lame', '-b:a', '128k', '-id3v2_version', '3',
         '-metadata', 'title=Fictional Synora pilot discussion', '-metadata', 'artist=Meera; Aarav; Rohan (synthetic voices)',
         str(OUTPUT / (STEM + '.mp3'))])
    transcript = ['FICTIONAL SYNORA PILOT DISCUSSION',
                  'Exact speech input; approximate timestamps. Exactly three synthetic speakers.',
                  'Only text between BEGIN/END SPOKEN TRANSCRIPT is spoken. The answer key is not spoken.',
                  '', 'BEGIN SPOKEN TRANSCRIPT']
    transcript += [f"[{timestamp(row['start_seconds'])}] {row['speaker']}: {row['text']}" for row in turn_data]
    transcript += ['END SPOKEN TRANSCRIPT', '', 'PLANTED CONFLICTS - VALIDATION KEY, NOT SPOKEN',
                   *[f'{index}. {row["description"]}' for index, row in enumerate(CONFLICTS.values(), 1)],
                   '', 'Outcome: no decision taken; confirm with the project lead; action owner not accepted.']
    (OUTPUT / (STEM + '-transcript.txt')).write_text('\n'.join(transcript) + '\n', encoding='utf-8')
    manifest = {'fictional': True, 'generation': 'Local FFmpeg libflite; no external TTS or account contacted.',
                'sample_rate': RATE, 'turns': turn_data, 'global_tempo_factor': global_tempo,
                'speaker_count': 3, 'expected_conflicts': CONFLICTS,
                'transcript_verification_method': 'Exact canonical TTS input per turn plus SHA-256 of every complete spoken PCM segment in the WAV.',
                'independent_asr_performed': False, 'app_started_or_review_run': False}
    (OUTPUT / 'verification.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    write_readme()
    verify()


def write_readme():
    content = '''# Synora samples for every source

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
.\\.venv\\Scripts\\python.exe scripts/generate_synora_source_samples.py --verify-only
```

Omit `--verify-only` to regenerate this dedicated sample folder with installed FFmpeg/libflite and ffprobe. Regeneration overwrites this pack's generated files; copy it first if you have edited them.

Checks include complete MP3/WAV decode with FFmpeg, ffprobe durations, three-to-four-minute bounds, exactly three named speakers/intros, exact transcript-to-synthesis-text equality, every complete spoken PCM segment's hash and location in the WAV, MP3/WAV audio correlation, and opposing conflict phrases in multiple documents and in the audio script. This is verification by deterministic synthesis and file integrity; no independent speech-recognition accuracy claim is made. The validation key at the end of the transcript is intentionally not audio.

**No ContextGuard app was started and no review was run or claimed to pass.**
'''
    (OUTPUT / 'README.md').write_text(content, encoding='utf-8')


def verify():
    report_path = OUTPUT / 'verification.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    transcript = (OUTPUT / (STEM + '-transcript.txt')).read_text(encoding='utf-8')
    spoken = transcript.split('BEGIN SPOKEN TRANSCRIPT\n', 1)[1].split('\nEND SPOKEN TRANSCRIPT', 1)[0]
    parsed = re.findall(r'^\[(\d+:\d+\.\d+)\] (Meera|Aarav|Rohan): (.+)$', spoken, re.MULTILINE)
    assert [(speaker, text) for _, speaker, text in parsed] == TURNS, 'Transcript differs from exact TTS input.'
    assert len(parsed) == len(report['turns']) == len(TURNS)
    assert set(speaker for speaker, _ in TURNS) == {'Meera', 'Aarav', 'Rohan'}
    for speaker in VOICES:
        first = next(text for who, text in TURNS if who == speaker)
        assert first.startswith('I am ' + speaker + '.')
    wav_data = pcm(OUTPUT / (STEM + '.wav'))
    cursor = 0
    for (stamp, speaker, text), row in zip(parsed, report['turns']):
        assert (speaker, text) == (row['speaker'], row['text'])
        assert stamp == timestamp(row['start_seconds'])
        start, end = row['start_frame'] * 2, (row['start_frame'] + row['frame_count']) * 2
        assert start >= cursor and not any(wav_data[cursor:start]), 'Unexpected audio outside the three speakers turns.'
        assert digest(wav_data[start:end]) == row['pcm_sha256'], 'Spoken audio turn differs from recorded synthesis.'
        cursor = end
    assert cursor == len(wav_data), 'Unaccounted trailing audio.'
    speaker_rates = {}
    for speaker in VOICES:
        turns = [row for row in report['turns'] if row['speaker'] == speaker]
        words = sum(len(row['text'].split()) for row in turns)
        seconds = sum(row['frame_count'] / RATE for row in turns)
        speaker_rates[speaker] = {'words': words, 'speech_seconds': seconds, 'words_per_minute': 60 * words / seconds,
                                  'voice': VOICES[speaker][0], 'gender': VOICES[speaker][2]}
    assert speaker_rates['Rohan']['words_per_minute'] < min(speaker_rates[name]['words_per_minute'] for name in ('Meera', 'Aarav'))
    measures = {}
    for suffix in ('.wav', '.mp3'):
        path = OUTPUT / (STEM + suffix)
        run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'])
        probe = json.loads(run(['ffprobe', '-v', 'error', '-show_entries',
                               'format=duration:stream=codec_name,sample_rate,channels', '-of', 'json', str(path)]))
        duration = float(probe['format']['duration'])
        assert 180 <= duration <= 240, 'Audio is outside the required three-to-four-minute window.'
        measures[suffix] = probe
    assert abs(float(measures['.wav']['format']['duration']) - float(measures['.mp3']['format']['duration'])) < .15
    decoded = BUILD / 'decoded-mp3.wav'
    BUILD.mkdir(parents=True, exist_ok=True)
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(OUTPUT / (STEM + '.mp3')),
         '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le', str(decoded)])
    from array import array
    reference, encoded = array('h'), array('h')
    reference.frombytes(wav_data)
    encoded.frombytes(pcm(decoded))
    assert abs(len(reference) - len(encoded)) < RATE * .1
    # LAME gapless decoding should preserve alignment; compare the complete content every 32nd sample.
    size = min(len(reference), len(encoded))
    a, b = reference[:size:32], encoded[:size:32]
    correlation = sum(x * y for x, y in zip(a, b)) / (sum(x*x for x in a) * sum(y*y for y in b)) ** .5
    assert correlation > .96, 'MP3 does not match the WAV content.'
    cleaned = {name: re.sub(r'\s+', ' ', content.replace('*', '').lower()) for name, content in
               ((name, (OUTPUT / name).read_text(encoding='utf-8')) for name in DOCUMENTS)}
    coverage = {}
    for key, conflict in CONFLICTS.items():
        matches = {anchor: [name for name, body in cleaned.items() if anchor.lower() in body]
                   for anchor in conflict['anchors']}
        assert all(matches.values()), 'A planted opposing statement is missing: ' + key
        assert len(set(name for names in matches.values() for name in names)) >= 2
        coverage[key] = matches
    checklist = (OUTPUT / '04-release-checklist.md').read_text(encoding='utf-8')
    boxes = re.findall(r'^- \[(.)\]', checklist, re.MULTILINE)
    assert len(boxes) == 9 and all(value == ' ' for value in boxes), 'Readiness items must all remain unchecked.'
    audio_text = ' '.join(text.lower() for _, text in TURNS)
    audio_checks = {
        'pilot_date': ['december seventh', 'january eighteenth'],
        'atlas_edits': ['saved atlas edits to become evidence', 'canvas edits are not evidence'],
        'memory_approval': ['write into memory automatically', 'stay pending until a member reviews them'],
        'routing': ['auto-routing ambiguous evidence', 'stay in unknown context until a member confirms'],
        'missing_owners_approval': ['no release approver', 'nobody has accepted ownership', 'no decision has been taken'],
    }
    for key, phrases in audio_checks.items():
        assert all(phrase in audio_text for phrase in phrases), 'Audio topic missing: ' + key
    assert TURNS[-1][0] == 'Rohan' and 'confirm' in TURNS[-1][1] and 'project lead' in TURNS[-1][1]
    report.update({'checks_passed': True, 'audio_probe': measures, 'mp3_wav_correlation': correlation,
                   'speaker_rates': speaker_rates, 'rohan_slower_than_other_speakers': True,
                   'only_declared_turns_and_silent_gaps': True,
                   'readiness_checklist_items': len(boxes), 'all_readiness_items_unchecked': True,
                   'document_conflict_coverage': coverage, 'audio_conflict_coverage': audio_checks,
                   'transcript_matches_exact_synthesis_input': True, 'all_spoken_pcm_segments_match': True,
                   'all_audio_decoded_without_errors': True,
                   'files': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
                             for p in sorted(OUTPUT.iterdir()) if p.is_file() and p.name != 'verification.json'}})
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'folder': str(OUTPUT), 'file_count': len(list(OUTPUT.iterdir())),
                      'wav_seconds': float(measures['.wav']['format']['duration']),
                      'mp3_seconds': float(measures['.mp3']['format']['duration']),
                      'speakers': list(VOICES), 'turns': len(TURNS), 'words': len(audio_text.split()),
                      'mp3_wav_correlation': round(correlation, 6), 'file_checks_passed': True,
                      'app_started_or_review_run': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    assert shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Install FFmpeg with libflite and ffprobe first.'
    verify() if args.verify_only else generate()
