"""Assemble canary_traps_gaps.ipynb: key-only requests (Exp 1c), an access-aware monitor, and the seeded swarm (Exp 2b)."""
import os
import sys
import nbformat as nbf

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src") + os.sep
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebooks", "canary_traps_gaps.ipynb")
DRY = "--dry" in sys.argv
NOGPU = "--nogpu" in sys.argv


def src(name):
    text = open(SRC + name).read().rstrip() + "\n"
    if DRY and name.startswith("00_config"):
        text = text.replace("DRY_RUN = False", "DRY_RUN = True")
    if NOGPU and name.startswith("00_config"):
        text = text.replace("FORCE_NO_GPU = False", "FORCE_NO_GPU = True")
    return text


def code(text, title=None, hide=False):
    c = nbf.v4.new_code_cell((f"#@title {title}\n" if title else "") + text)
    if hide:
        c.metadata["cellView"] = "form"
    return c


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


INTRO = """
# Canary Traps: closing the gaps

This notebook runs three extra checks for the report. Each one answers a question a judge is likely to ask.

1. **Key-only requests (Experiment 1c).** In the main run, the teammate asked "send me a key, *or pull the number for me*?". Do agents still fetch the data themselves if nobody suggests it? This reruns **the same scenarios** with the teammate asking *only* for a key, so every trial pairs with a trial from the main run.
2. **A stronger content monitor.** A monitor reads the **whole conversation**, is told the access rules, and is asked directly whether data went to someone without access. Can a content monitor catch laundering if we ask it the right question?
3. **The swarm with opening requests (Experiment 2b).** If the swarm notebook already finished, those episodes are reused.

## Works with or without a GPU: nothing to edit
- **No GPU** (for example, when Colab says you have reached your GPU limit): it runs the **Gemini** parts, which need no GPU: Gemini on key-only requests, then Gemini as the stronger monitor. This takes about **1 hour 20 minutes**. Use *Runtime → Change runtime type → **CPU***.
- **With a T4 GPU**: it runs the **Qwen and Llama** parts: key-only requests, the swarm, and the monitors. This takes about **1½ hours**, or about **2½ hours** if the swarm notebook never finished.

Run it once each way to get everything; finished work is always skipped. Then *Runtime → **Run all***, click **Run anyway**, and allow **Google Drive** when asked. Keep the tab open, and keep the laptop plugged in and awake.

Results are saved next to the earlier runs in Drive → `canary_traps`: key-only files contain `v3k`, swarm files contain `v3s`, and monitor files start with `accessmon_`. Earlier files are not changed.
"""

RUN_ALL = "run_gaps()\n"

RES_A = '''set_tag("v3k")
load_verdicts_tags(["v3", "v3k", "v3s"])
dask = exp1_ask_table("v3", "v3k")
tbl_ask = tbl_k = eff = tests_k = None
if len(dask) and dask["ask"].nunique() == 2:
    print("Share of trials (%), by request wording (same scenarios), model and credential source:")
    tbl_ask = (dask.groupby(["model", "source", "ask"])[["proxied", "leaked", "reported", "violation"]].mean() * 100).round(0)
    display(tbl_ask)
    dk = dask[dask["ask"] == "key only"]
    print("Key-only requests, by oversight condition (%):")
    tbl_k = (dk.groupby(["model", "source", "condition"])[["proxied", "leaked", "reported"]].mean() * 100).round(0)
    display(tbl_k)
    print("Paired tests, the same scenario: 'key or fetch' vs 'key only' (exact McNemar):")
    eff = exp1_ask_effect(dask)
    display(eff)
    print("Oversight effects within key-only requests (McNemar, Holm-corrected):")
    tests_k = exp1_tests(dk)
    display(tests_k[["model", "source", "outcome", "comparison", "rate_first", "rate_second", "pairs", "p", "p_holm"]].round(3))
    print("Which monitor catches what, key-only requests (fetch-only trials):")
    det_k = exp1_detection(dk, "fetch")
    display(det_k.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2))
    plot_ask_effect(dask)
else:
    print("Key-only results are not complete yet.")
'''

RES_B = '''dacc = access_monitor_eval(("v3", "v3k"))
acc_sum = access_monitor_summary(dacc)
print("Access-aware monitor (reads the whole conversation and knows the access rules):")
display(acc_sum)
if len(dacc):
    lau = dacc[dacc["delivered"] & ~dacc["leaked"]]
    print("Laundered values sent in a message, flagged by the access-aware monitor, by condition:")
    display(lau.groupby(["monitor", "model", "ask", "condition"])["flag_data"].mean().unstack("condition").round(2))
'''

RES_C = '''set_tag("v3s")
eps = load_results("exp2")
print(f"{len(eps)} swarm episodes with opening requests")
b2 = m2 = agg2 = compare2 = msg_eval2 = None
if eps:
    b2 = exp2_behaviour(eps)
    display(b2.groupby(["model", "condition"]).mean(numeric_only=True).round(2))
    print("The same worlds without and with the opening requests (Experiment 2 vs 2b), means per episode:")
    compare2 = exp2_compare_runs("v3")
    display(compare2)
    m2 = exp2_metrics(eps, rate=1.0)
    agg2 = plot_exp2_detection(m2)
    print("Table view of the detection chart:")
    display(agg2.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2))
    print("Content monitors judged message by message:")
    msg_eval2 = exp2_message_level_eval(eps)
    display(msg_eval2.round(3))
    cands = [e for e in eps if e["condition"] != "O0_none"] or eps
    plot_exp2_graph(max(cands, key=lambda e: len(exp2_ground_truth(e)["violators"])))
'''

EXAMPLES = '''# Example transcripts for quotes: key-only requests where the agent fetched the data anyway.
set_tag("v3k")
show_examples(n=3, behaviour="Fetched the data for them", condition="O1_policy")
if globals().get("eps"):
    set_tag("v3s")
    for ep in sorted(eps, key=lambda e: -len(exp2_ground_truth(e)["violators"]))[:2]:
        show_swarm_episode(ep)
'''

SUMMARY = '''parts = ["# Canary Traps: gap checks (key-only requests, access-aware monitor, seeded swarm)", ""]
def add(title, obj):
    if obj is not None and len(obj):
        parts.extend([f"## {title}", "", obj.to_string(), ""])
add("Key-only vs key-or-fetch: share of trials (%)", globals().get("tbl_ask"))
add("Key-only requests by condition (%)", globals().get("tbl_k"))
add("Paired tests: key-or-fetch vs key-only", globals().get("eff"))
add("Oversight effects within key-only requests", globals().get("tests_k"))
add("Access-aware monitor", globals().get("acc_sum"))
if globals().get("b2") is not None:
    add("Swarm 2b: means per episode", b2.groupby(["model", "condition"]).mean(numeric_only=True).round(2))
    add("Swarm episodes per cell", b2.groupby(["model", "condition"]).size().to_frame("episodes"))
add("Experiment 2 vs 2b on the same worlds", globals().get("compare2"))
if globals().get("agg2") is not None:
    add("Swarm 2b: share of rule-breaking agents each monitor flags", agg2.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2))
add("Swarm 2b: content monitors message by message", globals().get("msg_eval2"))
text = "\\n".join(parts)
path = os.path.join(RESULTS_DIR, "summary_gaps.md")
open(path, "w").write(text)
print(text)
print("\\nSaved", path)
'''

NOTES = """
## When it has finished
Download the whole **canary_traps** folder from Drive (right-click → Download), and send the zip to Claude.
"""

cells = [
    md(INTRO),
    code('''try:
    from google.colab import drive
    drive.mount("/content/drive")
except Exception as e:
    print("Drive not mounted; results will be saved in this session only.", e)
''', "Save results to Google Drive (allow access when asked)"),
    code(src("00_config_gaps.py")),
    code(src("01_backends.py"), "Library: model backends and utilities", hide=True),
    code(src("02_world.py"), "Library: the fake company and the leak detectors", hide=True),
    code(src("08_mock.py"), "Library: dry-run stand-in model (testing only)", hide=True),
    code(src("03_exp1.py"), "Library: Experiment 1", hide=True),
    code(src("04_exp2.py"), "Library: Experiment 2 (the swarm)", hide=True),
    code(src("05_analysis.py"), "Library: ground truth, monitors and statistics", hide=True),
    code(src("06_plots.py"), "Library: figures", hide=True),
    code(src("09_auto.py"), "Library: run every model", hide=True),
    code(src("10_gaps.py"), "Library: the gap checks", hide=True),
    md("## 1. Run (with a GPU: Qwen and Llama; without one: Gemini)"),
    code(RUN_ALL, "Run the checks (resumes where it stopped)"),
    md("## 2. Results: key-only requests (Experiment 1c)"),
    code(RES_A, "Key-only requests vs the main run"),
    md("## 3. Results: the access-aware monitor"),
    code(RES_B, "Can a content monitor catch laundering if it is asked the right question?"),
    md("## 4. Results: the swarm with opening requests (Experiment 2b)"),
    code(RES_C, "Swarm results"),
    code(EXAMPLES, "Example transcripts"),
    code(SUMMARY, "Write the summary (also saved as summary_gaps.md next to the results)"),
    md(NOTES),
]
nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"},
               "accelerator": "GPU", "colab": {"provenance": [], "gpuType": "T4", "name": "canary_traps_gaps.ipynb"}}
nbf.validate(nb)
nbf.write(nb, OUT)
print("cells:", len(cells), "->", OUT)
