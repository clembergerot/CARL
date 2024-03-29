# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/envs/10_TwoArmedBandit.ipynb.

# %% auto 0
__all__ = ['TwoArmedBandit']

# %% ../../nbs/envs/10_TwoArmedBandit.ipynb 4
import numpy as np

# %% ../../nbs/envs/10_TwoArmedBandit.ipynb 5
class TwoArmedBandit(object):
    """
    Class for defining a simple two-armed bandit task.
    """

    def __init__(self, p_0, p_1, rew, pun):
        self.M = 2    # number of arms
        self.rew = rew    # reward value (usually 1)
        self.pun = pun    # punishment value (usually 0 or -1)
        self.probs = [p_0, p_1]    # probability that option 0 (resp. option 1)
        # yields a reward

    def return_payoffs(self, choices):
        """Returns reward with probability p and punishment with probability
        (1-p)."""
        payoffs = np.ones((len(choices)))
        probs_ar = np.array(self.probs)  # create array of probs
        choices_li = list(choices)  # create list of choices
        probs_now = probs_ar[choices_li]  # returns prob associated
        # with each choice
        rd = np.random.rand(len(choices))  # returns random numbers
        # between 0 and 1
        mask = rd <= probs_now  # if random number is smaller than prob,
        # arm yields reward
        payoffs[mask] = payoffs[mask] * self.rew  # attribute reward
        payoffs[~mask] = payoffs[~mask] * self.pun  # attribute punishment
        return payoffs

    def reversal_occurs(self):
        """Introduces a reversal in reward probabilities."""
        self.probs = self.probs[::-1]

    def output_probs(self):
        """Outputs np array of probabilities associated to each option."""
        return np.array(self.probs)
