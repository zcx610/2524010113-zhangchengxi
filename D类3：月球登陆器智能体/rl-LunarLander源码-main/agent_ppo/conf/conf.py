from __future__ import annotations

from pathlib import Path


class Config:
    ROOT_DIR = Path(__file__).resolve().parents[2]

    ALGO = "ppo"
    ENV_ID = "LunarLander-v3"
    ORG = "sb3"
    LOG_FOLDER = ROOT_DIR / "logs"

    # LunarLander PPO training setup, aligned with RL Zoo defaults.
    POLICY = "MlpPolicy"
    ENV_WRAPPERS = [
        "agent_ppo.feature.reward_process.LunarLanderRewardWrapper",
    ]
    N_TIMESTEPS = 2_000_000
    N_ENVS = 16
    N_STEPS = 4096
    BATCH_SIZE = 256
    N_EPOCHS = 10
    LEARNING_RATE = 0.0003
    GAMMA = 0.995
    GAE_LAMBDA = 0.95
    CLIP_RANGE = 0.2
    ENT_COEF = 0.01
    VF_COEF = 0.3
    MAX_GRAD_NORM = 0.5
    NORMALIZE = False
    NORM_OBS = False
    NORM_REWARD = False
    TRAIN_SEED = 0
    EVAL_SEED = 10_000
    EVAL_FREQ_STEPS = 25_000
    N_EVAL_EPISODES = 20
    EVAL_SUCCESS_REWARD = 200.0

    # Real environment simulation: noisy sensors and delayed control.
    REAL_OBS_NOISE_STD = 0.10
    REAL_ACTION_DELAY_STEPS = 8
    REAL_DEFAULT_ACTION = 0
    REAL_NOISE_SEED_OFFSET = 2026
    REAL_GUST_PROBABILITY = 0.18
    REAL_GUST_FORCE_X_STD = 3.0
    REAL_GUST_FORCE_Y_STD = 1.0
    REAL_GUST_DURATION_MIN = 8
    REAL_GUST_DURATION_MAX = 32

    # Final real score: (20% fuel + 40% precision + 40% stability) * completion.
    REAL_SCORE_FUEL_WEIGHT = 0.20
    REAL_SCORE_PRECISION_WEIGHT = 0.40
    REAL_SCORE_STABILITY_WEIGHT = 0.40
    REAL_SIDE_ENGINE_FUEL_RATIO = 0.25
    REAL_PRECISION_MAX_ERROR = 1.5
    REAL_STABILITY_MAX_ERROR = 1.5
    REAL_STABILITY_ANGLE_WEIGHT = 1.0
    REAL_STABILITY_ANGULAR_VEL_WEIGHT = 0.5
    REAL_STABILITY_HORIZONTAL_VEL_WEIGHT = 0.5
    REAL_COMPLETION_X_THRESHOLD = 0.25
    REAL_COMPLETION_ANGLE_THRESHOLD = 0.35

    # Reward design, aligned with Gymnasium LunarLander original reward.
    REWARD_DISTANCE_WEIGHT = -100.0
    REWARD_VELOCITY_WEIGHT = -100.0
    REWARD_ANGLE_WEIGHT = -100.0
    REWARD_LEG_CONTACT_BONUS = 10.0
    REWARD_MAIN_ENGINE_COST = 0.30
    REWARD_SIDE_ENGINE_COST = 0.03
    REWARD_CRASH = -100.0
    REWARD_LANDING = 100.0
    REWARD_SCALE = 1.0
    REWARD_BIAS = 0.0

    # LunarLander observation/action layout.
    OBS_DIM = 8
    STATE_SHAPE = (OBS_DIM,)
    STATE_DIM = OBS_DIM
    ACTION_NUM = 4
    VALUE_NUM = 1

    # Stable-Baselines3 MlpPolicy defaults for PPO.
    ACTOR_HIDDEN_LAYERS = [64, 64]
    CRITIC_HIDDEN_LAYERS = [64, 64]
    ACTIVATION_FN = "nn.Tanh"
    ORTHO_INIT = True

    HYPERPARAMS_FILE = ROOT_DIR / "agent_ppo" / "conf" / "ppo_lunarlander.yml"
    TRAIN_CONF_FILE = ROOT_DIR / "agent_ppo" / "conf" / "train_env_conf.toml"

    # =========================================================
    # Real environment reward tuning (custom action mapping)
    # main engine = 2, side engines = {1, 3}
    # =========================================================

    REWARD_MODE = "base"
    IS_REAL = False

    REWARD_REAL_DISTANCE_WEIGHT = -25.0
    REWARD_REAL_VELOCITY_WEIGHT = -25.0
    REWARD_REAL_ANGLE_WEIGHT = -25.0
    REWARD_REAL_ANGLE_VEL_WEIGHT = -0.05
    REWARD_REAL_LEG_CONTACT_BONUS = 6.0
    REWARD_REAL_MAIN_ENGINE_COST = 0.10
    REWARD_REAL_SIDE_ENGINE_COST = 0.015
    REWARD_REAL_LANDING = 80.0
    REWARD_REAL_CRASH = -80.0
    REWARD_REAL_ACTION_SMOOTH_WEIGHT = 0.01
    REWARD_REAL_TIME_COST = -0.001
    REWARD_REAL_SCALE = 1.0
    REWARD_REAL_BIAS = 0.0