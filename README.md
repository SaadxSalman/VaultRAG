# VaultRAG

**Release status: ready for local evaluation and controlled single-user deployment.**

This repository contains a complete runnable local application: a Tauri desktop shell, React evidence desk, FastAPI service, document ingestion pipeline, privacy masking boundary, optional local NER adapter, typed API contracts, redacted audit events, persisted retrieval index, and local generation port. The default profile is intentionally retrieval-only and requires no cloud credentials or downloaded model to demonstrate the core workflow.

The project is finalized as a privacy-first local foundation. Organization-specific production controls such as encrypted storage, signed installers, sidecar supervision, FAISS semantic retrieval, and approved model evaluation remain deployment decisions rather than hidden assumptions.

VaultRAG is a desktop-first, local-only retrieval augmented generation (RAG) workspace for legal, medical, research, and other sensitive records. It is designed around one uncompromising rule: documents must remain on the operator's device. The project combines a Tauri desktop shell, a React evidence desk, a Python local API, deterministic privacy masking, and a local retrieval index.

> This project is a technical foundation, not legal or medical advice. It does not certify compliance with HIPAA, GDPR, CJIS, SOC 2, or any other regulatory framework. Deployments must be reviewed against their own policies, operating system controls, and threat model.

## What it does

1. A user adds a TXT, Markdown, PDF, or DOCX document from the desktop interface.
2. The local API extracts text and splits it into overlapping passages.
3. Passages are indexed on disk under `data/index`. The current implementation uses a dependable local TF-IDF index and is structured for a FAISS embedding adapter.
4. A query is scanned with deterministic regex rules for email addresses, phone numbers, SSNs, dates of birth, medical record numbers, and credit-card-shaped values.
5. Each detected value becomes a stable pseudo-token such as `<EMAIL_02F9C96A32>`. The original value is not placed in the query context sent to a model.
6. Local retrieval returns ranked evidence and source metadata.
7. Generation is deliberately disabled by default. The UI clearly reports retrieval-only mode until an operator explicitly enables and configures a downloaded local model.

The service binds to `127.0.0.1` by default. There are no cloud credentials, hosted inference calls, telemetry endpoints, analytics SDKs, or remote document stores in the application.

## Architecture

```text
Tauri window
    |
    +-- React/Vite evidence desk
    |       |
    |       +-- upload/query requests to 127.0.0.1:8765
    |
    +-- Rust shell (desktop packaging and permissions)

FastAPI local service
    |
    +-- ingestion.py: TXT/MD/PDF/DOCX extraction and chunking
    +-- masking.py: deterministic local PII replacement
    +-- retrieval.py: persisted local index and ranked search
    +-- main.py: health, document, and query API
    |
    +-- data/uploads: local source files
    +-- data/index/metadata.json: local chunk metadata
```

### Privacy boundary

The privacy boundary is the `_mask_for_context` call in `backend/main.py`. It runs before retrieval context is assembled and before the generation port is invoked. Both the retrieval-only generator and the optional local Transformers generator receive masked text. Do not bypass this boundary when adding a model provider.

Masking is deterministic within a configured salt. This is useful for questions that refer to the same person without revealing their name or identifier. It is not encryption, anonymization in the statistical sense, or a replacement for access control. Anyone who can read the source files can still read the originals.

## Requirements

### Runtime

- Windows 10/11, macOS, or Linux.
- Python 3.10 or newer. Python 3.12 is a practical default for current ML wheels.
- Node.js 20 or newer and npm.
- Rust stable and the Tauri system prerequisites.
- 4 GB RAM for retrieval-only mode. A local SLM may require substantially more RAM or a supported GPU.

### Windows prerequisites

Install the following before building the desktop app:

- Visual Studio Build Tools with **Desktop development with C++**.
- WebView2 Runtime (normally present on supported Windows installations).
- Rust via `rustup`.
- Node.js LTS.

The Tauri prerequisite documentation has the authoritative platform-specific list: <https://tauri.app/start/prerequisites/>.

## Quick start

Open PowerShell in the repository root.

### 1. Create the Python environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If your machine has no `py` launcher, use `python -m venv .venv` instead.

### 2. Configure the local environment

The repository includes an ignored `.env` with safe local defaults. `.env.example` is the shareable template. Keep real credentials, model paths, encryption keys, and institution-specific values in `.env` only. The `.gitignore` intentionally ignores `.env` and all other environment files except `.env.example`.

To recreate the file after a clean checkout:

```powershell
Copy-Item .env.example .env
```

There are currently no cloud keys to configure. `VAULTRAG_ENABLE_GENERATION=false` is the recommended first-run profile; enabling generation requires a locally available model and an explicit evaluation process.

### 3. Start the API

```powershell
python -m backend
```

The API is available at <http://127.0.0.1:8765>. Visit <http://127.0.0.1:8765/docs> for the generated local OpenAPI page.

### 4. Start the web UI

In a second terminal:

```powershell
npm install
npm run dev
```

Open <http://localhost:1420>. The browser UI and Tauri window use the same React application.

### 5. Run as a Tauri desktop app

Keep the Python API running, then use:

```powershell
npm run tauri dev
```

Create a distributable installer with:

```powershell
npm run tauri build
```

The current shell expects the API to be started separately. This keeps the Python environment, model lifecycle, and desktop packaging independently testable. A production distribution should add a signed sidecar or an installer-managed service after the organization chooses its process isolation and update policy.

## Environment reference

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `VaultRAG` | Display/service name. |
| `API_HOST` | `127.0.0.1` | Bind address. Keep loopback for local-only operation. |
| `API_PORT` | `8765` | Local API port. |
| `VAULTRAG_DATA_DIR` | `./data` | Root for local runtime data. |
| `VAULTRAG_INDEX_DIR` | `./data/index` | Persisted index metadata. |
| `VAULTRAG_UPLOAD_DIR` | `./data/uploads` | Original local documents. |
| `VAULTRAG_MAX_FILE_MB` | `25` | Upload size guard. |
| `VAULTRAG_TOP_K` | `5` | Default number of retrieved passages. |
| `VAULTRAG_EMBEDDING_MODEL` | MiniLM | Intended local embedding model setting. |
| `VAULTRAG_GENERATION_MODEL` | Phi 3.5 Unsloth | Intended local quantized SLM setting. |
| `VAULTRAG_ENABLE_GENERATION` | `false` | Explicit opt-in for generator integration. |
| `VAULTRAG_NER_MODEL` | empty | Local token-classification model path or cache name. |
| `VAULTRAG_ENABLE_NER` | `false` | Explicit opt-in for local NER. |
| `VAULTRAG_AUDIT_ENABLED` | `true` | Write redacted operational events. |
| `VAULTRAG_MAX_NEW_TOKENS` | `384` | Local generation output budget. |
| `VAULTRAG_LOG_LEVEL` | `INFO` | Python logging level. |

Values are loaded by `backend/config.py` using `pydantic-settings`. The application does not silently read arbitrary process secrets.

## API reference

### `GET /health`

Returns service status, indexed document count, chunk count, and whether generation is enabled.

### `GET /api/documents`

Returns grouped document metadata. Original file contents are not returned.

### `POST /api/documents`

Multipart upload with field name `file`. Supported extensions are `.txt`, `.md`, `.pdf`, and `.docx`. The response contains the generated document ID and number of passages added.

Example:

```powershell
curl.exe -F "file=@case-notes.txt" http://127.0.0.1:8765/api/documents
```

### `POST /api/query`

JSON body:

```json
{
  "query": "What phone number is associated with the claimant?",
  "top_k": 5,
  "mask_query": true
}
```

The response contains a masked query, count of masked entities, an answer status, ranked sources, and a bounded context preview. The preview exists for the local UI and should not be logged or sent outside the device.

### `DELETE /api/documents`

Clears the local index and uploaded source files. This is an irreversible local operation. A production release should add a confirmation dialog and secure deletion policy appropriate to the host filesystem.

## Local models and FAISS roadmap

The first-run experience intentionally works without downloading a model. This makes the privacy boundary inspectable and keeps installation practical on ordinary professional laptops. For semantic retrieval, replace the `LocalIndex` internals with:

1. A locally loaded `sentence-transformers` encoder from `VAULTRAG_EMBEDDING_MODEL`.
2. Normalized float32 vectors.
3. A persisted `faiss.IndexFlatIP` or an organization-approved FAISS index.
4. A metadata store mapping vector IDs to `Chunk` records.
5. An atomic write strategy so an interrupted indexing job cannot corrupt the prior index.

For local generation, add a separate adapter that loads `VAULTRAG_GENERATION_MODEL` through Transformers/Unsloth, never an HTTP inference endpoint. The adapter should:

- receive masked context only;
- enforce a bounded context window and output token limit;
- return source citations tied to chunk IDs;
- expose model load state and memory usage in `/health`;
- make model unload explicit;
- fail closed when no local model is available.

The current retrieval-only response is intentional until those safeguards are implemented and reviewed.

## Security model

### Included protections

- Loopback-only API default.
- No cloud API dependency.
- Ignored `.env` and runtime data directories.
- Deterministic replacement tokens before model context assembly.
- Upload extension and size validation.
- Explicit opt-in for generation.
- Local source names and scores in the UI without exposing source text in the document list.

### Important limitations

- The original documents remain in `data/uploads` and are not encrypted by this starter implementation.
- Regex masking misses novel formats and can produce false positives. NER is not yet wired into the pipeline.
- The salt is a process configuration value, not a key-management system.
- A compromised host, Python environment, desktop process, or user account can access local data.
- The TF-IDF fallback is lexical, not a semantic embedding index.
- Tauri does not automatically start or sandbox the Python API yet.
- Deleting a file does not guarantee forensic deletion on every filesystem.

Before handling regulated data, add OS-backed encryption, least-privilege service accounts, audit logging with content redaction, signed releases, dependency pinning and review, model provenance checks, secure update policy, backup policy, and an organization-approved NER model.

## Testing and verification

Compile the Python modules:

```powershell
python -m compileall backend tests
```

Run tests after installing development dependencies:

```powershell
python -m pytest -q
```

Run the UI typecheck/build:

```powershell
npm run build
```

Perform a manual local smoke test:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
curl.exe -F "file=@README.md" http://127.0.0.1:8765/api/documents
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/query -ContentType 'application/json' -Body '{"query":"What does VaultRAG do?"}'
```

Expected privacy behavior: a query containing `ada@example.com` returns a deterministic `<EMAIL_...>` token and never includes the literal email in the masked query.

## Project layout

```text
backend/                 Python local API and privacy pipeline
  audit.py               Redacted JSONL operational events
  config.py              Environment-backed settings
  generation.py          Retrieval-only and local Transformers ports
  ingestion.py           File extraction and overlap chunking
  main.py                FastAPI routes and privacy boundary
  masking.py             Deterministic regex masking
  ner.py                 Optional local token-classification adapter
  retrieval.py           Persisted local retrieval index
  schemas.py             Typed request and response contracts
src/                     React/Vite evidence desk
src-tauri/               Rust Tauri 2 desktop wrapper
tests/                   Focused core behavior tests
data/                    Ignored runtime data created on first run
.env                    Ignored local configuration
.env.example             Safe configuration template
requirements.txt          Python dependencies
package.json              Frontend and Tauri scripts
```

## Contribution guidelines

- Keep sensitive data out of fixtures, screenshots, logs, and issue descriptions.
- Add a focused test for every masking rule or privacy-boundary change.
- Do not add a cloud model provider without an explicit opt-in and a documented data-flow review.
- Keep public APIs backwards compatible where practical.
- Pin production dependencies after security review.
- Use `python -m compileall backend tests`, `python -m pytest -q`, and `npm run build` before opening a change.

## License and deployment note

No license has been selected for this starter repository. Choose and add one before redistribution. Treat deployment configuration, model weights, documents, and generated answers as separate governance concerns.

## Detailed component guide

### `backend/config.py`

`Settings` is the only configuration object used by the Python service. It reads the root `.env` file through `pydantic-settings`, applies typed defaults, and creates the local runtime directories. Keeping configuration in one object prevents individual modules from reaching into process environment variables with different names or assumptions.

The settings are intentionally prefixed with `VAULTRAG_` when they describe application behavior. Host and port settings use the shorter `API_` names because they are conventional service settings. In a managed deployment, mount the `.env` file with an operating-system permission that allows only the service account to read it.

### `backend/ingestion.py`

The ingestion module has three responsibilities:

1. Select a parser from the file suffix.
2. Normalize extracted text so layout noise does not dominate retrieval.
3. Split text into bounded, overlapping `Chunk` records.

The overlap is important. Without it, a sentence or definition that falls at a boundary can lose its subject in one passage and its conclusion in the next. The current defaults use a character-based window because it is predictable and works before a tokenizer is downloaded. A model-aware deployment can replace this with tokenizer token counts while preserving the `Chunk` contract.

PDF extraction is performed with PyMuPDF. DOCX extraction reads paragraph text with `python-docx`. Plain text and Markdown are treated as UTF-8 with replacement for malformed bytes. The service does not execute macros, render HTML, or evaluate document scripts.

### `backend/masking.py`

The masking pipeline is intentionally independent of any model library. Each detector produces a `MaskMatch` with a semantic kind, source span, and deterministic token. Matches are sorted by position and longest span so a specific identifier wins when it overlaps a broad phone-like expression.

Current deterministic detectors:

| Detector | Example shape | Replacement |
| --- | --- | --- |
| Email | `person@example.org` | `<EMAIL_HASH>` |
| SSN | `123-45-6789` | `<SSN_HASH>` |
| Date of birth | `01/24/1980` | `<DATE_OF_BIRTH_HASH>` |
| Medical record number | `MRN: A-10293` | `<MRN_HASH>` |
| Payment card | 13-19 digit card-shaped value | `<CREDIT_CARD_HASH>` |
| Phone | International or formatted phone-shaped value | `<PHONE_HASH>` |
| Optional NER | Local token-classification result | `<PERSON_HASH>` or model label |

The token hash is a truncated SHA-256 digest over a local salt, entity kind, and case-folded value. The original value cannot be recovered from the token by this code. The same local value maps to the same token, which lets a user ask follow-up questions about a masked subject without exposing the subject's identity.

Masking is not the same as redaction. A token may still be sensitive if the surrounding text identifies the person. It is also not a guarantee that every sensitive value is detected. For regulated workflows, combine these detectors with a reviewed local NER model, domain dictionaries, human review, and a clear policy for false negatives.

### `backend/ner.py`

`LocalNER` is an optional adapter around a Hugging Face token-classification pipeline. It is lazy: importing the service does not download or initialize a model. It uses `local_files_only=True`, so enabling it cannot silently fetch a model from the network. Operators must place a reviewed model in the local Transformers cache and set both `VAULTRAG_NER_MODEL` and `VAULTRAG_ENABLE_NER=true`.

NER spans are converted into the same `MaskMatch` type used by regex detectors. This is deliberate: there is one replacement mechanism and one overlap policy, regardless of how an entity was found. If the model is missing, startup remains safe when NER is disabled; an explicitly enabled but unavailable model fails loudly when a query or ingestion path tries to use it.

### `backend/retrieval.py`

`LocalIndex` is the persistence boundary for retrieved chunks. The first-run backend is TF-IDF with unigram and bigram features because it is deterministic, CPU-friendly, and easy to inspect. Metadata is stored as JSON and rewritten atomically through a temporary file replacement. A crash during a write therefore leaves either the previous complete metadata file or the new complete metadata file.

The return shape includes a one-based rank, a score, and a complete chunk record. The API masks the chunk text after retrieval before returning it to the UI or passing it to generation. This arrangement allows local lexical retrieval over the original corpus while maintaining a strict masked-context boundary for downstream model use.

The FAISS migration should preserve these invariants:

- vector IDs must map to stable chunk IDs;
- metadata and the FAISS index must be committed atomically as a pair;
- query vectors must use the same embedding model and normalization policy as document vectors;
- a failed rebuild must not destroy the last known-good index;
- index files must stay inside the configured local data directory;
- a rebuild must report progress and be cancellable for large case sets.

### `backend/generation.py`

Generation is represented by a small port rather than embedded in a route. `RetrievalOnlyGenerator` is the default and returns a truthful status message. `TransformersGenerator` loads a locally cached causal language model only when it is explicitly enabled. Both implementations receive a query and context that have already crossed the masking boundary.

The generator prompt instructs the model to use only evidence, state when evidence is insufficient, and avoid invented facts. This is a baseline control, not a substitute for evaluation. Production work should add citation enforcement, structured answer schemas, refusal tests, context budgets, output validation, and an evaluation corpus that contains adversarial and ambiguous cases.

### `backend/audit.py`

The audit logger is designed for operational visibility without becoming a second document store. Events are JSON Lines under `data/logs/events.jsonl`. Query, text, and error fields are masked before being written. Events record timestamps, counts, model mode, and document IDs, but not raw document contents.

Audit logs can still become sensitive through filenames, IDs, timing, or repeated pseudo-tokens. Protect the log directory with the same permissions as the index. Set `VAULTRAG_AUDIT_ENABLED=false` when an institution has a separate approved audit mechanism, and document that choice in the deployment record.

## End-to-end request lifecycle

### Document upload

```text
Browser/Tauri
  -> validate extension and size
  -> write source to data/uploads/<document-id>.<suffix>
  -> parse bytes locally
  -> normalize whitespace
  -> split into overlapping chunks
  -> add chunks to local index
  -> atomically persist metadata
  -> append redacted document_indexed event
  -> return count and extracted-character metadata
```

The source is written with a generated ID rather than the client filename. The original filename is retained as display metadata so the professional can identify evidence. A failed empty extraction removes the newly written file before returning the error.

### Query

```text
Client query
  -> request validation
  -> regex detection
  -> optional local NER detection
  -> deterministic replacement tokens
  -> local retrieval over masked query
  -> retrieved source text passes through the same masking pipeline
  -> bounded masked context is passed to the generator port
  -> typed response returns masked sources and generation mode
  -> redacted audit event is written
```

There is no route that accepts a cloud provider URL, API key, or remote model endpoint. Adding one would change the product's trust boundary and requires an explicit architectural review.

## Configuration profiles

### Retrieval-only laptop

Use this for development, review, and low-resource devices:

```dotenv
API_HOST=127.0.0.1
VAULTRAG_ENABLE_GENERATION=false
VAULTRAG_ENABLE_NER=false
VAULTRAG_AUDIT_ENABLED=true
VAULTRAG_TOP_K=5
```

### Local semantic retrieval

After placing an approved embedding model in the local cache, implement and test the FAISS adapter before changing the default index backend. Keep the existing TF-IDF backend available as a recovery mode.

### Local generation and NER

Both options should be enabled only after the model files have been transferred and verified locally:

```dotenv
VAULTRAG_ENABLE_GENERATION=true
VAULTRAG_GENERATION_MODEL=C:/Models/phi-local
VAULTRAG_ENABLE_NER=true
VAULTRAG_NER_MODEL=C:/Models/ner-local
VAULTRAG_MAX_NEW_TOKENS=384
```

Use absolute paths only when the installation process owns those paths. Avoid placing model files inside the repository, the upload directory, or a Git-tracked location.

## Failure modes and recovery

### API starts but the UI says it cannot connect

1. Confirm the process is running with `Invoke-RestMethod http://127.0.0.1:8765/health`.
2. Confirm `.env` has the same port the UI expects.
3. Check that another application is not using the port.
4. Review the terminal for a parser dependency error.
5. Confirm the Tauri CSP and CORS origins have not been changed to a different frontend port.

### A document uploads but no passages are created

The parser returned no readable text. This is common with image-only PDFs, scanned records, and DOCX files whose content is inside unsupported embedded objects. Add an approved local OCR stage rather than sending the document to a hosted OCR service. OCR output must pass through the same indexing and masking policy.

### Search returns no sources

The TF-IDF fallback requires lexical overlap. Try a more concrete phrase from the record, confirm the document appears in `GET /api/documents`, and inspect the chunk metadata under `data/index`. Semantic retrieval should be added when synonym-heavy or multilingual search is a core workflow.

### NER is enabled but queries fail

Confirm the model exists in the local Transformers cache, that its task is token classification, and that the installed Transformers version supports `aggregation_strategy="simple"`. The service intentionally does not download a missing model. Disable NER temporarily for retrieval-only operation while the local model installation is corrected.

### Generation is enabled but the process runs out of memory

Disable generation, reduce `VAULTRAG_MAX_NEW_TOKENS`, use a smaller quantized model, or configure an approved accelerator. Never solve memory pressure by sending prompts to a remote provider unless the data governance policy explicitly permits that change.

### Index metadata is damaged

Stop the API, copy `data/index` for incident analysis, and restore the last known-good backup. If no backup exists, delete the index metadata and re-ingest from the source files. The source files remain separate from the index so this recovery path does not require document re-collection.

## Test strategy

The tests are intentionally layered:

| Test area | What it protects | Location |
| --- | --- | --- |
| Masking determinism | Same source value maps to the same token | `tests/test_core.py` |
| Rule precedence | Specific identifiers beat broad phone matching | `tests/test_privacy_and_audit.py` |
| NER integration | External spans use the shared replacement policy | `tests/test_privacy_and_audit.py` |
| Audit redaction | Operational logs cannot contain a raw email | `tests/test_privacy_and_audit.py` |
| Chunking | Large records produce multiple stable chunks | `tests/test_core.py` |
| Index persistence | Metadata survives process recreation | `tests/test_retrieval.py` |
| Empty state | New installations answer safely | `tests/test_retrieval.py` |
| Frontend build | TypeScript and Vite integration | `npm run build` |

When adding a detector, test at least one positive, one near miss, one overlapping value, one repeated value, and one value with punctuation. When changing the generator, test that raw email, phone, and medical identifiers do not appear in the prompt assembled by the adapter. A future implementation should expose a prompt-capture fake for that test instead of loading a real model.

## Development workflow

### Backend-only iteration

```powershell
C:/Python314/python.exe -m compileall backend tests
C:/Python314/python.exe -m pytest -q
```

For a small smoke check without the test runner:

```powershell
C:/Python314/python.exe -c "from backend.masking import mask_text; print(mask_text('Call 555-123-4567')[0])"
```

### Frontend-only iteration

```powershell
npm run build
npm run dev
```

The frontend is intentionally plain React rather than a second service. Keeping the API URL in one constant makes the browser and Tauri development modes behave the same way. A later packaged build can replace that constant with a Tauri command or runtime configuration without changing the evidence-desk components.

### Desktop iteration

```powershell
npm run tauri dev
```

The Python API is currently started separately. A production sidecar should be added only after process supervision, shutdown behavior, log routing, virtual-environment packaging, and model-file discovery have been specified. Starting a detached Python process from an arbitrary UI button is not sufficient for a secure desktop distribution.

## Release checklist

Before a release is used with sensitive records, verify all of the following:

- [ ] The target machine has full-disk encryption and a supported OS patch level.
- [ ] The application binds only to loopback unless a reviewed service deployment says otherwise.
- [ ] `.env`, uploads, index files, logs, and model caches are excluded from source control and backups according to policy.
- [ ] The exact Python, Node, Rust, and model versions are recorded.
- [ ] Dependencies are locked, scanned, and reviewed for license and supply-chain risk.
- [ ] Model files are obtained from approved sources and checksummed.
- [ ] Regex and NER masking are tested against representative synthetic records.
- [ ] Raw values cannot appear in audit logs, UI responses, exception messages, or generated prompts.
- [ ] The generator is tested for unsupported questions, prompt injection inside documents, and fabricated citations.
- [ ] Backups are encrypted and restore-tested.
- [ ] Document deletion behavior is documented for the host filesystem.
- [ ] The incident response owner knows how to stop the API, preserve logs, revoke access, and rotate local salts if needed.
- [ ] A human reviewer signs off before answers are used in a legal or medical workflow.

## Data handling recommendations

Use synthetic fixtures for development. Do not commit real case files, patient data, screenshots containing identifiers, copied production logs, or model caches. Keep a small redaction corpus in an access-controlled test fixture outside Git when production evaluation is required.

For shared workstations, create separate operating-system accounts and separate VaultRAG data roots. For a team, do not treat the local application as a multi-user server unless authentication, authorization, encrypted storage, tenant separation, and audit ownership are implemented. The current design assumes one trusted operator on one trusted device.

## Future milestones

### Milestone 1: current foundation

- Local upload and extraction.
- Deterministic regex masking.
- Optional local NER adapter.
- Inspectable local TF-IDF retrieval.
- Retrieval-only generator contract.
- Tauri wrapper and React evidence desk.
- Redacted operational events.

### Milestone 2: semantic retrieval

- Sentence-transformer embedding provider.
- FAISS persistence with atomic generation directories.
- Index rebuild progress and cancellation.
- Evaluation corpus and recall-at-k metrics.
- Hybrid lexical plus semantic ranking.

### Milestone 3: safe local generation

- Unsloth/Transformers model loader with device selection.
- Prompt budget accounting.
- Structured citations tied to source chunk IDs.
- Model health and unload endpoints.
- Prompt-injection resistance tests.
- Answer confidence and insufficient-evidence state.

### Milestone 4: production hardening

- Encrypted document and index storage.
- OS keychain integration for salts and encryption keys.
- Signed Tauri installers and reproducible build notes.
- Managed Python sidecar lifecycle.
- Role-aware local access control.
- Secure deletion and retention policies.
- Organization-specific audit and compliance review.

The project is intentionally explicit about these milestones. A local UI plus a downloaded model is not automatically a privacy-preserving production system; the surrounding storage, process, update, and human-review controls matter just as much as the prompt.
