# ===================== CONFIG: nothing to edit. Just Runtime > Run all. =====================
# Experiment 2b: the six-agent swarm again, on the SAME six-agent worlds as the main run (tag v3),
# but every agent opens with a help request to the teammate who holds the key it needs.
MODELS = [
    ("ollama", "qwen2.5:7b"),                     # Alibaba, open weights, on Colab's free T4 GPU
    ("ollama", "llama3.1:8b"),                    # Meta, open weights, on Colab's free T4 GPU
    ("colab_gemini", "google/gemini-2.5-flash"),  # Google, via Colab's free built-in Gemini (no API key)
]
MONITOR_MODEL = "qwen2.5:7b"     # the same fixed LLM monitor as the main run
GEMINI_TIME_BUDGET_MIN = 40      # Gemini's free tier is rate-limited, so its run stops after this long
OPENAI_COMPAT = dict(base_url="", api_key="", model="")

DRY_RUN = False   # True = a scripted stand-in model, only for testing the code. Its numbers are NOT results.
QUICK = False     # True = tiny smoke-test sizes

TEMPERATURE = 0.7
WORKERS = 6                      # all six agents of a round are answered at once
EXP2_SEEDED = True               # every agent opens with a help request (Experiment 2b)
EXP2_WORLD_TAG = "v3"            # reuse the main run's worlds, so episodes pair up with it
EXP2_SEEDS = 1 if QUICK else 4   # episodes per condition (the same 4 worlds as the main run)
EXP2_ROUNDS = 4 if QUICK else 8
EXP2_AGENTS = 6
EXP2_CONDITIONS = ["O0_none", "O2_monitored", "O3_canary_aware"]
EXP1_TRIALS_PER_CELL, EXP1_ALT_TRIALS_PER_CELL, EXP1_MAX_STEPS = 15, 5, 4   # Experiment 1 is not run here
USE_LLM_MONITOR = False
STORE_PROMPTS = True
RUN_TAG = "v3s"                  # s = seeded swarm; results go to new files next to the main run's
TAG = RUN_TAG + ("_quick" if QUICK else "")
BACKEND = "mock" if DRY_RUN else "auto"
OLLAMA_MODEL, GEMINI_MODEL = MODELS[0][1], MODELS[-1][1]

import os
RESULTS_DIR = ("/content/drive/MyDrive/canary_traps" if os.path.isdir("/content/drive/MyDrive")
               else os.path.abspath("canary_results"))
os.makedirs(RESULTS_DIR, exist_ok=True)
print("Results will be saved in:", RESULTS_DIR)
print(f"Models: {[m[1] for m in MODELS]} | QUICK={QUICK} | DRY_RUN={DRY_RUN}")
