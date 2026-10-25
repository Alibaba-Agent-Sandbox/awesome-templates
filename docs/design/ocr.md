# OCR

## Purpose

Deliver [Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57)'s CPU image-to-text task through the official Tesseract CLI on Alibaba Express. English PNG/JPEG input and independently retrievable text/word-coordinate artifacts need no model credentials.

## Capabilities

One image per call, English recognition, EXIF orientation normalization, bounded private TXT/TSV results and actual offline smoke. No GPU, Docker, privileges, PDF, archive extraction, batch, language auto-download or handwriting guarantee. Existing server shell/files/code/ports capabilities remain; OCR containment applies to the named OCR interface.

## Exposed API

- `ocr_version()` → actual string `tesseract 5.5.0`; argv `tesseract --version`, 5-second deadline.
- `ocr_setup_check()` → availability, pinned/actual version, Pillow version and English language; no input processed.
- `ocr(image_path: str)` → text, word count, normalized width/height, language, engine version, private artifact directory/TXT/TSV paths and SHA256 hashes. Required path stays within an existing runtime-user-owned WORKSPACE; FD-relative no-follow traversal refuses symlinks, parents and nonregular inputs. Actual engine argv: `tesseract <private-input.png> <private-output-base> --tessdata-dir <fixed-data> -l eng --psm 6 --dpi 300 txt tsv`. All flags are fixed; no shell. Private input is a metadata-free RGB PNG generated after validating one PNG/JPEG, at most 10 MiB encoded / 8192 each side / 16 million pixels. The original is not modified.
- `ocr_smoke()` → `Tesseract image/text/TSV artifacts OK`, only after actual fixture recognition, independently reading both result files, hash checks, five words at confidence >50, then owned cleanup.

No OCR parameter selects an executable, language or external URL. Operators can configure absolute native binary/data paths for diagnostics; these settings are not available through the named API. Original HOME is preserved. Child environment omits cloud/model keys and network proxy settings.

## How to build

[Dockerfile](../../ocr/Dockerfile) keeps the literal Alibaba FROM placeholder and installs the published server package pin. Debian 13 pins Tesseract/libtesseract `5.5.0-1+b1`, English/orientation packs `1:4.1.0-2`, and Leptonica `1.84.1-4`; transitive OS libraries remain repository-resolved, not an entire distribution snapshot. Pillow `11.3.0` uses committed PyPI wheel SHA256 values with `pip download --require-hashes --only-binary=:all:`, then installs only those verified wheels with `pip install --no-index --no-deps`. Duplicating an unhashed command-line requirement beside a hashed requirements file is deliberately avoided. Public source, fixture image and manifest are the only added image files; no secrets are inputs. Package copyright files remain installed.

Generation 2 starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, readiness is `agent-sandbox-server healthcheck --port 9000`. Working directory ownership is explicitly assigned to `user`; runtime is non-root. There is no replacement CMD/ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: none identified for this bounded English CPU slice; actual changed-image verification remains pending.

The 2-vCPU/1024-MB allocation needs no extra capabilities or model/network access during recognition. Full OSWorld, OCR foundation models or extra languages are separate work and are not implied.

## Risks

Native decoding is bounded by encoded bytes and dimensions before pixel allocation, with a private temporary PNG limited to 64 MiB. The native engine uses an isolated Python exec wrapper to set RLIMIT_AS 512 MiB, CPU 30/31 seconds, FSIZE 4 MiB and CORE 0 before exec; this avoids threaded-server preexec_fn. Engine wall deadline is 45 seconds; diagnostic pipes are capped at 1 MiB each, TXT at 1 MiB and TSV at 4 MiB. One lock rejects concurrent OCR work. Pillow decoding occurs in the server process, so the sandbox memory limit remains its outer bound.

Linux WNOWAIT retains the leader identity until owned-group cleanup; both pipes are drained, and success/error/timeout/Python cancellation stop the owned group before reap. Deliberate setsid escapes and abrupt server SIGKILL are outside that Python cleanup guarantee. HTTP disconnection is not cancellation. No private source path, image contents, child argv or raw diagnostics appear in fixed execution errors. Results themselves contain recognized text and returned workspace artifact paths: callers must treat them as sensitive.

Successful result directories are mode 0700, files 0600, unique and retained for retrieval; callers must remove them or destroy the sandbox. Temporary normalized inputs are removed on all managed exits. General authenticated server file/shell APIs remain broader than this OCR path boundary. Dependency pins do not freeze transitive Debian OS security libraries. Recognition accuracy for arbitrary images is not guaranteed.

## Test plan

L0: strict checker, real process success/nonzero/timeout/cancellation cleanup with actual descendants and foreign-group preservation, bounded pipes, input type/path/symlink/FIFO/size/pixel/frame rejection, normalization, TSV validation, private artifacts and environment/resource regression, actual authenticated direct/canonical-form server startup. A synthetic fixture executable tests failure/privacy boundaries and is not OCR evidence. OCR_TEST_REAL=1 requires actual Tesseract against original fixture pixels.

L1: actual selected Docker build and non-root no-network `ocr_smoke`; pin diagnostics from actual `ocr_version`/Pillow and confidence/text/TSV checks. Local Docker is unavailable; remote CI is pending. L2: canonical deploy plus express_e2e remains not run. Supplemental changed-image acceptance, when run, must preserve exact image/app/SDK provenance, SDK/HTTP/CLI real OCR and strict owned compute/template/registry cleanup; it does not replace canonical L2. Source HTTP acceptance requires E2E_REQUIRE_OCR=1 and independently creates a random-digit image, downloads fresh TXT/TSV, verifies hashes/words/confidence/bounds and untouched input, then tests blank pixels and cleans owned artifacts. Current source result is 19 passed / 0 failed / 0 skipped. L3 model coding and L4 are not applicable to this keyless OCR task.

Official references: [fixed Tesseract source](https://github.com/tesseract-ocr/tesseract/tree/5.5.0), [fixed CLI manual](https://github.com/tesseract-ocr/tesseract/blob/5.5.0/doc/tesseract.1.asc), [Pillow release metadata](https://pypi.org/pypi/pillow/11.3.0/json), [verification](../../.agents/evidence/verify/2026-10-16-ocr-runtime.md).
