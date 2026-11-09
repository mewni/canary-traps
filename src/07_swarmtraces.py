# ===================== EXPERIMENT 3: SHARED CREDENTIALS IN THE REAL SWARM TRACES =====================
# Counts how often the same redaction placeholder (e.g. "[CREDENTIAL 12]") recurs across records of the
# redacted Swarm Traces release. It never tries to recover what a placeholder hid; it only uses the
# placeholder numbers, as the dataset's terms ask. Treat the file as untrusted text: nothing is executed.
import gzip, collections

PLACEHOLDER_RE = re.compile(r"\[(CREDENTIAL|SHORTENER CODE)\s+(\d+)\]")
REDACTED_RE = re.compile(r"\[REDACTED:([A-Za-z_]+)\]")


def scan_swarm_traces(path, max_records=None):
    opener = gzip.open if path.endswith(".gz") else open
    n, recs_with = 0, 0
    per_ph = collections.defaultdict(set)
    min_num_per_record = []
    redactions = collections.Counter()
    with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if max_records and i >= max_records:
                break
            if not line.strip():
                continue
            n += 1
            found = PLACEHOLDER_RE.findall(line)      # the raw JSON line, so nested fields count too
            if found:
                recs_with += 1
                min_num_per_record.append(min(int(num) for _, num in found))
            for kind, num in found:
                per_ph[(kind, int(num))].add(i)
            redactions.update(REDACTED_RE.findall(line))

    # Records linked by a shared placeholder form connected groups (union-find).
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for recs in per_ph.values():
        recs = list(recs)
        for r in recs[1:]:
            parent[find(r)] = find(recs[0])
    groups = collections.Counter(find(r) for recs in per_ph.values() for r in recs)
    sizes = sorted(groups.values(), reverse=True)

    ph = pd.DataFrame([{"kind": k, "number": num, "records": len(v)} for (k, num), v in per_ph.items()])
    starts_at_one = (np.mean([m == 1 for m in min_num_per_record]) if min_num_per_record else float("nan"))
    summary = {
        "records": n, "records_with_placeholders": recs_with,
        "distinct_credential_placeholders": int((ph["kind"] == "CREDENTIAL").sum()) if len(ph) else 0,
        "distinct_shortener_placeholders": int((ph["kind"] == "SHORTENER CODE").sum()) if len(ph) else 0,
        "credential_placeholders_in_2plus_records": int(((ph["kind"] == "CREDENTIAL") & (ph["records"] >= 2)).sum()) if len(ph) else 0,
        "largest_linked_group_records": sizes[0] if sizes else 0,
        "linked_groups_of_2plus": sum(1 for s in sizes if s >= 2),
        "share_of_placeholder_records_whose_numbering_starts_at_1": (f"{starts_at_one:.0%}" if starts_at_one == starts_at_one else "n/a"),
        "redaction_types": dict(redactions.most_common(12)),
    }
    if starts_at_one == starts_at_one and starts_at_one > 0.8:
        print("WARNING: most records number their placeholders from 1, so numbers may restart per record. "
              "If so, the same number in two records does NOT mean the same credential: report counts only, not reuse.")
    return summary, ph


def plot_placeholder_reuse(ph):
    cred = ph[ph["kind"] == "CREDENTIAL"]
    if not len(cred):
        print("No credential placeholders found.")
        return
    bins = [(1, 1, "1 record"), (2, 5, "2–5"), (6, 20, "6–20"), (21, 100, "21–100"), (101, 10 ** 9, "over 100")]
    counts = [int(((cred["records"] >= lo) & (cred["records"] <= hi)).sum()) for lo, hi, _ in bins]
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    ax.bar(range(len(bins)), counts, width=0.55, color=SLOTS[0])
    for i, c in enumerate(counts):
        ax.text(i, c, f"{c:,}", ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(bins)), [b[2] for b in bins])
    ax.set_xlabel("Records in which the same credential placeholder appears")
    ax.set_ylabel("Credential placeholders")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title("Swarm Traces: how widely each redacted credential recurs")
    fig.tight_layout()
    _save(fig, "exp3_placeholder_reuse")
    plt.show()
