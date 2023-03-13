# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/agents/00_SimpleConf.ipynb.

# %% auto 0
__all__ = ['SimpleConf']

# %% ../../nbs/agents/00_SimpleConf.ipynb 4
import numpy as np
import networkx as nx

# %% ../../nbs/agents/00_SimpleConf.ipynb 5
class SimpleConf(object):

    def __init__(self, params):
        self.N = np.shape(params)[0]   # number of agents
        self.M = 2  # number of options
        self.alphac = params[:, 0]   # confirmatory learning rates
        self.alphad = params[:, 1]   # disconfirmatory learning rates
        self.beta = params[:, 2]    # inverse temperatures

    def connect_agents_full(self):
        # all agents have full attention capacity
        return nx.complete_graph(self.N)

    def compute_softmax(self, Qtable):
        # returns a probability table for all agents for all actions
        beta = np.row_stack(self.beta)
        num = np.exp(beta*Qtable)  # numerator
        den = np.sum(num, axis=1)  # denominator
        return num/den[:, None]

    def choose(self, Ptable):
        # computes chosen options from probability table
        choices = np.zeros((np.shape(Ptable)[0]))  # 1 choice per agent
        rd = np.reshape(np.random.rand(len(choices)), (len(choices), 1))
        choices = np.sum(rd > np.cumsum(Ptable, axis=1), axis=1)
        choices = choices.astype(int)  # converts the choices to int values
        return choices

    def track_payoffs(self, agent, G_att, choices, payoffs):
        # tracks the choices and payoffs of oneself + neighbors
        obs_choices = [choices[agent]] + [
            choices[n] for n in list(G_att.neighbors(agent))]
        # observed choices
        obs_choices = list(dict.fromkeys(obs_choices))  # removes duplicates
        obs_payoffs = [payoffs[obs] for obs in obs_choices]  # lists
        # corresponding payoffs
        trackmat = np.column_stack((obs_choices, obs_payoffs))  # matches
        # tracked choices + payoffs in a matrix
        return trackmat

    def update_Qvalues_async(self, agent, G_att, choices, payoffs, Qtable):
        c = max(choices)
        delta_mat = np.zeros((self.N, c+1))
        delta_mat[agent, choices[agent]] = payoffs[agent] - Qtable[agent, choices[agent]]
        M = list(G_att.neighbors(agent))
        delta_mat[M, choices[M]] = payoffs[M] - Qtable[agent, choices[M]]
        j = choices[agent]
        delta_mat[:, j][delta_mat[:, j] > 0] *= self.alphac[agent]
        delta_mat[:, j][delta_mat[:, j] <= 0] *= self.alphad[agent]
        I = list(np.arange(0, c+1, 1))
        I.remove(j)
        delta_mat[:, I][delta_mat[:, I] > 0] *= self.alphad[agent]
        delta_mat[:, I][delta_mat[:, I] <= 0] *= self.alphac[agent]
        inc = np.sum(delta_mat, axis=0)
        Qtable[agent, :c+1] += inc
        return Qtable

    def update_Qvalues(self, agent, trackmat, Qtable):
        # updates Q-values according to a simple RW rule + asymmetric updating
        trackmat_int = trackmat.astype(int)  # used for indexing
        delta = trackmat[:, 1] - Qtable[agent, trackmat_int[:, 0]]  # all
        # prediction errors
        alpha = trackmat[:, 1] - Qtable[agent, trackmat_int[:, 0]]  # building
        # alpha from prediction errors
        alpha[alpha > 0] = self.alphad[agent]  # delta will be updated with
        # alphad if positive
        alpha[alpha <= 0] = self.alphac[agent]  # and with alphac if negative
        # this is reversed when choice is own choice
        if delta[0] >= 0:
            alpha[0] = self.alphac[agent]
        else:
            alpha[0] = self.alphad[agent]
        Qtable[agent, trackmat_int[:, 0]] += alpha * delta  # updates all
        # Q-values
        return Qtable
    
    # Allows to update Q-values for all agents without for loops
    def update_Qvalues_async2(self, G_att, choices, payoffs, Qtable): 
        Qs = np.einsum('ijk->ikj', np.reshape(np.repeat(Qtable, self.N), 
                                              (self.N, self.M, self.N)))
        Rs = np.einsum('ijk->kij', np.reshape(np.repeat(np.repeat(payoffs, 
                                                                  self.N), 
                                                        self.M), 
                                              (self.N, self.M, self.N)))
        deltas = Rs - Qs
        # TODO: the cubes could be built at the beginning of the experiment
        alphac_cube = np.reshape(np.repeat(self.alphac, self.N*self.M), 
                                 (self.N, self.N, self.M))
        alphad_cube = np.reshape(np.repeat(self.alphad, self.N*self.M), 
                                 (self.N, self.N, self.M))
        pos = deltas > 0
        ags = np.arange(0, self.N, 1)
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
        alphas = np.zeros((self.N, self.N, self.M))
        alphas[same_pos] = alphac_cube[same_pos]
        alphas[same_neg] = alphad_cube[same_neg]
        alphas[other_neg] = alphac_cube[other_neg]
        alphas[other_pos] = alphad_cube[other_pos] 
        # obs_mask selects actions that I observe; 
        # TODO: could be implemented at the beginning of the experiment
        obs_ij = np.asarray(nx.adjacency_matrix(G_att).todense()).astype(bool)
        obs_mask = np.reshape(np.repeat(obs_ij, self.M), (self.N, self.N, 
                                                          self.M))
        np.fill_diagonal(obs_ij, True)
        obs_mask[:, :, 0] = obs_ij
        obs_mask[:, :, 1] = obs_ij
        deltas[~obs_mask] = 0
        deltas *= alphas
        deltas_sum = np.sum(deltas, axis=1)
        Qtable += deltas_sum
        return Qtable


    def all_take_action(self, Qtable):
        # all agents choose an option according to their Q-tables
        Ptable = self.compute_softmax(Qtable)
        choices = self.choose(Ptable)
        return choices

    def all_update_Q(self, Qtable, G_att, payoffs, choices):
        # all agents update their Q-values
        for agent in range(self.N):
            trackmat = self.track_payoffs(agent, G_att, choices, payoffs)
            Qtable = self.update_Qvalues(agent, trackmat, Qtable)
        return Qtable

    def all_update_Q_async(self, Qtable, G_att, payoffs, choices):
        # all agents update their Q-values
        for agent in range(self.N):
            Qtable = self.update_Qvalues_async(agent, G_att, choices, payoffs,
            Qtable)
        return Qtable
