![test](https://github.com/jdz-green/evidence-scout/actions/workflows/test.yml/badge.svg)

# Evidence Scout — a small OpenMinion agent

Turns one URL into a dated evidence note: two quoted facts with their exact numbers, plus one line saying
what they establish. Built with the **OpenMinion 0.1 Python SDK** for Cortensor Hackathon #5.

Why this workflow: a forecasting market pays for a checkable fact with a date, not for a summary. The
deterministic part (HTTP, HTML stripping, truncation) is a registered tool; the language part (which
sentences carry the number, and what they do not say) is the model's job. An 8B local model can do the
second and should not be asked to imitate the first.

## A note file, not just a chat reply

```console
$ env -u NO_PROXY -u no_proxy python agent.py <url> --note demo/zurich-note.txt
```

The note file is shaped like the evidence notes used for Delphi: the URL, the retrieval date, the two
quoted facts, and the caveat. The agent pins `session_id="evidence-scout"` because the default session
carries brain state that makes later runs refuse (see BUGS.md #6).

## Demo

A 29-second walkthrough: https://youtu.be/FlpedyFJ7Nw

## Run

```console
$ env -u NO_PROXY -u no_proxy /proj/money/.venv/bin/python agent.py \
    "https://www.bern.ch/themen/stadt-recht-und-politik/abstimmungen-und-wahlen/abstimmungen/aktuelleabstimmungen/stimmbeteiligung"
openminion: The page states:
1. "Bis am Donnerstagabend, 26. November 2026, sind 33'219 briefliche Stimmabgaben eingegangen."
   (33,219 postal votes counted by November 26, 2026).
2. "Das entspricht einer Stimmbeteiligung von 36,8 Prozent. Die Stadt Bern hat 90'190
   stimmberechtigte Personen." (36.8% turnout among 90,190 eligible voters).
These establish the current voter participation rate and total eligible voters in Bern as of
November 26, 2026.
```

`env -u NO_PROXY -u no_proxy` is not cosmetic: without it every provider call fails before it is made.
See `BUGS.md`.

## A gate before the model

`agent.py` refuses to call the model when the fetched text contains no digit: that page cannot carry a
dated or numbered fact, so the honest output is `NO CHECKABLE FACT`, not a summary. This also removes the
brain layer's most common refusal (see BUGS.md #5), which is not deterministic.

## Two runs, two pages

| page | what the agent returned |
|---|---|
| bern.ch interim turnout | 33,219 postal ballots by 26 Nov 2026 = 36.8% of 90,190 voters |
| stadt-zuerich.ch interim turnout | 42.3% postal share, final turnout only after the count |

The second run also shows the model's limit: it attached "as of 29 November" (the vote date) to the 42.3%
figure, which the page does not say. That is the kind of error a human has to catch before the note is
sent, and it is why the agent's output is a draft, not a submission.

## OpenMinion building blocks exercised

| Block | How |
|---|---|
| tools | one custom tool, `fetch_text`, decorated with `@tool(min_scope="READ_ONLY", idempotent=True)` |
| action policy | the same tool without `min_scope` is classified `WRITE_SAFE` and blocks the turn behind a confirmation prompt; the annotation is what makes an unattended run possible |
| providers | `ollama` with `qwen3:8b`, configured through `openminion config init` |
| sessions | the run is one session turn; `Agent.run` returns `AgentRunResult` with `.text` |
| brain | the default planning layer runs before the model; see `BUGS.md` for how it changes small-model behaviour |

## What worked, what broke

Worked: installation, config, provider wiring, custom tools, the action-policy annotation, and a real
model-backed run end to end.

Broke: three things, written up in `BUGS.md` —
1. a `no_proxy` entry (`::1`) is turned into the httpx mount `all://*[::1]`, which fails at URL
   construction and is reported as a *provider* error even though no provider was called;
2. session ids are bound to the process that created them (`api-user` vs `cli-user`), and the error does
   not say how to reclaim one;
3. a custom tool with no `min_scope` is treated as a local write and blocks unattended runs — reasonable
   policy, but the failure mode is a prompt that a headless caller cannot answer, and the message does not
   name the annotation that fixes it.

## Files

- `agent.py` — the agent and its one tool
- `BUGS.md` — the three findings above, with reproductions
- `demo/` — captured runs
