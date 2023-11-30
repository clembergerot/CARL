# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/agents/00_SimpleConf.ipynb.

# %% auto 0
__all__ = ['SimpleConf']

# %% ../../nbs/agents/00_SimpleConf.ipynb 4
import numpy as np
import networkx as nx

# %% ../../nbs/agents/00_SimpleConf.ipynb 5
class SimpleConf(object):
    """
    Class for simple reinforcement learning (Rescorla-Wagner rule)
    with confirmation/disconfirmation bias.
    """

    def __init__(self, 
                 params: np.ndarray):  # agents' parameters
        
        self.N = np.shape(params)[0]  # number of agents
        self.M = 2  # number of options
        self.alphac = params[:, 0]   # confirmatory learning rates
        self.alphad = params[:, 1]   # disconfirmatory learning rates
        self.beta = params[:, 2]    # inverse temperatures

    def connect_agents_full(self):
        """Connects agents according to a fully connected graph."""
        return nx.complete_graph(self.N)

    def compute_softmax(self, Qtable):
        """Returns a probability table for all agents for all actions,
        from agents' Qtable."""
        beta = np.row_stack(self.beta)
        num = np.exp(beta*Qtable)  # numerator
        den = np.sum(num, axis=1)  # denominator
        return num/den[:, None]

    def choose(self, Ptable):
        """Computes chosen options from agents's probability table."""
        choices = np.zeros((np.shape(Ptable)[0]))  # 1 choice per agent
        rd = np.reshape(np.random.rand(len(choices)), (len(choices), 1))
        # a random number between 0 and 1 is attributed to each agent
        choices = np.sum(rd > np.cumsum(Ptable, axis=1), axis=1) # if 
        # random number is smaller than agent's probability of choosing 0,
        # then agent chooses 0
        choices = choices.astype(int)  # converts the choices to int values
        return choices
    
    def all_take_action(self, Qtable):
        """Computes all agents' choices from their Qtable.
        Combines `compute_softmax` and `choose`.
        """
        Ptable = self.compute_softmax(Qtable)  # converts Q-values to
        # policy via softmax function
        choices = self.choose(Ptable)  # choose an option according to
        # policy
        return choices
    
    def update_Qvalues(self, G_att, choices, payoffs, Qtable): 
        """Updates all agents' Q-values according to CARL."""
        Qs = np.einsum('ijk->ikj', np.reshape(np.repeat(Qtable, self.N), 
                                              (self.N, self.M, self.N)))
        Rs = np.einsum('ijk->kij', np.reshape(np.repeat(np.repeat(payoffs, 
                                                                  self.N), 
                                                        self.M), 
                                              (self.N, self.M, self.N)))
        # dimensions: own Q-values, options, others' actions
        deltas = Rs - Qs  # prediction errors
        alphac_cube = np.reshape(np.repeat(self.alphac, self.N*self.M), 
                                 (self.N, self.N, self.M))
        alphad_cube = np.reshape(np.repeat(self.alphad, self.N*self.M), 
                                 (self.N, self.N, self.M))
        # 3d matrices with only confirmatory alphas vs. disconfirmatory
        # alphas
        pos = deltas > 0  # mask that indicates where pred errors are 
        # positive
        ags = np.arange(0, self.N, 1)  # vector of agent indices
        # choice_mask selects all actions that have been taken
        choice_mask = np.zeros((self.N, self.N, self.M)).astype(bool)
        choice_mask[:, ags, choices] = True
        deltas[~choice_mask] = 0
        # own_mask selects actions per agent
        own_mask = np.zeros((self.N, self.N, self.M)).astype(bool)
        own_mask[ags, :, choices] = True
        # same_act selects actions similar to my actions
        same_act = choice_mask & own_mask
        # other_act selects actions different from mine
        other_act = choice_mask & ~own_mask
        same_pos = pos & same_act
        other_pos = pos & other_act
        same_neg = ~pos & same_act
        other_neg = ~pos & other_act
        # alphas determines which alpha to attribute to each pred error
        alphas = np.zeros((self.N, self.N, self.M))
        alphas[same_pos] = alphac_cube[same_pos]
        alphas[same_neg] = alphad_cube[same_neg]
        alphas[other_neg] = alphac_cube[other_neg]
        alphas[other_pos] = alphad_cube[other_pos] 
        # obs_mask selects actions that I observe
        obs_ij = np.asarray(nx.adjacency_matrix(G_att).todense()).astype(bool)
        obs_mask = np.reshape(np.repeat(obs_ij, self.M), (self.N, self.N, 
                                                          self.M))
        np.fill_diagonal(obs_ij, True)  # I observe my own actions
        obs_mask[:, :, 0] = obs_ij
        obs_mask[:, :, 1] = obs_ij
        deltas[~obs_mask] = 0  # cancelled pred errors from unobserved actions
        # update Q-values according to CARL model
        deltas *= alphas
        deltas_sum = np.sum(deltas, axis=1)
        Qtable += deltas_sum
        return Qtable
