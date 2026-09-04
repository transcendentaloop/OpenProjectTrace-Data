# OpenProjectTrace Data

Public, machine-readable OpenProjectTrace snapshots.

The `data` branch contains the current published dataset. This repository does
not contain product source code, private inputs, credentials, deployment
configuration, or data-processing implementation.

The scheduled workflow only invokes private automation and publishes data that
has passed its private validation policy. Forks do not receive the required
repository secrets.

Both public workflows check out the private automation at the exact immutable
commit recorded in `.github/automation-source.json`. Update that commit only
after resolving an authoritative owner-repository Git ref and confirming its
root `action.yml`; never replace it with a branch, tag, or guessed SHA. Run
`python3 scripts/verify-workflow-contract.py` to check this contract without
accessing credentials, private source, or GitHub Actions.
