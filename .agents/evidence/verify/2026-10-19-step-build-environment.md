# Verification: explicit build environment for platform RUN steps

Date: 2026-10-19
Result: PARTIAL

Scoped follow-up to the platform-step materializer/driver, regression and bilingual
guides. Runtime product sources and their pins remain unchanged.

An actual OpenClaw step build used base Node20 during npm install despite an earlier
native ENV PATH selecting pinned Node24. Its package-manager guard correctly rejected
the install. Native ENV configuration is therefore insufficient to reproduce Docker
RUN environment in this provider path. The failure remains a failure.

The adapter now explicitly exports declared build variables and workdir before RUN,
resolves runtime ENV references using a verified provider base PATH rather than local
controller PATH, and retains the final non-root user. A different base tag requires
an explicitly verified base-path input. A real owned Express base probe read the PATH
and independently confirmed its exact sandbox absent after deletion; see
[probe receipt](2026-10-19-base-path.json). An earlier probe controller attribute error
was reconciled by its exact unique metadata tag: one owned sandbox killed, then no
matching tag on independent paginated inventory. No unknown resource was deleted.

A real local fake-tool regression demonstrates that RUN finds a declared PATH tool
even without native ENV propagation, and confirms runtime PATH contains no unexpanded
reference. Combined spec/materializer/docs/cleanup checks pass60 tests and48 subtests;
all24 existing profiles still fit the wire budget. Real corrected OpenClaw and other
remaining catalog builds are in progress; this record is not their cloud pass.

## Large-asset follow-up

Independent build-network measurement retrieved8MiB code-server/Rust ranges in
385.267/398.173seconds, versus0.737/1.607seconds for Go/Hermes source. The
[build probe](2026-10-19-step-asset-network.json) completed real CLI/SDK report
retrieval and independent owned cleanup. It is a partial download diagnostic,
not a template acceptance receipt. A runtime base probe also completed and
independently cleaned; its64KiB samples are recorded separately.

The earlier306.777-second RUN stream deadline failure does not establish a
universal300-second RUN execution limit: this successful diagnostic RUN ran
longer. Separate installation phases remain useful, but large asset transport
is a verified remaining constraint. Whole-build timeouts are not successes.

An optional owned OSS public-cache probe created a private bucket, but object
public access was denied403. The object/bucket were deleted and independent
absence confirmed; no account policy was changed. Use of existing public CI
image export plus private local registry transfer is under separate review.
