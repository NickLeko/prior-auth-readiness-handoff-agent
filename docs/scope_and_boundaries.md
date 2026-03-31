# Scope And Boundaries

## In Scope

- mock prior auth cases only
- deterministic document and field readiness checks
- small LangGraph workflow orchestration
- automated status classification
- explicit human-in-the-loop checkpoint
- final administrative handoff summary
- visible workflow trace logging

## Out Of Scope

- diagnosis or treatment guidance
- medical necessity adjudication
- payer API integrations
- EHR integrations
- authentication
- databases
- background job infrastructure
- production deployment setup
- multi-agent orchestration

## Why The Workflow Is Administrative Only

The agent checks whether a mock packet is complete enough for prior auth handoff. It does not interpret symptoms, make clinical recommendations, or replace utilization management staff. The value is workflow completeness and routing clarity, not medical reasoning.

## Why Human Review Exists

Healthcare administrative workflows still need accountable review. This prototype keeps the human-in-the-loop checkpoint explicit so a reviewer can confirm a `READY` handoff, validate a `MISSING_INFO` route, or force `ESCALATE_TO_HUMAN` when the automated path is not sufficient.

## Limitations

- uses mock data only
- uses simplified rules instead of real payer policy logic
- does not persist case history
- does not integrate with external systems
- does not claim coverage determination accuracy

## Non-Production Disclaimer

This repository is a portfolio prototype for demonstrating safe, narrow healthcare workflow AI concepts. It is not production software and should not be used for real patient, payer, or clinical operations.
