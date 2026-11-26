# OpenMinion 0.1.24 — what broke on first contact

Environment: Arch Linux, Python 3.14, local Ollama (`qwen3:8b`), OpenMinion 0.1.24 from PyPI.

## 1. `NO_PROXY` containing `::1` breaks every provider call

**Symptom.** Every provider (ollama and openai-compatible alike) failed before any request:

```
ProviderError: The configured model provider failed before it could return a decision
(InvalidURL: Invalid port: ':1]')
```

**Root cause.** OpenMinion builds httpx proxy mounts from the proxy environment. With
`no_proxy=localhost,127.0.0.1,::1,...`, it constructs the mount pattern

```
all://*[::1]
```

which httpx rejects while parsing (`Invalid port: ':1]'`). The failure happens at `httpx.URL(...)`
construction, *before* any provider-specific code runs, which is why switching provider or `base_url`
changes nothing and why the error message never mentions the proxy.

**Workaround.** Unset `NO_PROXY` and `no_proxy` for the process:

```console
$ env -u NO_PROXY -u no_proxy python agent.py
```

**Suggestion.** Treat `no_proxy` entries as host patterns (`::1` → `[::1]` handling for IPv6), or skip
`no_proxy` when building mounts, and surface the offending pattern in the error message.

## 2. A stale session id is bound to the process that created it

**Symptom.**

```
ValueError: Session 'cli-run' belongs to target 'api-user', not 'cli-user'
```

After a run through the daemon, the in-process runtime refuses the same session id, and after restarting
the daemon, fresh session names still fail from the CLI.

**Workaround.** Use `--session <new-name>` for in-process runs, or clear the session from the store.

**Suggestion.** Either namespace sessions by caller, or make the error say which process owns the session
and how to reclaim it.

## 3. `--runtime-source inproc` and the daemon disagree about who the caller is

Same origin as #2: the CLI speaks as `cli-user`, the daemon as `api-user`, and the identity check rejects
the hand-off. It is not obvious from `openminion run --help` that these two modes have different session
ownership.

## 4. `--simulate` on `gnokey`-style flag parsing (unrelated, Gno)

Not OpenMinion, but recorded while working in the same session: Gno's `addpkg` fee must be denominated in
`ugnot`, and the package needs ~20.7M gas; a `gnot` fee fails as "insufficient funds" against a zero
`gnot` balance even when the account holds 100 GNOT.
