import sys, os, io, json, contextlib
DATA = sys.argv[1]
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src") + os.sep
import matplotlib; matplotlib.use("Agg")
ns = {"__name__": "x", "display": lambda *a, **k: None}
for f in ["00_config_gaps.py", "01_backends.py", "02_world.py", "08_mock.py", "03_exp1.py", "04_exp2.py", "05_analysis.py", "06_plots.py", "09_auto.py", "10_gaps.py"]:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(open(SRC + f).read(), f, "exec"), ns)
ns["RESULTS_DIR"] = DATA
G = ns
with contextlib.redirect_stdout(io.StringIO()):
    G["load_verdicts_tags"](["v3", "v3k", "v3s"])
pd = G["pd"]
out = {}
for tag in ("v3", "v3s"):
    eps = G["load_results_tag"]("exp2", tag)
    rows = []
    for ep in eps:
        gt = G["exp2_ground_truth"](ep)
        fl = G["exp2_monitor_flags"](ep, gt)
        V = gt["violators"]
        union = set(fl.get("Secret scanner, all messages", {})) | set(fl.get("Canary + scope check", {}))
        union_llm = union | set(fl.get("LLM monitor", {}))
        r = {"model": ep["model"].split(":")[1], "condition": ep["condition"], "violators": len(V),
             "leakers": len(gt["leakers"]), "users": len(gt["users"]), "proxy_agents": len(gt["proxy_agents"]),
             "only_leakers": len(gt["leakers"] - gt["users"] - gt["proxy_agents"]),
             "silent_users_or_proxies": len((gt["users"] | gt["proxy_agents"]) - gt["leakers"]),
             "msgs": len(gt["msgs"]), "deliveries": len(gt["deliveries"])}
        for mon in G["EXP2_MONITORS"]:
            f = set(fl.get(mon, {}))
            r[f"caught|{mon}"] = len(f & V)
            r[f"flagged|{mon}"] = len(f)
        r["caught|Scanner OR canary+scope"] = len(union & V)
        r["caught|Scanner OR LLM OR canary+scope"] = len(union_llm & V)
        rows.append(r)
    d = pd.DataFrame(rows)
    if not len(d):
        continue
    print(f"===== {tag}: {len(d)} episodes")
    agg = d.groupby("model")[[c for c in d.columns if c not in ("model", "condition")]].sum()
    print(agg.T.to_string())
    by_cond = d.groupby(["model", "condition"])[["violators", "leakers", "users", "proxy_agents", "msgs"]].sum()
    print(by_cond.to_string())
    tot = d[[c for c in d.columns if c not in ("model", "condition")]].sum()
    print("TOTAL violators", tot["violators"], {k.split("|")[1]: int(tot[k]) for k in tot.index if k.startswith("caught|")})
    print("flagged totals", {k.split("|")[1]: int(tot[k]) for k in tot.index if k.startswith("flagged|")})
    out[tag] = {"by_model": agg.to_dict(orient="index"), "total": {k: int(v) for k, v in tot.items()}}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "swarm_pooled.json"), "w"), indent=1)
