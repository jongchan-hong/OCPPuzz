# Artifact Status

## Artifact Name

OCPPuzz: Spec-Driven Fuzzing of CSMS with LLM

---

## Requested Badges

- Artifacts Available
- Artifacts Evaluated – Functional
- Artifacts Evaluated – Reusable

---

## Rationale

### Artifacts Available

The artifact has been made publicly available through a persistent archival repository with a DOI.

The repository contains:
- the complete source code of OCPPuzz,
- scripts for message direction extraction,
- rule extraction and scenario extraction modules,
- fuzzing and validation components,
- experiment and evaluation scripts,
- datasets and collected intermediate artifacts,
- reproduction instructions and documentation.

The archived artifact corresponds to the exact version used for the experiments reported in the paper.

---

### Artifacts Evaluated – Functional

The artifact includes all necessary components to reproduce the main functionality and experimental workflow presented in the paper.

Specifically, the artifact supports:
- extraction of message directions from the OCPP specification,
- extraction of structural and semantic validation rules,
- extraction of protocol scenarios using LLM-assisted processing,
- generation of valid and invalid mutation payloads,
- automated fuzzing of CSMS implementations,
- validation and collection of mismatch responses,
- reproduction of the experimental findings reported in the paper.

The artifact has been tested in a clean Docker-based environment and includes installation and execution instructions.

The evaluation pipeline can be executed using the provided scripts and Docker Compose configurations.

---

### Artifacts Evaluated – Reusable

The artifact is designed and documented to facilitate reuse and extension by other researchers and practitioners.

The artifact provides:
- modularized components for collectors, generators, validators, and test controllers,
- configurable target CSMS selection,
- reusable fuzzing and mutation modules,
- structured datasets and extracted protocol knowledge,
- automated execution scripts,
- Docker-based deployment environments,
- dependency specifications,
- detailed documentation and usage examples.

The framework can be extended to support additional OCPP versions and other protocol-testing scenarios.

The artifact is intended to support future research on:
- specification-driven fuzzing,
- protocol validation,
- LLM-assisted software testing,
- EV charging infrastructure security,
- automated robustness testing of stateful systems.

---

## Reproducible Results

The artifact supports reproduction of the following results presented in the paper:

- message direction extraction accuracy,
- rule extraction statistics,
- scenario extraction results,
- mismatch statistics for valid and invalid test cases,
- validation failure categories,
- coverage evaluation results,
- representative protocol validation failures and discovered vulnerabilities.

In particular, the artifact reproduces the evaluation results corresponding to:
- Table 2 (Mismatch response rates),
- Table 3 (Missing validations in OCPP implementations),
- Figure 8 (Coverage comparison of testing strategies).

---

## Expected Environment

### Recommended Environment

- Ubuntu 22.04 LTS or newer
- Docker and Docker Compose
- Python 3.13+
- ODBC Driver 17 for SQL Server

### Recommended Hardware

- 16 GB RAM or higher
- Multi-core CPU recommended

### External Requirements

Some collector modules require access to LLM APIs.

The following scripts require an OpenAI API key:
- `message_direction_collector.py`
- `rule_collector.py`
- `scenario_collector.py`

---

## Included Components

The artifact repository includes:

- OCPPuzz framework source code
- test controller modules
- validator modules
- rule and scenario extraction modules
- mutation and payload generation modules
- Docker deployment configurations
- CSMS target configurations
- datasets and collected protocol knowledge
- experiment scripts
- reproduction scripts
- documentation and usage instructions

---

## License

The artifact is distributed under the license included in the repository LICENSE file.
