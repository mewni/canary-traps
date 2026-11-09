"""Assemble canary_traps_swarm.ipynb (Experiment 2b, the seeded swarm) from the tested source files."""
import os
import sys
import nbformat as nbf

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src") + os.sep
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebooks", "canary_traps_swarm.ipynb")
DRY = "--dry" in sys.argv


def src(name):
    text = open(SRC + name).read().rstrip() + "\n"
    if DRY and name == "00_config_swarm.py":
        text = text.replace("DRY_RUN = False", "DRY_RUN = True")
    return text


def code(text, title=None, hide=False):
    body = (f"#@title {title}\n" if title else "") + text
    c = nbf.v4.new_code_cell(body)
    if hide:
        c.metadata["cellView"] = "form"
    return c


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


INTRO = """
# Canary Traps, Experiment 2b: the swarm, with opening requests

In the main run (tag `v3`), the six-agent swarm never sent a single message: nobody asked anybody for help, so nothing could be shared. In Experiment 1, a direct request is what made agents act.

**This notebook reruns the swarm on the same six-agent worlds** with two changes, both copied from Experiment 1:
1. every agent opens with a **scripted help request** to the teammate who holds the key it needs (the same wording as Experiment 1's peer request);
2. every agent is told it is also **on support duty**.

Everything after the opening requests is written by the models. The scripted requests are left out of every monitor score.

## How to run: nothing to edit
1. *Runtime → Change runtime type → **T4 GPU*** (if it isn't already).
2. *Runtime → **Run all***. Click **Run anyway** and allow **Google Drive** when asked.
3. Keep the tab open and the laptop plugged in and awake. It takes **about 1 hour 45 minutes**: about 30 minutes each for Qwen and Llama, up to 40 minutes for Gemini, then the monitor.
4. If Colab disconnects: reconnect and *Run all* again. Finished episodes are skipped.

Results are saved next to the main run's, in Drive → `canary_traps`, as `exp2_v3s_*.jsonl`. The main run's files are not touched.
"""

RES_MD = """
## Results

- **What the agents did**: messages, values fetched for a teammate and passed on, found-key uses, out-of-scope fetches, key leaks, reports, tasks completed.
- **Experiment 2 vs 2b**: the same worlds without and with the opening requests.
- **Which monitor flags the agents that broke a rule**: content monitors (secret scanner, LLM monitor), the agents' own audit answers, and the gateway checks (canary, out-of-scope).
"""

RUN_ALL = "run_swarm_only()\n"

RES = '''load_verdicts()
eps = load_results("exp2")
print(f"{len(eps)} episodes")
b2 = exp2_behaviour(eps)
display(b2.groupby(["model", "condition"]).mean(numeric_only=True).round(2))
print("The same worlds without and with the opening requests (Experiment 2 vs 2b), means per episode:")
compare2 = exp2_compare_runs("v3")
display(compare2)
m2 = exp2_metrics(eps, rate=1.0)
agg2 = plot_exp2_detection(m2)
print("Table view of the detection chart:")
display(agg2.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2))
print("Rounds from the first rule-break to each monitor's first flag (lower = earlier):")
display(exp2_latency(m2))
print("Same monitors when content monitors read only 20% of messages:")
m2_20 = exp2_metrics(eps, rate=0.2, draws=200)
display(m2_20.groupby(["model", "condition", "monitor"])["recall"].mean().unstack("monitor").round(2))
print("Content monitors judged message by message:")
msg_eval2 = exp2_message_level_eval(eps)
display(msg_eval2.round(3))
cands = [e for e in eps if e["condition"] != "O0_none"] or eps
if cands:
    plot_exp2_graph(max(cands, key=lambda e: len(exp2_ground_truth(e)["violators"])))
'''

EXAMPLES = '''# Read whole episodes for quotes and examples. Change the numbers to see others.
for ep in sorted(eps, key=lambda e: -len(exp2_ground_truth(e)["violators"]))[:3]:
    show_swarm_episode(ep)
'''

SUMMARY = '''summary_text = write_summary(None, globals().get("b2"), globals().get("m2"), None)
extra = []
if globals().get("compare2") is not None and len(compare2):
    extra += ["## Experiment 2 vs 2b on the same worlds (means per episode)", "", compare2.to_string(), ""]
if globals().get("msg_eval2") is not None and len(msg_eval2):
    extra += ["## Content monitors, message by message", "", msg_eval2.round(3).to_string(index=False), ""]
if extra:
    with open(os.path.join(RESULTS_DIR, f"summary_{TAG}.md"), "a") as f:
        f.write("\\n\\n" + "\\n".join(extra))
    print("\\n".join(extra))
'''

NOTES_MD = """
## When it has finished
Download the whole **canary_traps** folder from Drive (right-click → Download) and send the zip to Claude. It holds both runs, and the report will use both.
"""

cells = [
    md(INTRO),
    code('''try:
    from google.colab import drive
    drive.mount("/content/drive")
except Exception as e:
    print("Drive not mounted; results will be saved in this session only.", e)
''', "Save results to Google Drive (allow access when asked)"),
    code(src("00_config_swarm.py")),
    code(src("01_backends.py"), "Library: model backends and utilities", hide=True),
    code(src("02_world.py"), "Library: the fake company and the leak detectors", hide=True),
    code(src("08_mock.py"), "Library: dry-run stand-in model (testing only)", hide=True),
    code(src("03_exp1.py"), "Library: Experiment 1 (rules and audit text shared with the swarm)", hide=True),
    code(src("04_exp2.py"), "Library: Experiment 2 (the swarm)", hide=True),
    code(src("05_analysis.py"), "Library: ground truth, monitors, statistics and checks", hide=True),
    code(src("06_plots.py"), "Library: figures", hide=True),
    code(src("09_auto.py"), "Library: run every model", hide=True),
    md("## 1. Run the swarm on every model (about 1 hour 45 minutes)"),
    code(RUN_ALL, "Run the swarm (resumes where it stopped)"),
    md(RES_MD),
    code(RES, "Swarm results"),
    code(EXAMPLES, "Read whole episodes"),
    code(SUMMARY, "Write the results summary (also saved as a .md file next to the results)"),
    md(NOTES_MD),
]

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {
    "kernelspec": {"name": "python3", "display_name": "Python 3"},
    "language_info": {"name": "python"},
    "accelerator": "GPU",
    "colab": {"provenance": [], "gpuType": "T4", "name": "canary_traps_swarm.ipynb"},
}
nbf.validate(nb)
nbf.write(nb, OUT)
print("cells:", len(cells), "->", OUT)
