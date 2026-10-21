# Original Prime Agent distribution

The authored Agent Sandbox wrapper is Apache-2.0. Original Prime Agent is MIT;
its complete release LICENSE, PHOTON-LICENSE.md and original runtime/assets remain
installed in /opt/prime-agent. The wrapper does not relicense third-party assets.

Official stablev0.10.0 corresponds to source tag
763094e1b6a7c17450ee8399b06cda1853847ca5. This is public tag correspondence,
not a reproducible-native-build claim. Both original Linuxx64 archive and native
executable SHA256 are published in that release's manifest.json and checked.
No floating installer script is executed. Original sidecars, including the
CPython runtime source0.1.0/protocol3, remain unmodified.

The native tool is named ipython; this release's packaged implementation is a
CPython REPL. No unrelated IPython/ipykernel replacement is substituted. Kernel
imports use its supported fixed interpreter override plus original sidecar source.
Python packages are separately hash-locked. Native optional catalog/skills,
subscription, recursive-agent, research and daemon features are not qualified by
this bounded coding slice. Native code runs with the disposable sandbox's user
permissions; its process/kernel lifecycle is not an additional OS sandbox.
