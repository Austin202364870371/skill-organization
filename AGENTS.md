# Intrebid cluster constraints

- Run all formal preprocessing, inference, evaluation, and model serving through Slurm.
- Use login nodes only for editing, inspection, submission, monitoring, and brief tests.
- Use a project-local environment at `./env`; never modify the shared base environment, CUDA, drivers, shell startup files, or system directories.
- Use `fast` for short smoke tests (at most 6 hours), `cpu` for CPU-only work, `normal` for routine GPU runs, and `long` only when a run genuinely needs more than 3 days.
- Request two L40 GPUs on either GPU2 or GPU3 for the local Qwen model and use tensor parallel size 2. Do not keep an allocation or model server idle.
- Test on one task before pilots and pilots before formal runs. Do not flood the queue with near-duplicate jobs.
- Keep caches, AppWorld data, logs, outputs, and model weights inside this project. Do not duplicate existing large weights.
- Never use `sudo`, change public datasets, expose a service publicly, or write secrets to tracked files.
- Human-review generated commands before installation, download, submission, or deletion.

