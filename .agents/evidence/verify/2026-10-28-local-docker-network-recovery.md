# Local Docker network recovery during native provider acceptance

Result: PARTIAL (owned cleanup/network restored; fresh application run pending)

Date:2026-10-27–28. Original immutable combined template input4c4d1a700b76135333d8a85f32008f59745cc926,
CLI0.5.7/client-server0.4.0a6 and official OpenSandbox/execd1.1.1.

A capacity experiment started a second Docker daemon with separate VFS data/exec
roots, no default bridge and firewall/forwarding management disabled. Metadata
storage separation did NOT isolate shared host networking: the primary docker0
bridge was found absent. The owned registry answered internally, but both its
host-mapped and direct bridge endpoints timed out; IPv4 forwarding remained1 and
its NAT port rule existed. Do not call this an application/runtime source defect.

Actual AppWorld OpenSandbox run during that outage:9 native PASS/1 FAIL with
ServerAPIError, no full documentation pass. The sandbox was independently absent;
two owned prepared-image references were retained after registry ReadTimeout.
Original failure remains FAIL; no cleanup-only success establishes business use.
The queried default-daemon OOM event window returned0 events, which is not a
claim that no possible memory issue ever occurred.

Recovery: only the task registry container was active, with no other workload.
Restarted the primary Docker service to restore its bridge. Its auto-remove
registry container was recreated from the same pinned image and original owned
storage, delete setting and loopback port binding. Actual registry /v2/ returns200,
and outbound HTTPS from that container succeeds. Exact journal-scoped sandbox and
all image references are independently absent; reconciliation is SHA-bound to the
original failed receipt and performs0 new business/model calls. No journal/raw
failure is rewritten. Original20/24 batch summary is retained.

Fresh same-source, same flash-model/direct-endpoint AppWorld acceptance is queued,
followed by the four previously unrun targets. Earlier completed workflows are
not repeated. New summary-recovered.json explicitly selects that fresh attempt;
the original network failure remains separately linked. Original Muse/Tau model
and scoring failures are also preserved for their separate known max profiles.

Capacity experiment remains incomplete: direct workspace VFS unpack rejects an
original absolute symlink (invalid argument). An owned64MiB ext4 loop file supports
that symlink and was successfully formatted/attached/mounted/unmounted/detached.
The two exact Debian tooling archives were extracted into task-only storage, with
no system package installation. No native interpreter instance was run or granted
qualification. Further Docker storage experiments must wait until primary active
workloads finish and use one daemon at a time or explicitly owned networking;
separate data directories alone do not make parallel daemons safe here.
