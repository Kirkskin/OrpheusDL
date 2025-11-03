# OrpheusDL Setup Log

## Phase 1 – Environment Readiness

### Actions
- 2025-03-05T00:00Z approx: Verified project root `/mnt/c/Users/xipher/Documents/OrpheusDL` matches working copy.
- 2025-03-05T00:00Z approx: Confirmed existing virtual environment at `.venv/`; will reuse for all project commands.
- 2025-03-05T00:00Z approx: Installed system `ffmpeg` package via `sudo apt-get install -y ffmpeg` (success).
- 2025-03-05T00:00Z approx: Verified core Python dependencies previously installed inside `.venv` via `pip install -r requirements.txt` (no issues reported).
- 2025-03-05T00:00Z approx: Added `.vscode/settings.json` to point VS Code at `.venv` interpreter and auto-activate in terminals.

### Version Snapshot
- Python: `Python 3.12.3` (`/mnt/c/Users/xipher/Documents/OrpheusDL/.venv/bin/python`)
- ffmpeg: `ffmpeg 6.1.1-3ubuntu5` (`/usr/bin/ffmpeg`)

### Notes
- Dedicated environment: `.venv` (activate with `source .venv/bin/activate`).
- Requirements are installed inside the virtual environment; no global site packages used.
- VS Code Python extension and integrated terminals will default to `.venv`.
- Phase 1 acceptance criteria met.

## Phase 2 – Module Acquisition

### Actions
- 2025-03-05T00:15Z approx: Replaced local ignored module folders with fresh clones from upstream module repositories.
- 2025-03-05T00:15Z approx: Verified each module folder includes expected `interface.py`.

### Module Versions
| Module | Repository | Branch | Commit |
| --- | --- | --- | --- |
| tidal | https://github.com/Dniel97/orpheusdl-tidal | master | 14305d3a68268ff78489054b0ccb64e0378f477b |
| qobuz | https://github.com/OrfiDev/orpheusdl-qobuz | master | 6dc5c7e2bd9820a6a80b9ba4d3004fbdc6955e44 |
| napster | https://github.com/OrfiDev/orpheusdl-napster | main | e0774e706daea92bacf8fdf5d46c4022168afc8d |
| kkbox | https://github.com/uhwot/orpheusdl-kkbox | master | 0b5b87d7512fcb43323a36ac469bf9a4d5c3692b |
| deezer | https://github.com/uhwot/orpheusdl-deezer | master | b6e3492a27e53f9311126971b719b1b17405d2c4 |
| beatport | https://github.com/Dniel97/orpheusdl-beatport | master | cfd182ceffaf121e5b2023d166d96280a22e7654 |
| soundcloud | https://github.com/OrfiDev/orpheusdl-soundcloud.git | master | 7fc264910ac9a896b91a8428fb1e9b822413e37e |
| applemusic | https://github.com/OrfiDev/orpheusdl-applemusic-basic | master | 0bfec77d87012a91dd2a6f5de5dc065449ff80b5 |
| bugsmusic | https://github.com/Dniel97/orpheusdl-bugsmusic | master | 3b3c0a3c3ea0ea5f606498dd1066a986eeb419a4 |
| jiosaavn | https://github.com/bunnykek/orpheusdl-jiosaavn | master | 0c20361935f83c61972b7eddccda446be57090ec |
| nugs | https://github.com/Dniel97/orpheusdl-nugs | master | b65718c1dd7b22d57eac645fc960b24a3a24aa0a |
| beatsource | https://github.com/bascurtiz/orpheusdl-beatsource | master | 9f0133d48fb9580d5bf65fef37d43f0c3db0518f |
| genius | https://github.com/Dniel97/orpheusdl-genius | master | d4aaab5f4536af7d3085811006bcf61dde361784 |
| lrclib | https://github.com/rayun56/orpheusdl-lrclib | master | 2c1e2ee471c203954a4d1afed288b066ac4946ae |

### Notes
- Module folders remain git-ignored per project guardrails; upstream commit hashes logged for traceability.
- 2025-03-05T00:55Z approx: Installed module prerequisites (`xmltodict`, `pbkdf2`, `pytz`, `pysrp`, `srp`) inside `.venv`; aliased Apple Music SRP import for compatibility.
- Phase 2 acceptance criteria met.

## Phase 3 – Configuration Genesis

### Actions
- 2025-03-05T00:25Z approx: Ran `.venv/bin/python orpheus.py settings refresh` to regenerate `config/settings.json`.
- 2025-03-05T00:26Z approx: Updated `config/settings.json` with absolute download path, explicit `ffmpeg_path`, and per-module quality placeholders.

### Validation
- Settings file path: `/mnt/c/Users/xipher/Documents/OrpheusDL/config/settings.json`.
- JSON schema check: `python -c "import json; json.load(open('config/settings.json'))"` → success.
- Modules covered: tidal, qobuz, napster, kkbox, deezer (each now includes `preferred_quality` field).
- Global section includes `download_path` `/mnt/c/Users/xipher/Documents/OrpheusDL/downloads` and `ffmpeg_path` `/usr/bin/ffmpeg`.

### Notes
- Settings ready for credential injection in later phases.
- Phase 3 acceptance criteria met.

## Phase 4 – Discovery & URL Sanity

### Actions
- 2025-03-05T00:32Z approx: Instantiated `Orpheus()` inside `.venv` to confirm installed modules are detected.
- 2025-03-05T00:34Z approx: Ran offline pattern-matching script to verify representative track/album/playlist URLs for each module.

### Discovery Report
| Module | Detected |
| --- | --- |
| tidal | ✅ |
| qobuz | ✅ |
| napster | ✅ |
| kkbox | ✅ |
| deezer | ✅ |

### URL Patterns Sanity Check
| Module | Track | Album | Playlist |
| --- | --- | --- | --- |
| tidal | ✅ | ✅ | ✅ |
| qobuz | ✅ | ✅ | ✅ |
| napster | ✅ | ✅ | ✅ |
| kkbox | ✅ | ✅ | ✅ |
| deezer | ✅ | ✅ | ✅ |

### Notes
- Pattern validation reused the modules’ documented regex/parse logic without making network requests.
- Phase 4 acceptance criteria met.

## Phase 5 – Authentication Bootstrap

### Actions
- 2025-03-05T00:40Z approx: Reviewed README/auth docs for tidal, qobuz, napster, kkbox, and deezer modules to capture credential requirements.
- 2025-03-05T00:42Z approx: Verified `config/` remains git-ignored to keep secrets out of version control.
- 2025-03-05T00:43Z approx: Recorded credential placeholders in `config/settings.json`; no secrets written.

### Module Auth Status
| Module | Auth Method | Secrets Present | Notes |
| --- | --- | --- | --- |
| tidal | Device/TV & mobile session login (tokens + browser/device flow) | No | Needs TV device login plus optional mobile credentials; run `python orpheus.py` and follow prompts. |
| qobuz | Username/password with app ID/secret | No | Populate `app_id`, `app_secret`, `username`, `password` in `config/settings.json`. |
| napster | API key/secret + username/password | No | Fill `api_key`, `customer_secret`, `requested_netloc`, `username`, `password`; then rerun module login when ready. |
| kkbox | API keys + email/password | No | Supply `kc1_key`, `secret_key`, `email`, `password`; module stores session token in `config/loginstorage.bin`. |
| deezer | Client id/secret + email/password + bf_secret | No | Update Deezer credentials in settings; avoid logging values. |

### Notes
- Awaiting user-provided credentials before running any login routines; add them directly to `config/settings.json` (still ignored by git).
- Once credentials are added, rerun `python orpheus.py` to allow each module to store refreshed sessions.
- Phase 5 acceptance criteria pending user credential entry; placeholders documented.
- Deezer module updated to accept direct ARL input (see module README and `config/settings.json`).
- Qobuz module now supports supplying a `user_auth_token` directly in settings for token-based login.
