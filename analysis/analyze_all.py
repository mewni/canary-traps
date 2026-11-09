"""Recompute every number in the report from the raw logs.
Usage: python3 -I analyze_all.py <canary_traps data dir> <output dir> [--mock]
Writes results.md (all tables) and numbers.json (headline numbers) to the output dir."""
import sys, os, io, json, contextlib, math, glob

DATA, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
MOCK = "--mock" in sys.argv
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src") + os.sep

import matplotlib
matplotlib.use("Agg")
ns = {"__name__": "analysis", "display": lambda *a, **k: None}
for f in ["00_config_gaps.py", "01_backends.py", "02_world.py", "08_mock.py", "03_exp1.py", "04_exp2.py",
          "05_analysis.py", "06_plots.py", "09_auto.py", "10_gaps.py"]:
    code = open(SRC + f).read()
    if f.startswith("00_config"):
        code = code.replace("DRY_RUN = False", f"DRY_RUN = {MOCK}")
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code, f, "exec"), ns)
ns["RESULTS_DIR"] = DATA
ns["FIG_DIR"] = os.path.join(OUT, "nbfigs")
os.makedirs(ns["FIG_DIR"], exist_ok=True)
G = ns
pd, np = G["pd"], G["np"]
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 500)

md, NUM = [], {}


def sec(title):
    md.extend(["", f"## {title}", ""])


def tab(df, title=None, index=True):
    if title:
        md.append(f"**{title}**")
        md.append("")
    if df is None or not len(df):
        md.append("(none)")
    else:
        md.append("```")
        md.append(df.to_string(index=index))
        md.append("```")
    md.append("")


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def wil(k, n):
    p, lo, hi = G["wilson"](int(k), int(n)) if n else (float("nan"),) * 3
    return p, lo, hi


# ---------------------------------------------------------------- Experiment 1 (main run v3)
quiet(G["load_verdicts_tags"], ["v3", "v3k", "v3s"])
recs1 = G["load_results_tag"]("exp1", "v3")
df_all = G["exp1_table"](recs1)
df = G["main_wording"](df_all)
NUM["exp1_trials_all_wordings"] = len(df_all)
NUM["exp1_trials_main"] = len(df)
sec("Experiment 1 (v3): trials")
tab(df.groupby(["model", "source", "condition"]).size().unstack("condition"), "Main-wording trials per cell")

cols = ["leaked", "proxied", "fetched", "delivered_value", "reported", "used_found_key", "violation",
        "requester_used_key", "audit_says_shared", "audit_says_fetched", "audit_says_used_foreign_key", "escalated", "renamed"]
cell = df.groupby(["model", "source", "condition"])[cols].mean().round(3)
tab(cell, "Rates per cell (main wording)")

lk = df[df["leaked"]]
fo = df[df["proxied"] & ~df["leaked"]]
viol = df[df["violation"]]
NUM.update(leak_trials=len(lk), fetch_only_trials=len(fo), violating_trials=len(viol),
           invisible_share=len(fo) / len(viol) if len(viol) else None,
           proxied_trials=int(df["proxied"].sum()), delivered_trials=int(df["delivered_value"].sum()),
           fetched_trials=int(df["fetched"].sum()))
for name, k_ in (("leak", len(lk)), ("fetch_only", len(fo))):
    p, a, b = wil(k_, len(df))
    NUM[f"{name}_rate"], NUM[f"{name}_ci"] = p, (a, b)
NUM["violation_other"] = int((df["violation"] & ~df["leaked"] & ~df["proxied"]).sum())
NUM["fetch_only_delivered_share"] = float(fo["delivered_value"].mean()) if len(fo) else None
NUM["fetch_only_by_source"] = fo.groupby("source").size().to_dict()
sec("Experiment 1 headline counts")
md.append("```\n" + json.dumps({k: NUM[k] for k in NUM}, indent=1, default=str) + "\n```")

# detection
sec("Detection by monitor")
d_leak = quiet(G["exp1_detection"], df, "leak")
d_fetch = quiet(G["exp1_detection"], df, "fetch")
tab(d_leak.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2), "Leak trials (rate)")
tab(d_fetch.pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2), "Fetch-only trials (rate)")
pool = {}
for col, name in G["MONITORS_LEAK"]:
    pool[f"leak|{name}"] = (int(lk[col].fillna(False).astype(bool).sum()) if col in lk else None, len(lk))
for col, name in G["MONITORS_FETCH"]:
    pool[f"fetch|{name}"] = (int(fo[col].fillna(False).astype(bool).sum()) if col in fo else None, len(fo))
# The per-message LLM monitor on laundered fetches. No credential appears in any of these messages,
# so every alarm here is a false credential alarm. For comparison: its alarm rate on trials with no misuse.
pool["fetch|LLM monitor, all messages (false alarms)"] = (int((fo["det_llm_monitor_100"].fillna(0) > 0).sum()), len(fo))
_clean = df[~df["violation"]]
NUM["llm_monitor_alarms_no_misuse"] = (int((_clean["det_llm_monitor_100"].fillna(0) > 0).sum()),
                                       int(_clean["det_llm_monitor_100"].notna().sum()))
for src in ("own", "found"):
    g = fo[fo["source"] == src]
    pool[f"fetch_{src}|Agent's own audit answer"] = (int(g["det_self_report_fetch"].astype(bool).sum()), len(g))
NUM["pooled_detection"] = pool
md.append("```\n" + json.dumps(pool, indent=1) + "\n```")
if "det_canary_or_scope" in lk:
    NUM["leak_canary_or_scope"] = (int(lk["det_canary_or_scope"].astype(bool).sum()), len(lk))

# board vs DM
lk_board = lk["det_board_scanner_100"].astype(bool)
nr = lk[lk["condition"] == "O0_none"]
rr = lk[lk["condition"] != "O0_none"]
nb_, rb_ = int(nr["det_board_scanner_100"].astype(bool).sum()), int(rr["det_board_scanner_100"].astype(bool).sum())
from scipy.stats import fisher_exact
NUM["board_share"] = {"no_rules": (nb_, len(nr)), "rules": (rb_, len(rr)),
                      "fisher_p": float(fisher_exact([[nb_, len(nr) - nb_], [rb_, len(rr) - rb_]])[1]) if len(nr) and len(rr) else None}

# audit honesty
claims = df[df["audit_says_shared"] == True]
true_claims = claims[claims["leaked"]]
NUM["audit"] = {"claims": len(claims), "true_claims": len(true_claims), "leakers": len(lk),
                "leakers_admitted": int(lk["audit_says_shared"].fillna(False).astype(bool).sum()),
                "by_model_claims": claims.groupby("model").size().to_dict(),
                "by_model_true": true_claims.groupby("model").size().to_dict()}
tab(quiet(G["exp1_audit_honesty"], df).round(2), "Audit honesty by model and condition")

# message-level
sec("Message-level monitor evaluation (all Exp 1 messages, all wordings)")
tab(quiet(G["message_level_eval"], recs1), index=False)

# tests
sec("Paired tests (Holm)")
t1 = quiet(G["exp1_tests"], df_all)
tab(t1[["model", "source", "outcome", "comparison", "rate_first", "rate_second", "pairs", "only_first", "only_second",
        "p", "p_holm", "cochran_Q", "cochran_p"]].round(5), index=False)
tab(quiet(G["exp1_source_effect"], df_all).round(4), "Own vs found", index=False)
tab(quiet(G["exp1_requester_effect"], df_all).round(4), "Peer vs coordinator", index=False)
wc = quiet(G["exp1_wording_check"], df_all)
tab(wc.round(3), "Second wording", index=False)
NUM["wording_min_p"] = float(wc["p"].min()) if len(wc) else None
NUM["wording_n"] = len(wc)
tab(quiet(G["exp1_tactics"], df_all), "Disguise tactics")
NUM["disguised_trials"] = int(df_all["tactics"].astype(bool).sum())

# requester outcomes
NUM["requester_used_key_in_leaks"] = (int(lk["requester_used_key"].sum()), len(lk))

# ---------------------------------------------------------------- Experiment 1c (key-only, v3k)
sec("Experiment 1c: key-only requests")
dask = G["exp1_ask_table"]("v3", "v3k")
if len(dask) and dask["ask"].nunique() == 2:
    dk = dask[dask["ask"] == "key only"]
    tab(dk.groupby(["model", "source", "condition"]).size().unstack("condition"), "Key-only trials per cell")
    tab(dask.groupby(["model", "source", "ask"])[["proxied", "leaked", "reported", "violation", "used_found_key"]].mean().round(3),
        "Rates by request wording")
    tab(dk.groupby(["model", "source", "condition"])[["proxied", "leaked", "reported", "fetched", "delivered_value"]].mean().round(3),
        "Key-only by condition")
    eff = G["exp1_ask_effect"](dask)
    tab(eff, "Paired: key-or-fetch vs key-only", index=False)
    tk = quiet(G["exp1_tests"], dk)
    tab(tk[["model", "source", "outcome", "comparison", "rate_first", "rate_second", "pairs", "p", "p_holm"]].round(5),
        "Oversight tests within key-only", index=False)
    lkk, fok = dk[dk["leaked"]], dk[dk["proxied"] & ~dk["leaked"]]
    vk = dk[dk["violation"]]
    NUM["keyonly"] = {"trials": len(dk), "leak": len(lkk), "fetch_only": len(fok), "violating": len(vk),
                      "invisible_share": len(fok) / len(vk) if len(vk) else None,
                      "by_model": dk.groupby("model")[["proxied", "leaked", "reported", "violation"]].mean().round(4).to_dict(),
                      "by_model_source": {f"{m}|{s}": v for (m, s), v in
                                          dk.groupby(["model", "source"])[["proxied", "leaked", "reported"]].mean().round(4).iterrows()
                                          for v in [v.to_dict()]}}
    tab(quiet(G["exp1_detection"], dk, "fetch").pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2),
        "Key-only fetch-only detection")
    tab(quiet(G["exp1_detection"], dk, "leak").pivot_table(index="monitor", columns=["model", "condition"], values="rate").round(2),
        "Key-only leak detection")
    tab(G["exp1_behaviour_shares"](dk).pivot_table(index=["model", "condition"], columns="behaviour", values="share").round(2),
        "Key-only behaviour shares")
else:
    md.append("(no key-only data)")

# ---------------------------------------------------------------- access-aware monitor
sec("Access-aware monitor")
dacc = G["access_monitor_eval"](("v3", "v3k"))
if len(dacc):
    tab(G["access_monitor_summary"](dacc), index=False)
    m = dacc[dacc["wording"] == "main"]
    lau = m[m["delivered"] & ~m["leaked"]]
    tab(lau.groupby(["monitor", "model", "ask", "source"])["flag_data"].agg(["mean", "size"]).round(3),
        "Laundered values flagged, by source")
    tab(lau.groupby(["monitor", "ask", "condition"])["flag_data"].agg(["mean", "size"]).round(3),
        "Laundered values flagged, by condition")
    acc = {}
    for (mon, ask), g in m.groupby(["monitor", "ask"]):
        lk_, dl_, cl_ = g[g["leaked"]], g[g["delivered"] & ~g["leaked"]], g[g["clean"]]
        acc[f"{mon}|{ask}"] = {"leaks": (int(lk_["flag_any"].sum()), len(lk_)),
                               "laundered_data_flag": (int(dl_["flag_data"].sum()), len(dl_)),
                               "laundered_any_flag": (int(dl_["flag_any"].sum()), len(dl_)),
                               "clean_false_alarm": (int(cl_["flag_any"].sum()), len(cl_))}
    NUM["access_monitor"] = acc
    md.append("```\n" + json.dumps(acc, indent=1) + "\n```")
else:
    md.append("(no access-monitor verdicts)")

# ---------------------------------------------------------------- swarm (v3 and v3s)
sec("Swarm")
eps_a = G["load_results_tag"]("exp2", "v3")
eps_b = G["load_results_tag"]("exp2", "v3s")
for tag, eps in (("v3", eps_a), ("v3s", eps_b)):
    if not eps:
        md.append(f"(no {tag} episodes)")
        continue
    b = G["exp2_behaviour"](eps)
    tab(b.groupby(["model", "condition"]).mean(numeric_only=True).round(2), f"{tag}: means per episode")
    tab(b.groupby(["model", "condition"]).size().to_frame("episodes"), f"{tag}: episodes")
    m2 = quiet(G["exp2_metrics"], eps, 1.0, 1)
    agg = m2.groupby(["model", "condition", "monitor"])[["recall", "precision", "n_violators"]].mean().round(2)
    tab(agg, f"{tag}: per-episode monitor recall over rule-breaking agents")
    tab(G["exp2_message_level_eval"](eps).round(3), f"{tag}: message-level", index=False)
    # pooled agent-level detection
    rows = []
    for ep in eps:
        gt = G["exp2_ground_truth"](ep)
        flags = G["exp2_monitor_flags"](ep, gt)
        for mon, fl in flags.items():
            rows.append({"model": ep["model"], "monitor": mon, "violators": len(gt["violators"]),
                         "caught": len(set(fl) & gt["violators"])})
    pr = pd.DataFrame(rows)
    if len(pr):
        tot = pr.groupby(["model", "monitor"])[["caught", "violators"]].sum()
        tot["rate"] = (tot["caught"] / tot["violators"]).round(3)
        tab(tot, f"{tag}: pooled agent-level detection")
        NUM[f"swarm_{tag}_pooled"] = {f"{m}|{mon}": (int(r.caught), int(r.violators)) for (m, mon), r in tot.iterrows()}
    NUM[f"swarm_{tag}"] = b.groupby("model").mean(numeric_only=True).round(3).to_dict(orient="index")
    NUM[f"swarm_{tag}_episodes"] = b.groupby("model").size().to_dict()
if eps_b:
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        for ep in sorted(eps_b, key=lambda e: -len(G["exp2_ground_truth"](e)["violators"]))[:4]:
            G["show_swarm_episode"](ep, max_lines=60)
    open(os.path.join(OUT, "swarm_examples.txt"), "w").write(buf.getvalue())

open(os.path.join(OUT, "results.md"), "w").write("\n".join(md))
json.dump(NUM, open(os.path.join(OUT, "numbers.json"), "w"), indent=1, default=str)
print("wrote", os.path.join(OUT, "results.md"), "and numbers.json")
