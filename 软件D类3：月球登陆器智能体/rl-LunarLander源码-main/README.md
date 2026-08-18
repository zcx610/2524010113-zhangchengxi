# LunarLander PPO 基于强化学习控制的月球登陆器智能体

本项目基于 Gymnasium `LunarLander-v3` 和 Stable-Baselines3 PPO，用于训练、评估和可视化登月舱控制智能体。

工程保留两套环境入口：

```text
base  原始 LunarLander 训练/评测环境
real  仿真实机环境，在 base 上加入传感器噪声、控制延迟、随机阵风和最终评分
```

## 目录结构

```text
agent_ppo/conf       环境、奖励、模型、PPO 和 real 参数
agent_ppo/feature    奖励处理与 real 环境封装
agent_ppo/model      actor-critic 网络结构
agent_ppo/algorithm  PPO 算法封装
agent_ppo/workflow   环境创建、训练、评估流程

train_base.py        base 训练入口
evaluate_base.py     base 测评入口
train_real.py        real 训练入口
evaluate_real.py     real 测评入口
dashboard.py         网页端训练、测评和可视化入口
```

## 安装

```powershell
conda activate rl-maze
python -m pip install -r requirements.txt
```

`requirements.txt` 默认安装 CPU 版 PyTorch，适合先确认工程能正常运行。

如果 Box2D 安装失败，可以先安装 `swig`：

```powershell
python -m pip install swig
python -m pip install "gymnasium[box2d]"
```

如果需要 GPU 训练，请根据自己的显卡驱动和 CUDA 环境到 PyTorch 官网选择合适的安装命令：

```text
https://pytorch.org/get-started/locally/
```

推荐使用 `torch>=2.8,<3.0`，并保持 `stable-baselines3>=2.3,<3.0`。不要直接复制固定 CUDA 版本命令，除非确认它和本机驱动匹配。

GPU 版安装完成后可以检查：

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

## 网页端训练与测评

项目以本地 Web Dashboard 作为唯一可视化界面，适合在浏览器中进行训练、测评、模型选择和测评回放。网页端不会改写 PPO 算法，仍然复用现有训练与测评流程。

首次使用先构建前端：

```powershell
cd dashboard/frontend
npm install
npm run build
cd ../..
```

启动网页端：

```powershell
python dashboard.py
```

浏览器打开：

```text
http://127.0.0.1:7860
```

网页端包含两个主界面：

```text
训练界面：选择 base/real、CPU/GPU、训练轮数、并行环境数，并查看训练曲线。
测评界面：自动识别模型文件，选择 CPU/GPU、测评回合数、best_model.zip，并查看大屏测评回放和测评曲线。
```

启动训练或测评时，界面会确认当前环境和设备。开启测评后会自动播放对应模型的回放；切换到其他模型会中断当前回放。

## 任务说明

智能体控制登月舱降落到两个旗帜之间的着陆区。

观测是 8 维连续状态：

```text
x, y, x_velocity, y_velocity, angle, angular_velocity,
left_leg_contact, right_leg_contact
```

动作是 4 个离散动作：

```text
0 不喷火
1 左侧姿态发动机
2 主发动机
3 右侧姿态发动机
```

base 测评中，一局累计回报 `episode_return >= 200` 记为达到 LunarLander 常用通过标准。

## 命令行训练与测评

命令行入口适合快速训练、批量实验和在终端中复现实验结果。`--device` 可选 `cpu`、`cuda` 或 `auto`；如果本机没有可用 CUDA，请使用 `cpu`。

### Base 环境

训练：

```powershell
python train_base.py --device cpu
```

测评：

```powershell
python evaluate_base.py --episodes 20 --device cpu
```

短训练验证：

```powershell
python train_base.py --timesteps 256 --n-envs 1 --device cpu
```

### Real 环境

real 环境封装在：

```text
agent_ppo/feature/real_env.py
```

当前 real 环境包含：

```text
观测高斯噪声        REAL_OBS_NOISE_STD = 0.10
控制延迟            REAL_ACTION_DELAY_STEPS = 8
默认延迟动作        REAL_DEFAULT_ACTION = 0
阵风触发概率        REAL_GUST_PROBABILITY = 0.18
阵风水平力标准差    REAL_GUST_FORCE_X_STD = 3.0
阵风垂直力标准差    REAL_GUST_FORCE_Y_STD = 1.0
阵风持续帧数        REAL_GUST_DURATION_MIN = 8, REAL_GUST_DURATION_MAX = 32
```

训练：

```powershell
python train_real.py --device cpu
```

测评：

```powershell
python evaluate_real.py --episodes 20 --device cpu
```

短训练验证：

```powershell
python train_real.py --timesteps 256 --n-envs 1 --device cpu
```

## Real 最终评分

real 测评会额外输出最终评分：

```text
final_score = (0.2 * fuel_score + 0.4 * precision_score + 0.4 * stability_score) * completion_rate
```

分项含义：

```text
fuel_score       燃料消耗分，主发动机和侧发动机使用越少越高
precision_score  定位精准度分，越靠近目标中心越高
stability_score  机体平稳度分，角度、角速度、水平速度越小越高
completion_rate  完成率，满足落地接触、居中、姿态条件记为 1，否则为 0
```

评分参数在：

```text
agent_ppo/conf/conf.py
```

## 推荐开发流程

1. 激活环境并安装依赖：

```powershell
conda activate rl-maze
python -m pip install -r requirements.txt
```

2. 做一次短训练验证：

```powershell
python train_base.py --timesteps 256 --n-envs 1 --device cpu
```

3. 构建并启动网页端，在浏览器中继续训练、测评和回放：

```powershell
cd dashboard/frontend
npm install
npm run build
cd ../..
python dashboard.py
```

4. 修改前端时使用开发服务器：

```powershell
python dashboard.py --no-browser
cd dashboard/frontend
npm run dev
```

5. 修改算法、奖励或 real 环境后，优先跑短训练，再用网页端测评回放检查行为是否符合预期。

## 二次开发入口

奖励设计：

```text
agent_ppo/feature/reward_process.py
agent_ppo/conf/conf.py
```

real 环境设计：

```text
agent_ppo/feature/real_env.py
agent_ppo/workflow/env_factory.py
agent_ppo/conf/conf.py
```

网络结构：

```text
agent_ppo/model/actor_critic.py
agent_ppo/conf/conf.py
```

PPO 算法与训练参数：

```text
agent_ppo/algorithm/algorithm_ppo.py
agent_ppo/conf/ppo_lunarlander.yml
agent_ppo/conf/train_env_conf.toml
```

## 常见说明

短训练命令只用于验证训练流程能正常启动，不代表模型效果。

如果运行时看到 `gym_minigrid` 或旧 `gym` 警告，通常是当前 conda 环境残留旧包，不是本工程主线在使用它们。可以清理：

```powershell
python -m pip uninstall gym-minigrid gym -y
```
