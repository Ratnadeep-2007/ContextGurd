# Synora architecture notes (synthetic draft)

**Status:** Engineering discussion notes  
**Project:** Synora project-intelligence workspace

Synora receives information from Google Meet, WhatsApp, and supported manual uploads. Evidence retains its source and location. Context resolution and knowledge extraction feed the shared project-memory pipeline.

There is one shared Synora agent and one memory engine. Project identity and membership determine the context available to each task. Ambiguous routing stays in Unknown Context until a person assigns or keeps it.

Routine evidence-backed notes can update project memory automatically. A proposed replacement to an approved requirement, decision, or other high-impact project-state item must remain pending until a project member reviews it. The current approved value stays active while that proposal is pending.

Excalidraw is generated output. The model returns a structured visual plan; a deterministic compiler builds the canvas. User canvas edits do not flow back into the evidence pipeline.

**Pilot timing:** target **January 18, 2027**, after the approval workflow is verified.
