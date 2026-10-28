# LAW-U rule engine and versioned rule graph

Code and data accompanying *A semi-structured consultation agent for temporally versioned rules: information-gain fact
elicitation compared with LLM chat and Graph RAG on Thai sexual-offence law* (Results in Engineering).

This release contains the deterministic part of LAW-U only:

- `data/01_STATUTES/.../section_versions.json` — the official text of all 27 enactments of Sections 276–279 of the Thai
  Criminal Code with their in-force intervals (public law).
- `data/03_RULES/VERSIONED_RULES.json`, `data/03_RULES/graph/data/nodes.jsonl` — the rule graph: one AND/OR syntax tree per
  paragraph of each enactment, with typed element nodes (age thresholds, operators).
- `data/03_RULES/ALL23_DEFINITIONS.json` — the 23-element catalogue.
- `lawu/engine/law.py` — version (era) resolution, version-specific definitions of intercourse and indecent act, and
  three-valued (Kleene) evaluation of every paragraph.
- `lawu/engine/slots.py` — the four-state ledger (supported / denied / unknown / conflict) and the fixed Thai question
  templates (Supplementary File S1, Table T1).
- `lawu/engine/jev_rules.py` — the outcome distribution by Shannon expansion over open elements and version weights,
  statutory precedence, entropy and expected information gain.
- `lawu/engine/policy.py` — the inquiry policies (EIG, fixed order, random) and conflict confirmation.
- `example.py` — a synthetic consultation state, its outcome distribution and the next question.

Not included: court decisions, extracted facts, simulated users, dialogue transcripts, prompts to language models
(published in Supplementary File S1) and the language-model adapters.

## Run

Python 3.10 or later, no third-party packages.

```
python3 example.py
```

## Licence

Code: MIT (see `LICENSE`). Rule graph and element catalogue (`data/03_RULES/`): CC BY 4.0. The statutory text in
`data/01_STATUTES/` is Thai public law.

## Citation

If you use this code or the rule graph, please cite the article above.
