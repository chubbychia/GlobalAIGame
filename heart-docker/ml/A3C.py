import threading
import numpy as np
import tensorflow as tf
import pylab
import time
import gym
import os
from keras.layers import Dense, Input
from keras.models import Model
from keras.optimizers import Adam
from keras import backend as K


# global variables for threading
episode = 0
scores = []

EPISODES = 2000

# This is A3C(Asynchronous Advantage Actor Critic) agent(global) for the Cartpole
# In this example, we use A3C algorithm
class A3CAgent:
    def __init__(self, state_size, action_size):
        # get size of state and action
        self.state_size = state_size
        self.action_size = action_size

        # these are hyper parameters for the A3C
        self.actor_lr = 0.001
        self.critic_lr = 0.001
        self.discount_factor = .99
        self.hidden1, self.hidden2 = 30, 30
        self.threads = 1

        current_folder = os.path.dirname(os.path.abspath(__file__))
        actor_path = os.path.join(current_folder, "./save_model/trend_hearts_actor.h5")
        critic_path = os.path.join(current_folder, "./save_model/trend_hearts_critic.h5")
        if os.path.exists(actor_path) and os.path.exists(critic_path): 
            self.load_model('./save_model/trend_hearts')
            print('!!!!!!!!!!LOAD MODEL!!!!!!!!!!')
        # create model for actor and critic network
        else:
            self.actor, self.critic = self.build_model()

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
    def train(self, players_episodes):
        agents = [Agent(players_episodes[i], self.actor, self.critic, self.optimizer, self.discount_factor) for i in range(self.threads)]

        for agent in agents:
            agent.start()
        
        self.save_model('./save_model/trend_hearts')
        
        #If batch training 
        #while True:
        #    time.sleep(10)
        #    plot = scores[:]
        #    pylab.plot(range(len(plot)), plot, 'b')
        #    pylab.savefig("./save_graph/trend_hearts.png")
           

    def save_model(self, name):
        self.actor.save_weights(name + "_actor.h5")
        self.critic.save_weights(name + "_critic.h5")

    def load_model(self, name):
        self.actor.load_weights(name + "_actor.h5")
        self.critic.load_weights(name + "_critic.h5")

# This is Agent(local) class for threading
class Agent(threading.Thread):
    def __init__(self, player, actor, critic, optimizer, discount_factor):
        threading.Thread.__init__(self)
        self.player = player # Player
        self.actor = actor
        self.critic = critic
        self.optimizer = optimizer
        self.discount_factor = discount_factor
    
    # Thread 
    def run(self):
        global episode
        episode += 1
        scores.append(self.player.total_rewards)
        self.train_episode()

    # In Policy Gradient, Q function is not available.
    # Instead agent uses sample returns for evaluating policy
    def discount_rewards(self, rewards, done=True):
        discounted_rewards = np.zeros_like(rewards)
        running_add = 0
        if not done:
            running_add = self.critic.predict(np.reshape(self.states[-1], (1, self.player.state_size)))[0]
        for t in reversed(range(0, len(rewards))):
            running_add = running_add * self.discount_factor + rewards[t]
            discounted_rewards[t] = running_add
        return discounted_rewards
  
    # update policy network and value network every episode
    def train_episode(self):
        discounted_rewards = self.discount_rewards(self.player.rewards)

        values = self.critic.predict(np.array(self.player.states))
        values = np.reshape(values, len(values))

        advantages = discounted_rewards - values

        self.optimizer[0]([self.player.states, self.player.actions, advantages])
        self.optimizer[1]([self.player.states, discounted_rewards])
        self.states, self.actions, self.rewards = [], [], []

   

if __name__ == "__main__":
  
    #state_size = env.observation_space.shape[0]
    #action_size = env.action_space.n
    state_size = 54
    action_size = 52
    global_agent = A3CAgent(state_size, action_size)
    #global_agent.train()