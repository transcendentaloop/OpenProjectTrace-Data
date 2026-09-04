# Publication operations

## Authority boundary

This repository owns only the public snapshot bytes and the public `data`
branch. Private inputs, selection/evaluation policy, and processing source stay
with the `open-project-trace` owner and are injected into GitHub Actions through
scoped repository secrets. Forks cannot run the private publication path.

`data` is a mutable latest-snapshot pointer, not an immutable name. A consumer
that needs reproducibility must retain the resolved data commit and Git blob
IDs. A workflow run, a source commit on `main`, the current `data` ref, and the
`generated_at` value inside `meta.json` are separate evidence.

## Read-only verification and freshness

Refresh the remote-tracking ref, then run the local verifier:

```bash
git fetch origin data
python3 scripts/verify-publication.py
git ls-remote --exit-code origin refs/heads/data
```

The verifier requires the five public files, parses every JSON blob, checks the
metadata schema and candidate count, and treats `meta.json.generated_at` older
than 48 hours as stale. It does not run private automation or prove that the
selection/evaluation policy itself is correct.

The remote `data` SHA must equal the fetched ref used by the verifier. If they
differ, fetch and verify again; do not call a stale local ref current.

## Publication and failure handling

The only declared maintainer release entry is manual dispatch of
`.github/workflows/refresh.yml` with a reviewed update mode. Scheduled and
manual runs invoke private automation. Do not reproduce that implementation or
its secrets in this public repository.

Before dispatch, record the current public data SHA and successful local
verification summary. After dispatch:

1. inspect the exact GitHub Actions run conclusion and head SHA;
2. fetch `origin/data` again;
3. rerun `scripts/verify-publication.py`;
4. compare the remote SHA, local remote-tracking SHA, and reported snapshot SHA;
5. report freshness from `meta.json`, not from the workflow start time alone.

For routine triage, the two workflow files use separate
`github-actions-run-summary/v1` sources through the shared `agentctl diagnose`
path. The adapter reads one bounded page of orchestration metadata only and
does not access jobs, annotations, logs, artifacts, step output, actors, URLs,
or private automation content. It requires explicit remote/log opt-in, the
confirmed diagnostic plan digest, and the exact
`github:transcendentaloop/OpenProjectTrace-Data:actions-read` credential scope.
Its receipt keeps only aggregate states, freshness, redaction statistics, and a
digest over allowlisted metadata.

Prepare the immutable diagnostic plan first:

```bash
agentctl diagnose plan open-project-trace-data \
  --include-logs --allow-remote --json > /tmp/open-project-trace-data-plan.json
```

Inspect the exact repository, workflow files, bounds, credential scope, and
`planDigest`. A remote summary may run only by passing that saved plan and the
same digest to `agentctl diagnose run` together with `--include-logs` and
`--allow-remote`. Planning never resolves credentials or contacts GitHub.

An Actions summary is not test, artifact, deployment, data-publication, or
runtime-health proof. If deeper investigation needs the GitHub UI or raw logs,
the repository owner must use their human session and retain only a sanitized
run locator, conclusion, relevant SHA, checked layers, and residual
uncertainty; raw remote content does not enter task evidence.

## Rollback and recovery limits

There is no repository-owned backup schedule or retained rollback index for
previous generated datasets. GitHub may retain objects, but a force-updated
branch is not a backup guarantee. The private automation owner must preserve or
recreate a prior validated snapshot before a destructive publication change.

Rollback means republishing an exact previously validated dataset through the
owner workflow, then repeating remote-ref, JSON, freshness, and consumer
visibility checks. Never manually copy private inputs into this repository or
force-push an unverified local tree as a shortcut.

For handoff, record the main commit, workflow/run locator, update mode, previous
and resulting data SHAs, `generated_at`, verifier output, and any unavailable
private-policy layer. Credentials and private source data never enter the
handoff record.
