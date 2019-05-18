import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.contrib.distributions import MultivariateNormalDiag


class GaussianActor(tf.keras.Model):
    LOG_SIG_CAP_MAX = 2
    LOG_SIG_CAP_MIN = -20
    EPS = 1e-6

    def __init__(self, state_dim, action_dim, max_action, units=[256, 256],
                 name='GaussianPolicy'):
        super().__init__(name=name)

        self.l1 = Dense(units[0], name="L1", activation='relu')
        self.l2 = Dense(units[1], name="L2", activation='relu')
        self.out_mean = Dense(action_dim, name="L_mean")
        self.out_sigma = Dense(action_dim, name="L_sigma")

        self._max_action = max_action

        dummy_state = tf.constant(np.zeros(shape=[1, state_dim], dtype=np.float64))
        self(dummy_state)

    def _compute_dist(self, states):
        features = self.l1(states)
        features = self.l2(features)

        mu = self.out_mean(features)
        log_sigma = self.out_sigma(features)
        log_sigma = tf.clip_by_value(log_sigma, self.LOG_SIG_CAP_MIN, self.LOG_SIG_CAP_MAX)

        return MultivariateNormalDiag(loc=mu, scale_diag=tf.exp(log_sigma))

    def call(self, states):
        dist = self._compute_dist(states)
        raw_actions = dist.sample()
        log_pis = dist.log_prob(raw_actions)

        actions = tf.tanh(raw_actions)

        # for variable replacement
        diff = tf.reduce_sum(tf.log(1. - actions ** 2 + self.EPS), axis=1)
        log_pis -= diff

        actions = actions * self._max_action
        return actions, log_pis

    def mean_action(self, states):
        dist = self._compute_dist(states)
        raw_actions = dist.mean()
        actions = tf.tanh(raw_actions) * self._max_action

        return actions
