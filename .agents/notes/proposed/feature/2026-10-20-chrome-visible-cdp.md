# Decision: native visible Chrome with CDP and noVNC on Express

Status: proposed

## Problem

[Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61)
requires both DevTools and an actual visible Chrome desktop so a human can watch
automation. Existing headless browser and OSWorld task wrappers do not expose
this combined CDP/noVNC surface. Memory/shm behavior needs actual Express proof.

## Decision

Pin the already reviewed Playwright1.58 Chromium145.0.7632.6 native asset and
Debian13 Xvfb/Openbox/x11vnc/noVNC. Run a genuine headed browser in a private
non-root desktop, expose transparent CDP9222 and noVNC6080 relays, and preserve
native VNC password authentication. Use private HOME/profile/Xauthority, bounded
original protocols, owned group/nonce/pidfd lifecycle and independent cleanup.
No Docker daemon, KVM, GPU or model dependency. Experimental until actual gates.

## API Design

Planned scalar version/setup/start/status/open/screenshot/stop and internal smoke.
Start returns ports and a generated ephemeral VNC password only to the caller.
No raw secret enters argv, public evidence or native browser environment. Desktop
PNG comes from the actual authenticated VNC framebuffer; CDP is the original
Chrome protocol through a bounded local relay, not a substitute browser.

## Alternatives considered

Headless-only Chromium does not meet visible VNC scope. A canned screenshot or
HTML fake is rejected. A privileged desktop or provider VM is unnecessary for
this application slice. A floating OpenSandbox image is not reproducible. Native
CDP Host handling requires a transparent local relay for forwarded gateway hosts.

## Dependencies

Reviewed Playwright/browser asset, exact Debian desktop/VNC packages and an
isolated hash-locked Python protocol runtime. Preserve all upstream notices,
including noVNC/native browser and VNC server licenses. Common immutable server
and actual native CLI/paired Python client for real Express acceptance.

## Test Strategy

Authored validation/path/process/protocol bounds regressions and strict/bilingual
docs. Actual L1 headed native smoke. SDK-created canonical steps, official READY,
independent external CDP navigation/click, actual noVNC static UI, password-authenticated
WebSocket RFB framebuffer, visible color change matching native DOM, independently
downloaded PNG and owned artifact/session/ports/display/private-state absence.
Repeat lifecycle in a2vCPU/2048MiB/64MiB-shm target and record measured facts.
Mocks/source-only skips cannot qualify this surface.

## Acceptance criteria

Complete standalone source/catalog/design/bilingual docs/records. Required local,
image, SDK-created Express/native CDP and VNC checks pass with exact provenance
and independently confirmed owned cleanup. Normal current-head review/CI/merge
before Issue61 closure. Actual feasibility remains pending until measured.
