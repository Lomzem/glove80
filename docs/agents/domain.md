# Domain docs

This repo uses a single-context layout: `GLOSSARY.md` at the repo root and ADRs under `docs/adr/`.

## Before exploring

Read `GLOSSARY.md` and any ADRs under `docs/adr/` relevant to the area being explored.

If these files do not exist, proceed silently. The `domain-modeling` skill creates them lazily when terms or decisions are resolved.

## Use the glossary's vocabulary

When naming a domain concept in an issue, refactor proposal, hypothesis, or test, use the term defined in `GLOSSARY.md`.

If a needed concept is missing, reconsider whether the project uses it; note real gaps for `domain-modeling`.

## Flag ADR conflicts

If a proposal contradicts an existing ADR, identify the ADR and explain why the decision should be revisited.
