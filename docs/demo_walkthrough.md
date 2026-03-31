# Demo Walkthrough

## How To Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Sample Cases

- `case_001`: clean MRI lumbar spine packet that should land in `READY`
- `case_002`: outpatient PT request with missing supporting information that should land in `MISSING_INFO`
- `case_003`: urgent CT abdomen with contrast that should land in `ESCALATE_TO_HUMAN`

## What Each Sample Should Show

- `case_001`: all required checks pass, no missing items appear, and the reviewer approves the `READY` handoff
- `case_002`: multiple missing items appear in validation and the reviewer confirms the `MISSING_INFO` route
- `case_003`: the packet validates as complete but escalation logic triggers `ESCALATE_TO_HUMAN` because of urgency and payer rules

## Where Traces And Logs Appear

- automated workflow trace table in the right-side panel after running the workflow
- final workflow trace table after the human-in-the-loop decision is applied
- `trace_log` inside each output JSON in `outputs/`

## Suggested Demo Flow

1. Open the app and show the selected mock case input.
2. Click `Run automated readiness review`.
3. Point out the validation table, automated status, and workflow trace.
4. Use the human-in-the-loop controls to confirm or override the route.
5. Show the final handoff summary JSON and summary paragraph.

## Suggested Screenshots

- selected case input JSON
- automated validation plus workflow trace for `case_002`
- final handoff summary for `case_003`

Save screenshots in:

- [assets/screenshots](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots)
- [app_home.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/app_home.png)
- [validation_trace_case_002.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/validation_trace_case_002.png)
- [final_handoff_case_003.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/final_handoff_case_003.png)
