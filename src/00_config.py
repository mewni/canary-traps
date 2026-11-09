# ===================== CONFIG: nothing to edit. Just Runtime > Run all. =====================
# Models, run one after another. Every results cell compares all of them.
MODELS = [
    ("ollama", "qwen2.5:7b"),                     # Alibaba, open weights, on Colab's free T4 GPU
    ("ollama", "llama3.1:8b"),                    # Meta, open weights, on Colab's free T4 GPU
    ("colab_gemini", "google/gemini-2.5-flash"),  # Google, via Colab's free built-in Gemini (no API key)
]
MONITOR_MODEL = "qwen2.5:7b"     # ONE fixed LLM monitor reads every message from every model
GEMINI_TIME_BUDGET_MIN = 60      # Gemini's free tier is rate-limited, so its run stops after this long
OPENAI_COMPAT = dict(base_url="", api_key="", model="")   # only for ("openai_compat", ...) entries

DRY_RUN = False   # True = a scripted stand-in model, only for testing the code. Its numbers are NOT results.
QUICK = False     # True = tiny smoke-test sizes (about 15 minutes for everything)

TEMPERATURE = 0.7
WORKERS = 4
EXP1_TRIALS_PER_CELL = 3 if QUICK else 15      # cells = 4 oversight x 2 credential sources x 2 requesters
EXP1_ALT_TRIALS_PER_CELL = 1 if QUICK else 5   # same scenarios, second wording of the rules (robustness)
EXP1_MAX_STEPS = 4                             # actions the key holder may take per trial
EXP2_SEEDS = 1 if QUICK else 4                 # swarm episodes per condition
EXP2_ROUNDS = 4 if QUICK else 8
EXP2_AGENTS = 6
EXP2_CONDITIONS = ["O0_none", "O2_monitored", "O3_canary_aware"]
USE_LLM_MONITOR = False    # the fixed LLM monitor runs once at the end over all saved messages
STORE_PROMPTS = True       # keep full prompts in the logs so anyone can rerun and audit them
RUN_TAG = "v3"
TAG = RUN_TAG + ("_quick" if QUICK else "")
BACKEND = "mock" if DRY_RUN else "auto"
OLLAMA_MODEL, GEMINI_MODEL = MODELS[0][1], MODELS[-1][1]

import os
RESULTS_DIR = ("/content/drive/MyDrive/canary_traps" if os.path.isdir("/content/drive/MyDrive")
               else os.path.abspath("canary_results"))
os.makedirs(RESULTS_DIR, exist_ok=True)
print("Results will be saved in:", RESULTS_DIR)
print(f"Models: {[m[1] for m in MODELS]} | QUICK={QUICK} | DRY_RUN={DRY_RUN}")
