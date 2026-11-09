# ===================== CONFIG: nothing to edit. Just Runtime > Run all. =====================
# Gap checks: Experiment 1c (key-only requests), an access-aware monitor, and Experiment 2b (seeded swarm).
# Experiment 1c reuses the main run's scenarios (tag v3); the swarm reuses its worlds. Finished work is skipped.
MODELS = [
    ("ollama", "qwen2.5:7b"),                     # Alibaba, open weights, on Colab's free T4 GPU
    ("ollama", "llama3.1:8b"),                    # Meta, open weights, on Colab's free T4 GPU
    ("colab_gemini", "google/gemini-2.5-flash"),  # Google, via Colab's free built-in Gemini (no API key)
]
MONITOR_MODEL = "qwen2.5:7b"     # the same fixed LLM monitor as the main run
GEMINI_TIME_BUDGET_MIN = 25
GEMINI_KEYONLY_MIN = 45          # without a GPU: Gemini key-only requests get this long (rate-limited free tier)
GEMINI_MONITOR_MIN = 35          # then Gemini as the access-aware monitor gets this long
GEMINI_MONITOR_LAUNDER, GEMINI_MONITOR_CLEAN = 100, 60   # its sample of main-run trials (plus every hand-over)
FORCE_NO_GPU = False             # True = behave as if there were no GPU (testing only)
GPU_ONLY = False                 # True = do nothing without a GPU (the account 2 copy)
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
EXP1_TRIALS_PER_CELL, EXP1_ALT_TRIALS_PER_CELL, EXP1_MAX_STEPS = 15, 5, 4
EXP1C_TRIALS_PER_CELL = 3 if QUICK else 15        # key-only: the same 15 scenarios x 2 requesters as the main run
EXP1C_GEMINI_TRIALS_PER_CELL = 2 if QUICK else 8
EXP1_ASK = "key"                 # the teammate asks ONLY for a key
EXP1_SCENARIO_TAG = "v3"         # the main run's scenarios, so every trial pairs with one from the main run
USE_LLM_MONITOR = False
STORE_PROMPTS = True
RUN_TAG = "v3k"                  # k = key-only requests; the swarm part switches to "v3s" itself
TAG = RUN_TAG + ("_quick" if QUICK else "")
BACKEND = "mock" if DRY_RUN else "auto"
OLLAMA_MODEL, GEMINI_MODEL = MODELS[0][1], MODELS[-1][1]

import os
RESULTS_DIR = ("/content/drive/MyDrive/canary_traps" if os.path.isdir("/content/drive/MyDrive")
               else os.path.abspath("canary_results"))
os.makedirs(RESULTS_DIR, exist_ok=True)
print("Results will be saved in:", RESULTS_DIR)
print(f"Models: {[m[1] for m in MODELS]} | QUICK={QUICK} | DRY_RUN={DRY_RUN}")
