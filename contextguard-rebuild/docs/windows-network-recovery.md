# Local AI network denial and retry timing

If every provider reports outbound connection denied by local Windows/network permissions, the requests were blocked locally before provider inference. In this incident the server was launched by the agent's CodexSandboxOffline account. Its inherited network restrictions prevented Muse Wonder, Groq and NVIDIA access. Changing model keys or repeatedly submitting the same files does not resolve that process identity.

The sandbox-launched server was stopped only after verifying this rebuild's health identity and confirming there were no active intake jobs. No retained input, review or decision was deleted. The normal launcher now refuses to start the server under the actual Windows CodexSandboxOffline identity, with instructions to start it from the normal user account. Test-only isolated browser servers remain available for offline verification.

## Recover

1. Open this rebuild folder in File Explorer.
2. Double-click start.bat under your normal Windows account. No administrator elevation is required by this recovery step.
3. Open the printed local address, sign in and choose Retry retained input. Do not reupload the documents just to recover the saved run.
4. If the same error occurs from the normal account, inspect the local firewall/device network policy. A normal-user launch is not a guarantee of provider availability or valid model output.

Do not disable the Codex sandbox or widen global filesystem/firewall permissions to launch this app. This change does not claim a successful live review. The six-document review still needs to complete provider and citation checks.

## Timer correction

The old UI measured from intake.created to the latest update, so a retry could display hours of idle time as processing duration. New intakes and retries persist attempt_started and an incremented attempt number while keeping the original created timestamp. The UI measures the current attempt from attempt_started. Legacy jobs without this field are labelled Since original upload rather than suggesting an accurate attempt duration; their next retry starts a fresh clock.

Verification: 42 targeted Python tests, six progress UI tests, and four grouped isolated browser journeys passed. The browser check confirms that a retry increments its attempt and the displayed clock uses its new start. An actual offline-account probe detected this session, and start.bat refused to start a normal server here. No live model requests were performed for these checks.
