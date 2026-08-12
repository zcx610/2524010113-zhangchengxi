import random
import numpy as np
import matplotlib.pyplot as plt
# =========================
# 井字棋环境
# =========================
class TicTacToeEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [0] * 9  # 0=空, 1=玩家1(X), 2=玩家2(O)
        self.done = False
        self.winner = None
        return tuple(self.board)

    def get_legal_actions(self):
        return [i for i, v in enumerate(self.board) if v == 0]

    def step(self, action, player):
        if self.board[action] != 0:
            raise ValueError("非法落子")

        self.board[action] = player

        if self._check_win(player):
            self.done = True
            self.winner = player
        elif len(self.get_legal_actions()) == 0:
            self.done = True
            self.winner = 0  # 平局

        return tuple(self.board), self.done

    def _check_win(self, player):
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        return any(all(self.board[i] == player for i in line) for line in wins)
# =========================
# Q-Learning 智能体
# =========================
class QAgent:
    def __init__(self, player, epsilon=0.3, alpha=0.1, gamma=0.9):
        self.player = player
        self.q_table = {}
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma

    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state, legal_actions):
        if random.random() < self.epsilon:
            return random.choice(legal_actions)

        q_values = [self.get_q(state, a) for a in legal_actions]
        max_q = max(q_values)
        best_actions = [a for a, q in zip(legal_actions, q_values) if q == max_q]
        return random.choice(best_actions)

    def update(self, state, action, reward, next_state, next_legal_actions):
        next_max_q = max(
            [self.get_q(next_state, a) for a in next_legal_actions],
            default=0.0
        )
        key = (state, action)
        old_q = self.get_q(state, action)
        new_q = old_q + self.alpha * (
            reward + self.gamma * next_max_q - old_q
        )
        self.q_table[key] = new_q


# =========================
# 奖励函数
# =========================
def get_reward(env, player):
    if not env.done:
        return -0.01          # 鼓励尽快结束
    if env.winner == player:
        return 1.0
    elif env.winner == 0:
        return 0.0
    else:
        return -1.0


# =========================
# 训练过程
# =========================
def train():
    env = TicTacToeEnv()
    agent1 = QAgent(player=1, epsilon=0.3)
    agent2 = QAgent(player=2, epsilon=0.3)

    episodes = 20000
    win_history = []

    for ep in range(episodes):
        state = env.reset()
        agents = [agent1, agent2]
        turn = 0

        while not env.done:
            agent = agents[turn]
            legal_actions = env.get_legal_actions()
            action = agent.choose_action(state, legal_actions)
            next_state, _ = env.step(action, agent.player)

            reward = get_reward(env, agent.player)
            next_legal = env.get_legal_actions()

            agent.update(
                state, action, reward,
                next_state, next_legal
            )

            state = next_state
            turn ^= 1

        win_history.append(env.winner == 1)

        # ε 衰减
        agent1.epsilon *= 0.9999
        agent2.epsilon *= 0.9999

    return agent1, agent2, win_history


# =========================
# 训练曲线
# =========================
def plot_training_curve(win_history):
    window = 500
    avg_win = [
        np.mean(win_history[max(0, i - window):i])
        for i in range(1, len(win_history))
    ]

    plt.figure(figsize=(8, 4))
    plt.plot(avg_win)
    plt.xlabel("Episode")
    plt.ylabel("Win Rate (Player X)")
    plt.title("Tic-Tac-Toe Q-Learning Training Curve")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# =========================
# 下棋演示
# =========================
def print_board(board):
    sym = [" ", "X", "O"]
    for i in range(3):
        print(" {} | {} | {} ".format(*[sym[board[j]] for j in range(i*3, i*3+3)]))
        if i < 2:
            print("-----------")


def play_demo(agent1, agent2):
    env = TicTacToeEnv()
    state = env.reset()

    agent1.epsilon = 0
    agent2.epsilon = 0

    agents = [agent1, agent2]
    turn = 0

    print("\n=== Demo Game ===")
    while not env.done:
        print_board(env.board)
        print()
        agent = agents[turn]
        action = agent.choose_action(state, env.get_legal_actions())
        state, _ = env.step(action, agent.player)
        turn ^= 1

    print_board(env.board)
    if env.winner == 0:
        print("结果：平局")
    else:
        print(f"结果：{'X' if env.winner == 1 else 'O'} 获胜")


# =========================
# 主程序入口
# =========================
if __name__ == "__main__":
    agent1, agent2, win_history = train()
    plot_training_curve(win_history)
    play_demo(agent1, agent2)