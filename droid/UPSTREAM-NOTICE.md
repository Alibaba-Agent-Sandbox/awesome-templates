# Factory Droid distribution

This template installs the original official `@factory/cli@0.241.1` and its
`@factory/cli-linux-x64@0.241.1` compiled distribution from the public npm registry.
The complete dependency/integrity lock is retained in `package-lock.json` and
the actual native binary SHA256 is checked at build and execution.

Official package metadata declares `UNLICENSED`; this is proprietary upstream
software governed by its upstream terms. The template wrapper's Apache-2.0
license does not relicense Factory software. No native binary is committed here.
The package's repository metadata does not prove public source availability.

[Official BYOK documentation](https://docs.factory.com/model-independence/byok)
describes local custom models. Contract qualification uses the actual fixed
0.241.1 binary, rather than assuming current documentation matches every release.
