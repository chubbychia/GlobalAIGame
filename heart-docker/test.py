import numpy as np
import datetime
import os
import pickle


current_folder = os.path.dirname(os.path.abspath(__file__))
       
def load_training_data(fname):
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
    obj = []
    if os.path.exists(TRAINDATA_PATH):
        with open(TRAINDATA_PATH, 'rb') as f:
            while True:
                try:
                    l = pickle.load(f)
                    # s_array=l[0]
                    # if isinstance(s_array, np.ndarray):
                    #     print(s_array)
                    obj.append(l)

                except EOFError:
                    break
        print("load: {}".format(obj))
    else:
        print("No such training file {}".format(TRAINDATA_PATH))
    return obj

def save_append_training_data(episode): 
        now = datetime.datetime.now()
        TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ str(now)[:10] + '.pkl')
        directory = os.path.dirname(TRAINDATA_PATH)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        if os.path.exists(directory):
            with open(TRAINDATA_PATH,'ab') as f:
                print(episode)
                pickle.dump(episode, f)

if __name__ == "__main__":
    states = []
    states.append(np.array([1, 2]))
    states.append(np.array([5, 6]))
    actions = []
    actions.append(np.array([0, 0, 7]))
    actions.append(np.array([2, 6, 9]))
    rewards = [0,0,0,0,-1,-4,-7,-8,-8]
    # print(states)
    # print(actions)
    # print(rewards)

    #s_a_r = list(np.tolist() for np in states) + list(np.tolist() for np in actions) + [rewards]
    # s = [np.tolist() for np in states]
    # a = [np.tolist() for np in actions]
    # r = [rewards]
    
    epi = str([states]+[actions]+[rewards])
    
    #save_append_training_data(epi)
    load_training_data('2018-09-03')

