# New_Evaluation

Simple manual evaluation app for 12 movement videos.

## Folder structure

- `motion/` -> place video files:
  - `Movement1.mp4` ... `Movement12.mp4`
- `web/` -> instruction page, evaluation page, and results page
- `data/submissions.json` -> saved submissions
- `config.json` -> movement mapping + 15 answer options
- `server.py` -> backend API + static file server

## Run

From `New_Evaluation/`:

```bash
python server.py
```

Open:

- `http://localhost:8010/` -> instruction page for participants
- `http://localhost:8010/evaluate.html` -> direct evaluation page

Result page (for evaluator/researcher only):

- `http://localhost:8010/results.html`

## Metrics shown in Results page

- Overall Accuracy
- Accuracy per Movement
- Mean Overall Confidence
- Confidence per Movement
- Rate of Not Identifiable / Not Sure
- Confusion Matrix
