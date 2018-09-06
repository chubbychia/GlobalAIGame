import numpy as np
from utils.poker import Card

class Player(object):
    
    def __init__(self, player_name, state_size, action_size):
        self.player_name = player_name
        self.state_size = state_size
        self.action_size = action_size
        
        self.state = np.zeros(self.state_size)
        self.action = np.zeros(self.action_size)
        self.reward = 0
        self.states = []
        self.rewards = []
        self.actions = []
        self.scores = []
    def set_AH_exposed(self):
        self.state[52] = 1
    
    def set_TC_eaten(self):
        self.state[53] = 1

    def set_hand_cards(self, hands): # list 
        for h in hands:
            h_card = Card(h)
            self.state[13 * h_card.suit_index + h_card.value - 2] = 1
    
    def set_turn_card(self, out): # Card
        self.state[13 * out.suit_index + out.value - 2] = -1

    def set_others_turn_card(self, used): # Card
        self.state[13 * used.suit_index + used.value - 2] = 2

    def set_dumped_card(self): # Card
        for idx in range(self.state_size):
            if self.state[idx] == 2:
                self.state[idx] = -1
    
    def set_score_cards(self, scores): # list
        for s in scores:
            s_card = Card(s)
            self.state[13 * s_card.suit_index + s_card.value - 2] = 3
    
    def set_others_score_cards(self, oppo_label, scores): # list
        for s in scores:
            s_card = Card(s)
            self.state[13 * s_card.suit_index + s_card.value - 2] = oppo_label # 4 / 5 / 6 

    def set_action(self, stategy): # int: stategy no.
        self.action=np.zeros(self.action_size) 
        self.action[stategy] = 1

    def set_reward(self, round_score): # int. Accumulative by our calculation
        if self.scores:
            r = round_score - self.scores[-1]
        else:
            r = round_score
        self.scores.append(round_score)
        self.reward = r

    def reset_sample(self):
        self.state = np.zeros(self.state_size) #54
        self.action = np.zeros(self.action_size) #52
        self.reward = 0
        self.total_rewards = 0
        self.states = []
        self.rewards = []
        self.actions = []
        self.scores = []

    # save <s, a ,r> of each step
    # this is used for calculating discounted rewards
    def memorize(self):
        self.states.append(self.state.copy())
        self.actions.append(self.action)
        self.rewards.append(self.reward)
    
   
   