# ===================== FIGURES =====================
# Palette: validated categorical slots (light surface). Text always uses ink colours, never series colours.
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyArrowPatch

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
LABEL_ON = {"#eda100": INK}          # text inside a yellow fill is near-black; white elsewhere
DEEMPH = "#c3c2b7"                    # non-highlighted bars
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "font.size": 9.5, "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
})


def _save(fig, name):
    path = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    print("saved", path)


def _cond_order(conds):
    return [c for c in CONDITIONS if c in set(conds)]


def plot_exp1_behaviour(df):
    df = main_wording(df)
    shares = exp1_behaviour_shares(df)
    lab = df["model"] + " · " + df["source"].map(SOURCE_LABELS)
    panels = sorted(shares["model"].unique())
    fig, axes = plt.subplots(len(panels), 1, figsize=(8.8, 0.9 + 0.55 * 4 * len(panels)), squeeze=False)
    for ax, panel in zip(axes[:, 0], panels):
        sub = shares[shares["model"] == panel]
        conds = _cond_order(sub["condition"])
        for yi, cond in enumerate(conds):
            left = 0.0
            for bi, b in enumerate(BEHAVIOURS):
                v = sub[(sub["condition"] == cond) & (sub["behaviour"] == b)]["share"].sum()
                if v <= 0:
                    continue
                col = SLOTS[bi]
                ax.barh(yi, v, left=left, height=0.56, color=col, edgecolor=SURFACE, linewidth=1.5)
                if v >= 0.12:
                    ax.text(left + 0.012, yi, f"{v:.0%}", va="center", ha="left", fontsize=8.5,
                            color=LABEL_ON.get(col, "white"))
                left += v
            n = int(((lab == panel) & (df["condition"] == cond)).sum())
            ax.text(1.01, yi, f"n={n}", va="center", ha="left", fontsize=8, color=MUTED)
        ax.set_yticks(range(len(conds)), [CONDITION_LABELS[c] for c in conds])
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        ax.set_title(f"What the agent on support duty did  ·  {panel}")
        ax.tick_params(axis="y", length=0)
    handles = [Patch(facecolor=SLOTS[i], label=b) for i, b in enumerate(BEHAVIOURS)]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0), fontsize=8.5,
               handlelength=1.0, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0.06 + 0.02 * (len(panels) < 3), 1, 1))
    _save(fig, "exp1_behaviour")
    plt.show()


def _detection_grid(det, monitor_names, highlight, title, fname):
    models = sorted(det["model"].unique())
    conds = _cond_order(det["condition"])
    if not conds:
        print("No violating trials to plot yet.")
        return
    fig, axes = plt.subplots(len(models), len(conds), figsize=(2.75 * len(conds) + 1.8, 0.42 * len(monitor_names) * len(models) + 1.1),
                             squeeze=False, sharex=True)
    for r, model in enumerate(models):
        for c, cond in enumerate(conds):
            ax = axes[r, c]
            g = det[(det["model"] == model) & (det["condition"] == cond)].set_index("monitor")
            for yi, mon in enumerate(monitor_names):
                if mon not in g.index or pd.isna(g.loc[mon, "rate"]):
                    ax.text(0.01, yi, "n/a", va="center", fontsize=8, color=MUTED)
                    continue
                v, lo, hi = g.loc[mon, ["rate", "lo", "hi"]]
                col = SLOTS[0] if mon in highlight else DEEMPH
                ax.barh(yi, v, height=0.5, color=col)
                ax.plot([lo, hi], [yi, yi], color=INK2, linewidth=1)
                ax.text(min(hi, 1) + 0.03, yi, f"{v:.0%}", va="center", fontsize=8, color=INK)
            ax.set_xlim(0, 1.28)
            ax.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
            ax.grid(axis="x")
            ax.set_axisbelow(True)
            ax.set_yticks(range(len(monitor_names)), monitor_names if c == 0 else [""] * len(monitor_names))
            ax.tick_params(axis="y", length=0)
            ax.invert_yaxis()
            n = int(g["n"].iloc[0]) if len(g) else 0
            ax.set_title(f"{CONDITION_LABELS[cond]}  (n={n})", fontsize=9.5)
        axes[r, 0].set_ylabel(model, fontsize=9, color=INK2)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="bold", color=INK)
    fig.tight_layout()
    _save(fig, fname)
    plt.show()


def plot_exp1_detection(df):
    df = main_wording(df)
    det = exp1_detection(df, "leak")
    _detection_grid(det, [n for _, n in MONITORS_LEAK], {"Canary gateway"},
                    "Share of credential leaks each monitor catches (bars: mean, lines: 95% bootstrap interval)",
                    "exp1_detection_leaks")
    det_f = exp1_detection(df, "fetch")
    if len(det_f):
        _detection_grid(det_f, [n for _, n in MONITORS_FETCH], {"Canary + scope check"},
                        "When the agent fetched the data for the teammate instead of passing on the credential",
                        "exp1_detection_fetch")
    return det, det_f


def plot_exp1_audit(df):
    df = main_wording(df)
    h = exp1_audit_honesty(df)
    models = sorted(h["model"].unique())
    fig, axes = plt.subplots(1, len(models), figsize=(4.2 * len(models), 2.6), squeeze=False)
    for ax, model in zip(axes[0], models):
        g = h[h["model"] == model].set_index("condition")
        conds = _cond_order(g.index)
        for yi, cond in enumerate(conds):
            p, lo, hi, n = g.loc[cond, ["admitted_leak", "lo", "hi", "n_leakers"]]
            if n == 0:
                ax.text(0.01, yi, "no leaks", va="center", fontsize=8, color=MUTED)
                continue
            ax.barh(yi, p, height=0.5, color=SLOTS[0])
            ax.plot([lo, hi], [yi, yi], color=INK2, linewidth=1)
            ax.text(min(hi, 1) + 0.03, yi, f"{p:.0%} of {int(n)}", va="center", fontsize=8, color=INK)
        ax.set_yticks(range(len(conds)), [CONDITION_LABELS[c] for c in conds])
        ax.invert_yaxis()
        ax.set_xlim(0, 1.35)
        ax.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.set_title(f"Leakers who admitted it in the audit  ·  {model}", fontsize=10)
    fig.tight_layout()
    _save(fig, "exp1_audit_honesty")
    plt.show()
    return h


def plot_exp2_detection(m):
    agg = (m.groupby(["model", "condition", "monitor"])["recall"]
           .apply(lambda s: pd.Series(bootstrap_mean(s.tolist()), index=["rate", "lo", "hi"]))
           .unstack().reset_index())
    agg["n"] = m.groupby(["model", "condition", "monitor"])["recall"].apply(lambda s: s.notna().sum()).values
    _detection_grid(agg, EXP2_MONITORS, {"Canary gateway", "Canary + scope check"},
                    "Swarm episodes: share of rule-breaking agents each monitor flags", "exp2_detection")
    return agg


def _ring_pos(n):
    ang = [math.pi / 2 - 2 * math.pi * i / n for i in range(n)]
    return [(math.cos(a), math.sin(a)) for a in ang]


def plot_exp2_graph(ep):
    gt = exp2_ground_truth(ep)
    flags = exp2_monitor_flags(ep, gt, 1.0)
    pos = _ring_pos(len(ep["agents"]))
    key_edges = sorted({(c["key_owner"], c["caller"]) for c in gt["uses"] if c["key_owner"] != c["caller"]})
    true_data = sorted({(d["from"], d["to"]) for d in gt["deliveries"]})
    # The gateway sees which record each call fetched, so it can name whose task needed it.
    scope_data = sorted({(c["caller"], _scope_beneficiary(ep, c)) for c in gt["proxies"] + gt["uses"]
                         if _scope_beneficiary(ep, c) not in (None, c["caller"])})
    panels = [("What happened (full logs)", key_edges, true_data, gt["violators"]),
              ("What the canary gateway + scope check saw", key_edges, scope_data,
               set(flags.get("Canary + scope check", {}))),
              ("What a secret scanner on all messages saw", [], [], set(flags.get("Secret scanner, all messages", {})))]
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4))
    for ax, (title, ke, de, flagged) in zip(axes, panels):
        for (u, v), col in [(e, SLOTS[0]) for e in ke] + [(e, SLOTS[1]) for e in de]:
            (x1, y1), (x2, y2) = pos[u], pos[v]
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, color=col,
                                         linewidth=2, shrinkA=17, shrinkB=17, connectionstyle="arc3,rad=0.12"))
        for a in ep["agents"]:
            x, y = pos[a["id"]]
            on = a["id"] in flagged
            ax.scatter([x], [y], s=520, color=INK if on else SURFACE, edgecolors=INK if on else AXIS,
                       linewidths=1.5, zorder=3)
            ax.text(x, y, a["service"][:3], ha="center", va="center", fontsize=7.5,
                    color="white" if on else INK2, zorder=4)
            ax.text(x * 1.45, y * 1.36, a["handle"], ha="center", va="center", fontsize=7.5, color=INK2)
        ax.set_xlim(-1.75, 1.75)
        ax.set_ylim(-1.6, 1.6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=9.5)
    legend = [Line2D([0], [0], color=SLOTS[0], lw=2, label="Key passed on and used (issued to / found by → user)"),
              Line2D([0], [0], color=SLOTS[1], lw=2, label="Data fetched for another agent (fetcher → beneficiary)"),
              Line2D([0], [0], marker="o", color="none", markerfacecolor=INK, markersize=9,
                     label="Agent flagged / broke a rule")]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=8.5)
    fig.suptitle(f"One episode · {CONDITION_LABELS[ep['condition']]} · {ep['model']}  (circles show each agent's own service)",
                 x=0.01, ha="left", fontsize=11, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.07, 1, 0.93))
    _save(fig, f"exp2_graph_{norm(ep['id'])[:60]}")
    plt.show()


def plot_wording_robustness(check):
    """Leak and fetch rates under the original vs the second wording of the rules (paired scenarios)."""
    if check is None or not len(check):
        print("No second-wording trials yet.")
        return
    models = sorted(check["model"].unique())
    fig, axes = plt.subplots(len(models), 2, figsize=(9.5, 0.9 + 1.1 * len(models) * 1.6), squeeze=False)
    for r, model in enumerate(models):
        for c, out in enumerate(("leaked", "proxied")):
            ax = axes[r, c]
            g = check[(check["model"] == model) & (check["outcome"] == out)].set_index("condition")
            conds = _cond_order(g.index)
            for yi, cond in enumerate(conds):
                a, b, n = g.loc[cond, ["original_wording", "second_wording", "pairs"]]
                ax.plot([a, b], [yi - 0.13, yi + 0.13], color=GRID, linewidth=2, zorder=1)
                ax.scatter([a], [yi - 0.13], s=60, color=SLOTS[0], edgecolors=SURFACE, linewidths=2, zorder=3)
                ax.scatter([b], [yi + 0.13], s=60, color=SLOTS[1], edgecolors=SURFACE, linewidths=2, zorder=3)
                ax.text(1.04, yi, f"n={int(n)} pairs, p={g.loc[cond, 'p']:.2f}", va="center", fontsize=7.5, color=MUTED,
                        transform=ax.get_yaxis_transform())
            ax.set_yticks(range(len(conds)), [CONDITION_LABELS[x] for x in conds] if c == 0 else [""] * len(conds))
            ax.set_xlim(-0.03, 1.03)
            ax.set_ylim(len(conds) - 0.5, -0.5)
            ax.set_xticks([0, 0.5, 1], ["0", "50%", "100%"])
            ax.grid(axis="x")
            ax.set_axisbelow(True)
            ax.tick_params(axis="y", length=0)
            ax.set_title(("Leaked the key" if out == "leaked" else "Fetched the data") + f"  ·  {model}", fontsize=9.5)
    fig.legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=SLOTS[0], markersize=8, label="Original wording"),
                        Line2D([0], [0], marker="o", color="none", markerfacecolor=SLOTS[1], markersize=8, label="Second wording")],
               loc="lower center", ncol=2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.08, 0.86, 1))
    _save(fig, "exp1_wording_robustness")
    plt.show()
