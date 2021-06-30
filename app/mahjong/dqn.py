import random

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tf_agents.agents.dqn import dqn_agent
from tf_agents.environments import py_environment, tf_py_environment
from tf_agents.networks import network
from tf_agents.policies import policy_saver
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.specs import array_spec
from tf_agents.trajectories import policy_step as ps
from tf_agents.trajectories import time_step as ts
from tf_agents.trajectories import trajectory
from tf_agents.utils import common, nest_utils

from .const import Const
from .game import Game
from .kago import Kago


class DQN(Kago):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'dqn'


# シミュレータクラスの設定
class Env(py_environment.PyEnvironment):
    def __init__(self):
        super(Env, self).__init__()
        self._observation_spec = array_spec.BoundedArraySpec(
            shape=(34, 4, 17), dtype=np.float32, minimum=0, maximum=1
        )
        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32, minimum=0, maximum=33
        )
        self.count = 0
        self.stats = [0] * 4

        self._reset()

    def observation_spec(self):
        return self._observation_spec

    def action_spec(self):
        return self._action_spec

    # 初期化
    def _reset(self):
        print(self.count, '試合目')
        self.count += 1

        self.game = Game()
        self.player = DQN(id=0, game=self.game)
        self.game.start_game(mode=Const.AUTO_MODE, player=self.player)
        self.game.start_kyoku()

        self.reward = 0
        self.game_end = False

        while self.game.next():
            pass

        time_step = ts.restart(self.board())
        return nest_utils.batch_nested_array(time_step)

    # 行動による状態変化
    def _step(self, action):
        action = nest_utils.unbatch_nested_array(action)
        score = self.score()
        dahai = self.dahai(action)
        # print(action, dahai, self.player.tehai)

        self.reward = 0
        self.game.dahai(dahai, self.player)
        while self.game.next():
            pass

        if self.game.state in [Const.RYUKYOKU_STATE, Const.AGARI_STATE]:
            self.reward = self.score() - score
            self.game_end = True
            time_step = ts.termination(self.board(), reward=0)
        elif self.game.state == Const.SYUKYOKU_STATE:
            self.reward = [90, 45, 0, -180][self.rank()] * 1000
            self.game_end = True
            time_step = ts.termination(self.board(), reward=0)
        else:
            time_step = ts.transition(self.board(), reward=0, discount=1)

        return nest_utils.batch_nested_array(time_step)

    def board(self):
        return self.player.make_input().reshape(34, 4, 17)

    def score(self):
        return self.game.scores[self.player.position]

    def dahai(self, action):
        for p in self.player.tehai:
            if p // 4 == action and self.player.can_dahai(p):
                return p

        return None

    def rank(self):
        myscore = self.game.scores[self.player.position]
        scores = sorted(self.game.scores, reverse=True)
        self.stats[scores.index(myscore)] += 1
        print(scores, myscore, scores.index(myscore))
        return scores.index(myscore)

    def random_action(self):
        return self.player.decide_dahai() // 4

    @property
    def batched(self):
        return True

    @property
    def batch_size(self):
        return 1


# ネットワーククラスの設定
class MyQNetwork(network.Network):
    def __init__(self, observation_spec, action_spec, name='QNetwork'):
        super(MyQNetwork, self).__init__(
            input_tensor_spec=observation_spec,
            state_spec=(),
            name=name
        )
        n_action = action_spec.maximum - action_spec.minimum + 1
        self.model = models.Sequential([
            layers.Conv2D(100, (5, 2), activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Conv2D(100, (5, 2), activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Conv2D(100, (5, 2), activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Flatten(),
            layers.Dense(300, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(n_action, activation='softmax'),
        ])

    def call(self, observation, step_type=None, network_state=(), training=True):
        observation = tf.cast(observation, tf.float32)
        actions = self.model(observation, training=training)
        return actions, network_state


def random_policy_step(random_action_function):
    random_act = random_action_function()
    return ps.PolicyStep(
        action=tf.constant([random_act]),
        state=(),
        info=()
    )


def main():
    print(' === MAIN ===')

    # 環境の設定
    env_py = Env()
    env = tf_py_environment.TFPyEnvironment(env_py)
    print(' === ENV LOADED === ')

    # ネットワークの設定
    primary_network = MyQNetwork(env.observation_spec(), env.action_spec())
    print(' === NETWORK LOADED === ')

    # エージェントの設定
    n_step_update = 1
    agent = dqn_agent.DqnAgent(
        env.time_step_spec(),
        env.action_spec(),
        q_network=primary_network,
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        n_step_update=n_step_update,
        target_update_period=100,
        gamma=0.99,
        train_step_counter=tf.Variable(0),
        epsilon_greedy=0.0
    )
    agent.initialize()
    agent.train = common.function(agent.train)
    print(' === AGENT LOADED === ')

    # 行動の設定
    policy = agent.collect_policy
    print(' === POLICY LOADED === ')

    # データの保存の設定
    replay_buffer = tf_uniform_replay_buffer.TFUniformReplayBuffer(
        data_spec=agent.collect_data_spec,
        batch_size=env.batch_size,
        max_length=10**6
    )
    dataset = replay_buffer.as_dataset(
        num_parallel_calls=tf.data.experimental.AUTOTUNE,
        sample_batch_size=16,
        num_steps=n_step_update + 1
    ).prefetch(tf.data.experimental.AUTOTUNE)
    iterator = iter(dataset)
    print(' === BUFFER LOADED === ')

    # ポリシーの保存設定
    tf_policy_saver = policy_saver.PolicySaver(policy=agent.policy)
    print(' === SAVER LOADED === ')

    # 学習
    num_episodes = 200
    decay_episodes = 70
    epsilon = np.concatenate([np.linspace(start=1.0, stop=1.0, num=decay_episodes),
                              0.1 * np.ones(shape=(num_episodes - decay_episodes,)), ], 0)

    action_step_counter = 0
    replay_start_size = 100

    episode_average_loss = []

    for episode in range(1, num_episodes + 1):
        policy._epsilon = epsilon[episode - 1]  # ε-greedy法用
        env.reset()

        previous_time_step = None
        previous_policy_step = None

        while not env.game_end:  # ゲームが終わるまで繰り返す
            current_time_step = env.current_time_step()
            if previous_time_step is None:  # 1手目は学習データを作らない
                pass
            else:
                previous_step_reward = tf.constant([env.reward, ], dtype=tf.float32)
                current_time_step = current_time_step._replace(reward=previous_step_reward)

                traj = trajectory.from_transition(
                    previous_time_step, previous_policy_step, current_time_step)  # データの生成
                replay_buffer.add_batch(traj)  # データの保存

                if action_step_counter >= 2 * replay_start_size:  # 事前データ作成用
                    experience, _ = next(iterator)
                    loss_info = agent.train(experience=experience)  # 学習
                    episode_average_loss.append(loss_info.loss.numpy())
                else:
                    action_step_counter += 1
            if random.random() < epsilon[episode - 1]:  # ε-greedy法によるランダム動作
                policy_step = random_policy_step(env.random_action)  # 設定したランダムポリシー
            else:
                policy_step = policy.action(current_time_step)  # 状態から行動の決定

            previous_time_step = current_time_step  # 1つ前の状態の保存
            previous_policy_step = policy_step  # 1つ前の行動の保存

            env.step(policy_step.action)  # 石を配置

        print(env.stats)

        # 学習の進捗表示 (100エピソードごと)
        if episode % 100 == 0:
            print('==== Episode {}: rank: {} ===='.format(
                episode, env.stats
            ))
            episode_average_loss = []

        if episode % (num_episodes // 10) == 0:
            tf_policy_saver.save(f"policy_{episode}")


if __name__ == "__main__":
    main()
