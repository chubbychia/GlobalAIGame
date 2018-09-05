import threading
import numpy as np
import tensorflow as tf
import time
import os
from keras.layers import Dense, Input
from keras.models import Model
from keras.optimizers import Adam
from keras import backend as K
import sys
import pickle


# global variables for threading
ws_folder = os.path.dirname(os.path.abspath(__file__+"/../"))


# This is A3C(Asynchronous Advantage Actor Critic) agent(global) 
class A3CAgent:
    def __init__(self, state_size, action_size, is_train_mode=False):
        # get size of state and action
        self.state_size = state_size
        self.action_size = action_size
        # these are hyper parameters for the A3C
        self.actor_lr = 0.001
        self.critic_lr = 0.001
        # modifiy to no discount becase hearts has no such phenomenon
        self.discount_factor = 1
        self.hidden1, self.hidden2 = 30, 30
        self.threads = 1
        self.is_train_mode = is_train_mode

        # create model for actor and critic network
        self.actor, self.critic = self.build_model()

        actor_path = os.path.join(ws_folder, "save_model/trend_hearts_actor.h5")
        critic_path = os.path.join(ws_folder, "save_model/trend_hearts_critic.h5")
        if os.path.exists(actor_path) and os.path.exists(critic_path):
            self.load_model('./save_model/trend_hearts')
                
        # method for training actor and critic network
        self.optimizer = [self.actor_optimizer(), self.critic_optimizer()]

        self.sess = tf.InteractiveSession()
        K.set_session(self.sess)
        self.sess.run(tf.global_variables_initializer())

    # approximate policy and value using Neural Network
    # actor -> state is input and probability of each action is output of network
    # critic -> state is input and value of state is output of network
    # actor and critic network share first hidden layer
    def build_model(self):
        state = Input(batch_shape=(None,  self.state_size))
        shared = Dense(self.hidden1, input_dim=self.state_size, activation='relu', kernel_initializer='glorot_uniform')(state)

        actor_hidden = Dense(self.hidden2, activation='relu', kernel_initializer='glorot_uniform')(shared)
        action_prob = Dense(self.action_size, activation='softmax', kernel_initializer='glorot_uniform')(actor_hidden)

        value_hidden = Dense(self.hidden2, activation='relu', kernel_initializer='he_uniform')(shared)
        state_value = Dense(1, activation='linear', kernel_initializer='he_uniform')(value_hidden) # linear for regression prediction

        actor = Model(inputs=state, outputs=action_prob)
        critic = Model(inputs=state, outputs=state_value)

        actor._make_predict_function()
        critic._make_predict_function()

        actor.summary()
        critic.summary()

        return actor, critic

    # make loss function for Policy Gradient
    # [log(action probability) * advantages] will be input for the back prop
    # we add entropy of action probability to loss
    def actor_optimizer(self):
        action = K.placeholder(shape=(None, self.action_size)) # label
        advantages = K.placeholder(shape=(None, )) # Expected reward

        policy = self.actor.output # output layer = action prob (since softmax)

        good_prob = K.sum(action * policy, axis=1)
        eligibility = K.log(good_prob + 1e-10) * K.stop_gradient(advantages)
        loss = -1*K.sum(eligibility)

        entropy = K.sum(policy * K.log(policy + 1e-10), axis=1)

        actor_loss = loss + 0.01*entropy

        optimizer = Adam(lr=self.actor_lr)
        updates = optimizer.get_updates(self.actor.trainable_weights, [], actor_loss)
        train = K.function([self.actor.input, action, advantages], [], updates=updates)
    
        return train

    # make loss function for Value approximation
    def critic_optimizer(self):
        discounted_reward = K.placeholder(shape=(None, ))

        value = self.critic.output

        critic_loss = K.mean(K.square(discounted_reward - value))

        optimizer = Adam(lr=self.critic_lr)
        updates = optimizer.get_updates(self.critic.trainable_weights, [], critic_loss)
        train = K.function([self.critic.input, discounted_reward], [], updates=updates)
        return train

    def predict_action(self, state):
        policy = self.actor.predict(np.reshape(state, [1, self.state_size]))[0]
        return np.random.choice(self.action_size, 1, p=policy)[0]
  
    # make agents(local) and start training
    def train(self, player_episode):
        if self.is_train_mode:
            thread = 4
            partition = len(player_episode)//thread
            agents = [Agent(player_episode[partition*i : partition*(i+1) if partition*(i+2) < len(player_episode) else len(player_episode)], self.actor, self.critic, self.optimizer, self.discount_factor) for i in range(thread)]
        else:
            agents = [Agent(player_episode, self.actor, self.critic, self.optimizer, self.discount_factor)]
        
        for agent in agents:
            agent.start()
        
        time.sleep(2)
        self.save_model('./save_model/trend_hearts')
        
       
    def save_model(self, name):
        self.actor.save_weights(name + "_actor.h5")
        self.critic.save_weights(name + "_critic.h5")

    def load_model(self, name):
        self.actor.load_weights(name + "_actor.h5")
        self.critic.load_weights(name + "_critic.h5")

# This is Agent(local) class for threading
class Agent(threading.Thread):
    def __init__(self, player_episodes, actor, critic, optimizer, discount_factor):
        threading.Thread.__init__(self)
        self.player_episodes = player_episodes # Player list
        self.actor = actor
        self.critic = critic
        self.optimizer = optimizer
        self.discount_factor = discount_factor
    
    # Thread 
    def run(self):
        #print("Number of episode dispatched: {}".format(len(self.player_episodes)))
        for player in self.player_episodes:
            self.train_episode(player)

    # In Policy Gradient, Q function is not available.
    # Instead agent uses sample returns for evaluating policy
    def discount_rewards(self, rewards):
        discounted_rewards = np.zeros_like(rewards)
        running_add = 0
        for t in reversed(range(0, len(rewards))):
            running_add = running_add * self.discount_factor + rewards[t]
            discounted_rewards[t] = running_add
        return discounted_rewards
  
     # update policy network and value network every episode
    def train_episode(self, player):
        discounted_rewards = self.discount_rewards(player.rewards)

        values = self.critic.predict(np.array(player.states))
        values = np.reshape(values, len(values))

        advantages = discounted_rewards - values

        self.optimizer[0]([player.states, player.actions, advantages])
        self.optimizer[1]([player.states, discounted_rewards])

   
def _load_training_data(fname, start_from, episode_num): 
    global ws_folder
    TRAINDATA_PATH = os.path.join(ws_folder, 'training/'+ fname + '.pkl')
    directory = os.path.dirname(TRAINDATA_PATH)
    
    player_line = []
    episode_count = -1
    end_before = episode_num + start_from
    if not os.path.exists(directory):
        return None
    else:
        with open(TRAINDATA_PATH,'rb') as f:
            while True:
                try:
                    episode_count += 1                   
                    if episode_count < start_from:
                        #print('skip #'+str(episode_count))
                        continue
                    elif episode_count < end_before: 
                        line = pickle.load(f)
                        player_line.append(line)
                    elif episode_count >= end_before:
                        break
                except EOFError as e:
                    print('_load_training_data exception: {}'.format(e))
                    break
        return player_line
    
def _parse_player(episode, state_size, action_size):
    player_episode = []
    for epi in episode:
        player = Player('training_player', state_size, action_size)
        player.states = epi[0] 
        player.actions = epi[1]
        player.rewards = epi[2]
        player_episode.append(player)
    #print(player_episode)
    return player_episode

def load_parent():
    import os,sys,inspect
    current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir) 

if __name__ == "__main__":
  
    state_size = 54
    action_size = 52
    start_from = 2
    EPISODES = 5
    IS_TRAIN_MODE = True

    if len(sys.argv) < 2:
        print("Usage: {} <FILENAME>".format(sys.argv[0]))
        sys.exit(1)

    fname = sys.argv[1]
   
    load_parent()
    from player import Player
    player_line = _load_training_data(fname, start_from, EPISODES)
    player_episode = _parse_player(player_line, state_size, action_size)
    global_agent = A3CAgent(state_size, action_size,IS_TRAIN_MODE)
    global_agent.train(player_episode)