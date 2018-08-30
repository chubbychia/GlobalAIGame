import numpy as np
from utils.poker import Card

class Player(object):
    
    def __init__(self, player_name, state_size, action_size):
        self.player_name = player_name
        self.state_size = state_size
        self.action_size = action_size
        
        self.state = np.zeros(self.state_size) #54
        self.action = np.zeros(self.action_size) #52
        self.reward = 0
        self.total_rewards = 0
        self.states = []
        self.rewards = []
        self.actions = []
       
    def set_AH_exposed(self):
        self.state[52] = 1
    
    def set_TC_eaten(self):
        self.state[53] = 1

    def set_hand_cards(self, hands): # list 
        for h in hands:
            h_card = Card(h)
            self.state[13 * h_card.suit_index + h_card.value - 2] = 1
    
    def set_hand_out_card(self, out): # Card
        self.state[13 * out.suit_index + out.value - 2] = -1

    def set_used_card(self, used): # Card
        self.state[13 * used.suit_index + used.value - 2] = 2

    def set_score_cards(self, scores): # list
        for s in scores:
            s_card = Card(s)
            self.state[13 * s_card.suit_index + s_card.value - 2] = -2

    def set_action(self, action_card): # Card
        self.action[13 * action_card.suit_index + action_card.value - 2] = 1

    def set_reward(self, round_score): # int. Accumulative by our calculation
        self.reward = round_score

    def set_total_rewards(self, total_score): # int
        self.total_rewards = total_score

    # save <s, a ,r> of each step
    # this is used for calculating discounted rewards
    def memorize(self):
        self.states.append(self.state)
        self.actions.append(self.action)
        self.rewards.append(self.reward)
    
   
   