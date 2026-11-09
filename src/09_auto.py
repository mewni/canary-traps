# ===================== RUN EVERYTHING: every model, both experiments, then the fixed monitor =====================
import subprocess, shutil

RUN_DEADLINE = None


def has_gpu():
    try:
        return subprocess.run(["nvidia-smi"], capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


def start_ollama(model, parallel=4, ctx=6144):
    if shutil.which("ollama") is None:
        print("Installing Ollama (about a minute)...")
        subprocess.run("apt-get -qq update > /dev/null 2>&1; apt-get -qq install -y zstd > /dev/null 2>&1", shell=True)
        subprocess.run("curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1", shell=True, check=True)
    try:
        requests.get("http://localhost:11434", timeout=2)
    except Exception:
        env = dict(os.environ, OLLAMA_NUM_PARALLEL=str(parallel), OLLAMA_KEEP_ALIVE="6h",
                   OLLAMA_CONTEXT_LENGTH=str(ctx), OLLAMA_MAX_LOADED_MODELS="2")
        subprocess.Popen(["ollama", "serve"], env=env, stdout=open(os.path.abspath("ollama.log"), "w"),
                         stderr=subprocess.STDOUT)
        for _ in range(90):
            try:
                requests.get("http://localhost:11434", timeout=2)
                break
            except Exception:
                time.sleep(1)
    print(f"Downloading {model} if needed (about 2-4 minutes the first time)...", flush=True)
    subprocess.run(["ollama", "pull", model], check=True, capture_output=True)


def make_backend(kind, name):
    if DRY_RUN:
        return MockBackend(label=f"mock:{name.split('/')[-1]}")
    if kind == "ollama":
        start_ollama(name, parallel=max(4, WORKERS))
        return OllamaBackend(name)
    if kind == "colab_gemini":
        return ColabGeminiBackend(name)
    if kind == "openai_compat":
        return OpenAICompatBackend(**OPENAI_COMPAT)
    raise ValueError(f"Unknown model kind: {kind}")


def probe_ok(backend):
    """Run the first trial of every cell and check the model actually follows the action format."""
    recs = run_experiment1(backend, trials_per_cell=1, alt_trials_per_cell=0)
    if not recs:
        return False, "no trial finished"
    df = exp1_table(recs)
    broken = float((df["invalid"] >= 2).mean())
    return broken <= 0.5, f"{broken:.0%} of probe trials had unreadable replies"


def model_summary(label):
    recs = [r for r in load_results("exp1") if r.get("model") == label]
    if not recs:
        return
    d = main_wording(exp1_table(recs))
    t = d.groupby(["source", "condition"])[["leaked", "proxied", "reported", "requester_used_key", "audit_says_shared"]].mean()
    t.index = [f"{SOURCE_LABELS[s_]} · {CONDITION_LABELS[c]}" for s_, c in t.index]
    print(f"\nFirst look at {label} (full analysis is further down):")
    print((t * 100).round(0).astype(int).astype(str).add("%").to_string())


def run_everything():
    global WORKERS, RUN_DEADLINE
    gpu = DRY_RUN or has_gpu()
    if not gpu:
        print("NOTE: no GPU in this session, so the open models are skipped.\n"
              "For them: Runtime > Change runtime type > T4 GPU, then Run all again (finished work is kept).")
    t_start = time.time()
    for kind, name in MODELS:
        print("\n" + "=" * 90 + f"\nMODEL: {name}  ({kind})\n" + "=" * 90, flush=True)
        if kind == "ollama" and not gpu:
            print("Skipped: needs a GPU.")
            continue
        light = kind == "colab_gemini" and not QUICK
        WORKERS = 2 if kind == "colab_gemini" else 4
        RUN_DEADLINE = time.time() + GEMINI_TIME_BUDGET_MIN * 60 if kind == "colab_gemini" else None
        try:
            backend = make_backend(kind, name)
            reply = parse_json(backend.chat('Reply with ONLY this JSON object: {"ok": true}', 0.0))
            print("Model answers:", reply)
            ok, why = probe_ok(backend)
            if not ok:
                print(f"Skipping {name}: it is not following the action format ({why}). Send this output to Claude.")
                continue
            save_run_info(backend)
            run_experiment1(backend,
                            trials_per_cell=8 if light else EXP1_TRIALS_PER_CELL,
                            alt_trials_per_cell=0 if light else EXP1_ALT_TRIALS_PER_CELL)
            run_experiment2(backend, seeds=2 if light else EXP2_SEEDS)
            model_summary(backend.label)
        except Exception as e:
            print(f"Skipping {name} after an error: {e!r}")
        finally:
            RUN_DEADLINE = None
    WORKERS = 4
    print("\n" + "=" * 90 + "\nONE FIXED LLM MONITOR OVER EVERY MESSAGE\n" + "=" * 90, flush=True)
    try:
        if DRY_RUN:
            judge_all_messages(MockBackend(label="mock:monitor"))
        elif gpu:
            start_ollama(MONITOR_MODEL)
            judge_all_messages(OllamaBackend(MONITOR_MODEL))
        else:
            load_verdicts()
            print("No GPU here: the LLM monitor runs the next time you Run all on a T4.")
    except Exception as e:
        print(f"LLM monitor step failed: {e!r}")
        load_verdicts()
    print(f"\nAll runs finished in {(time.time() - t_start) / 60:.0f} minutes. Results follow below.")


# ===================== Experiment 2b only: the seeded swarm =====================
def probe_swarm_ok(backend, tries=3):
    """Ask one swarm agent for its first move a few times and check the replies are valid actions."""
    world = make_exp2_world(stable_seed("probe", RUN_TAG), "O0_none")
    prompt = agent_prompt(world, world["agents"][0])
    good = 0
    for i in range(tries):
        act = parse_json(backend.chat(prompt + " " * i, TEMPERATURE))
        good += bool(act) and act.get("action") in EXP2_ACTIONS
    return good >= 2, f"{good} of {tries} probe replies were valid actions"


def run_swarm_only():
    global WORKERS, RUN_DEADLINE
    gpu = DRY_RUN or has_gpu()
    if not gpu:
        print("NOTE: no GPU in this session, so the open models are skipped.\n"
              "For them: Runtime > Change runtime type > T4 GPU, then Run all again (finished work is kept).")
    t_start = time.time()
    for kind, name in MODELS:
        print("\n" + "=" * 90 + f"\nMODEL: {name}  ({kind})\n" + "=" * 90, flush=True)
        if kind == "ollama" and not gpu:
            print("Skipped: needs a GPU.")
            continue
        WORKERS = 2 if kind == "colab_gemini" else 6
        RUN_DEADLINE = time.time() + GEMINI_TIME_BUDGET_MIN * 60 if kind == "colab_gemini" else None
        try:
            backend = make_backend(kind, name)
            ok, why = probe_swarm_ok(backend)
            print("Probe:", why)
            if not ok:
                print(f"Skipping {name}: it is not following the action format. Send this output to Claude.")
                continue
            save_run_info(backend)
            eps = run_experiment2(backend)
            if eps:
                b = exp2_behaviour(eps)
                print(f"\nFirst look at {backend.label} (per episode; full analysis is further down):")
                print(b.groupby("condition")[["messages", "values_relayed", "got_needed_value", "found_key_uses",
                                              "proxy_fetches", "own_key_leaks", "found_key_leaks", "reports",
                                              "tasks_completed"]].mean().round(2).to_string())
        except Exception as e:
            print(f"Skipping {name} after an error: {e!r}")
        finally:
            RUN_DEADLINE = None
    WORKERS = 6
    print("\n" + "=" * 90 + "\nTHE SAME FIXED LLM MONITOR OVER EVERY NEW MESSAGE\n" + "=" * 90, flush=True)
    try:
        if DRY_RUN:
            judge_all_messages(MockBackend(label="mock:monitor"))
        elif gpu:
            start_ollama(MONITOR_MODEL, parallel=6)
            judge_all_messages(OllamaBackend(MONITOR_MODEL))
        else:
            load_verdicts()
            print("No GPU here: the LLM monitor runs the next time you Run all on a T4.")
    except Exception as e:
        print(f"LLM monitor step failed: {e!r}")
        load_verdicts()
    print(f"\nAll runs finished in {(time.time() - t_start) / 60:.0f} minutes. Results follow below.")
