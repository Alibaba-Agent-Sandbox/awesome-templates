# Upstream software and notices

This Apache-2.0 template wrapper installs the unchanged original Chrome for
Testing145.0.7632.6 Linuxx64 archive from the reviewed official Playwright1.58.0
installer URL. [browser.json](browser.json) retains the controller-measured
archive digest and its basis; this is not an upstream-published checksum.
Original native browser files and notices remain under `/opt/chrome-browser`.
The wrapper license does not relicense native browser components.

Debian13 distributes Xvfb/Openbox/x11vnc/TigerVNC tools and noVNC. Keep their
installed `/usr/share/doc/<package>/copyright` and common-license files. noVNC1.6
contains MPL-2.0 code, BSD-2-clause HTML/styles, OFL-1.1 fonts, CC-BY-SA-3.0 images,
and Expat/Zlib vendor code as documented by Debian's unmodified copyright file.
Native VNC/X server components retain their own licenses and notices.

The Chromium system-library list is taken from the original pinned
[Playwright source](https://github.com/microsoft/playwright/blob/961381ec73a9fa2661d92504eab1a6bd6eaffc75/packages/playwright-core/src/server/registry/nativeDeps.ts).
No Playwright agent or alternative browser implementation is substituted; the
template relays the real Chrome DevTools and authenticated RFB protocols.
