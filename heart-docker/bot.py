from abc import abstractmethod
from utils.poker import Card
from utils.log import Log
from utils.strategy import Strategy
from ml.A3C import A3CAgent, Agent
from player import Player
import numpy as np
import collections
import datetime
import os
import pickle
class PokerBot(object):

    def __init__(self, player_name, system_log):
        self.round_cards_history = []
        self.pick_his = {}
        self.round_cards = {}
        self.score_cards = {}
        self.player_name = player_name
        self.players_current_picked_cards = []
        self.game_score_cards = {Card("QS"), Card("TC"), Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"),
                           Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), Card("QH"), Card("KH"),
                           Card("AH")}
        self.system_log = system_log
        self.state_size = 54
        self.action_size =  12 # strategy amount
        self.player_dict = collections.defaultdict(list)
        self.global_agent = A3CAgent(self.state_size, self.action_size)
        self.player_episodes = []
        self.strategy = None
    #@abstractmethod
    def new_deal(self,data):
        err_msg = self.__build_err_msg("receive_cards")
        raise NotImplementedError(err_msg)
    def pass_cards(self,data):
        err_msg = self.__build_err_msg("pass_cards")
        raise NotImplementedError(err_msg)
    def pick_card(self,data):
        err_msg = self.__build_err_msg("pick_card")
        raise NotImplementedError(err_msg)
    def expose_my_cards(self,yourcards):
        err_msg = self.__build_err_msg("expose_my_cards")
        raise NotImplementedError(err_msg)
    def expose_cards_end(self,data):
        err_msg = self.__build_err_msg("expose_cards_announcement")
        raise NotImplementedError(err_msg)
    def receive_opponent_cards(self,data):
        err_msg = self.__build_err_msg("receive_opponent_cards")
        raise NotImplementedError(err_msg)
    def round_end(self,data):
        err_msg = self.__build_err_msg("round_end")
        raise NotImplementedError(err_msg)
    def deal_end(self,data):
        err_msg = self.__build_err_msg("deal_end")
        raise NotImplementedError(err_msg)
    def game_over(self,data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)
    def show_pick_history(self,data,is_timeout,pick_his):
        err_msg = self.__build_err_msg("show_pick_history")
        raise NotImplementedError(err_msg)

    def reset_card_his(self):
        self.round_cards_history = []
        self.pick_his={}
    
    def reset_player_dict(self):
        self.player_episodes = []
        self.player_dict = {}

    def get_card_history(self):
        return self.round_cards_history

    def get_cards(self,data):
        try:
            receive_cards=[]
            players=data['players']
            for player in players:
                if player['playerName']==self.player_name:
                    cards=player['cards']
                    for card in cards:
                        receive_cards.append(Card(card))
                    break
            return receive_cards
        except Exception as e:
            self.system_log.show_message(e)
            self.system_log.save_errors(e)
            return None

    def get_round_scores(self,is_expose_card=False,data=None):
        if data!=None:
            players = data['roundPlayers']
            picked_user = players[0] #init
            round_card = self.round_cards.get(picked_user)
            score_cards=[]
            for i in range(len(players)):
                card=self.round_cards.get(players[i])
                if card in self.game_score_cards:
                    score_cards.append(card)
                if round_card.suit_index==card.suit_index:
                    if round_card.value<card.value:
                        picked_user = players[i] #next
                        round_card=card
            if (self.score_cards.get(picked_user)!=None):
                current_score_cards=self.score_cards.get(picked_user)
                score_cards+=current_score_cards
            self.score_cards[picked_user]=score_cards
            self.round_cards = {}

        receive_cards={}
        for key in self.pick_his.keys():
            picked_score_cards=self.score_cards.get(key)
            round_score = 0
            round_heart_score=0
            is_double = False
            if picked_score_cards!=None:
                for card in picked_score_cards:
                    if card in self.game_score_cards:
                        if card == Card("QS"):
                            round_score += -13
                        elif card == Card("TC"):
                            is_double = True
                        else:
                            round_heart_score += -1
                if is_expose_card:
                    round_heart_score*=2
                round_score+=round_heart_score
                if is_double:
                    round_score*=2
            receive_cards[key] = round_score
        return receive_cards

    def get_deal_scores(self, data):
        try:
            self.score_cards = {}
            final_scores  = {}
            initial_cards = {}
            receive_cards = {}
            picked_cards  = {}
            players = data['players']
            for player in players:
                player_name     = player['playerName']
                palyer_score    = player['dealScore']
                player_initial  = player['initialCards']
                player_receive  = player['receivedCards']
                player_picked   = player['pickedCards']

                final_scores[player_name] = palyer_score
                initial_cards[player_name] = player_initial
                receive_cards[player_name]=player_receive
                picked_cards[player_name]=player_picked
            return final_scores, initial_cards,receive_cards,picked_cards
        except Exception as e:
            self.system_log.show_message(e)
            self.system_log.save_errors(e)
            return None

    def get_game_scores(self,data):
        try:
            receive_cards={}
            players=data['players']
            for player in players:
                player_name=player['playerName']
                palyer_score=player['gameScore']
                receive_cards[player_name]=palyer_score
            return receive_cards
        except Exception as e:
            self.system_log.show_message(e)
            self.system_log.save_errors(e)
            return None
  
    # save <s, a ,r> of each step from every player's point of view
    def set_player_episodes(self, player):
        self.player_episodes.append(player)

   
class HeartPlayBot(PokerBot):

    def __init__(self,name,system_log,IS_SAVE_DATA):
        super(HeartPlayBot,self).__init__(name, system_log)
        self.my_hand_cards=[]
        self.expose_card=False
        self.my_pass_card=[]
        self.is_save_data = IS_SAVE_DATA

    def new_game(self,data):
        message="============== New Game =============="
        self.system_log.show_message(message)
        self.system_log.save_logs(message)

    
    def new_deal(self,data):
        self.my_hand_cards=self.get_cards(data)
        # init Player
        self.player_dict[self.player_name] = Player(self.player_name,self.state_size,self.action_size)
        # init Strategy
        self.strategy = Strategy()
        message="New Deal: No.{}. Init Player and Strategy".format(data['dealNumber'])
        self.system_log.show_message(message)
        self.system_log.save_logs(message)

  
    def pass_cards(self,data):
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        pass_cards=[]
        count=0
        suit_dict = collections.defaultdict(int)
        for card in self.my_hand_cards:
            # count every suit's amount
            suit_dict[card.suit] += 1 
            if card==Card("QS"): # -13
                pass_cards.append(card)
                count+=1
            elif card==Card("TC"): # - double your score in this deal (except shooting the moon)
                pass_cards.append(card)
                count += 1
            #elif card.suit_index == 2: # pick largest Heart (already desc sort)
            #    pass_cards.append(card)
            #    count += 1
            if count == 3:
                break
        i=0
        asc_suit_amount = sorted(suit_dict.items(), key=lambda d: d[1]) #asc :[('S', 0), ('D', 1), ('C', 5), ('H', 7)]
        while count < 3:
            minn = asc_suit_amount[i][0]
            for card in self.my_hand_cards: 
                if card.suit == minn: # pick the least suit so far
                    pass_cards.append(card)
                    count += 1
                if count == 3:
                    break
            i+=1
                
        return_values=[]
        for card in pass_cards:
            return_values.append(card.toString())
        self.my_pass_card=return_values
        return return_values

    def pick_card(self,data):
        me = data['self']['playerName'] 
        cadidate_cards=data['self']['candidateCards']
        # set strategy candidate cards
        self.strategy.set_candidates(cadidate_cards)
        out_round = []
        # print("candidates_cards {}".format(cadidate_cards))
        for player_name, out_turn_card in self.round_cards.items():
            out_round.append(out_turn_card)
        # set strategy round cards
        self.strategy.set_roundcards(out_round)
        # print("round_cards {}".format(out_round))
        if self.player_dict[me]:
            predict_strategy_num = self.global_agent.predict_action(self.player_dict[me].state)
            message = "Me:{}, Predict Startegy No.{}".format(me, predict_strategy_num)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            predict_card, actual_action = self.strategy.dispatcher(predict_strategy_num)
            # set the chosen action
            message = "Me:{}, Startegy Fallback to No.{}".format(me, actual_action)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            self.player_dict[me].set_action(actual_action)
            message = "Me:{}, Set Action: {}".format(me, self.player_dict[me].action)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            card_string = predict_card.toString()
            message = "Me:{}, Predict Card:{}".format(me, card_string)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            return card_string
        else:
            cards = data['self']['cards']
            self.my_hand_cards = []
            for card_str in cards:
                card = Card(card_str)
                self.my_hand_cards.append(card)
            message = "My Cards:{}".format(self.my_hand_cards)
            self.system_log.show_message(message)
            card_index=len(cadidate_cards)-1 # pick smallest
            message = "Pick Card Event Content:{}".format(data)
            self.system_log.show_message(message)
            message = "Candidate Cards:{}".format(cadidate_cards)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            message = "Pick Card:{}".format(cadidate_cards[card_index])
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            return cadidate_cards[card_index]
        
    def expose_my_cards(self,yourcards):
        expose_card=[]
        for card in self.my_hand_cards:
            if card==Card("AH"):
                expose_card.append(card.toString())
        message = "Expose Cards:{}".format(expose_card)
        self.system_log.show_message(message)
        self.system_log.save_logs(message)
        return expose_card

    def expose_cards_end(self,data):
        players = data['players']
        expose_player=None
        expose_card=None
        for player in players:
            try:
                if player['exposedCards']!=[] and len(player['exposedCards'])>0 and player['exposedCards']!=None:
                    expose_player=player['playerName']
                    expose_card=player['exposedCards']
            except Exception as e:
                self.system_log.show_message(e)
                self.system_log.save_errors(e)
        if expose_player!=None and expose_card!=None:
            message="Player:{}, Expose card:{}".format(expose_player,expose_card)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            #for player in self.player_dict.values(): # if multi 
            self.player_dict[self.player_name].set_AH_exposed()
            self.expose_card=True
        else:
            message="No player expose card!"
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
            self.expose_card=False

    def receive_opponent_cards(self,data):
        self.my_hand_cards = self.get_cards(data)
        players = data['players']
        for player in players:
            player_name = player['playerName']
            if player_name == self.player_name:
                picked_cards = player['pickedCards']
                receive_cards = player['receivedCards']
                message = "Me:{}, Picked Cards:{}, Received Cards:{}".format(player_name, picked_cards,receive_cards)
                self.system_log.show_message(message)
                self.system_log.save_logs(message)
    
    def pass_cards_end(self,data):
        players = data['players']
        for player in players:
            if player['playerName'] == self.player_name:
                cards = player['cards']
                player_sample = self.player_dict[self.player_name]
                if player_sample:
                    player_sample.set_hand_cards(cards)
                    message="Me:{}, new state after pass cards changing:{}".format(self.player_name, player_sample.state)
                    self.system_log.show_message(message)
                    self.system_log.save_logs(message)
    
    def new_round(self,data):
        message="New Round: No.{}".format(data['roundNumber'])
        self.system_log.show_message(message)
        self.system_log.save_logs(message)

    def turn_end(self,data):
        turnCard=data['turnCard']
        turnPlayer=data['turnPlayer']
        players=data['players']
        is_timeout=data['serverRandom']
        player_sample = self.player_dict[self.player_name]
        for player in players:
            if player['playerName'] == self.player_name:
                current_cards=player['cards']
                for card in current_cards:
                    self.players_current_picked_cards.append(Card(card)) # self left hand cards
        
        self.round_cards[turnPlayer]=Card(turnCard) # turnPlayer hand out turnCard. keep round_cards here {'P1':'3C', 'P2':'8C'}
        
        if self.player_name == turnPlayer:
            player_sample.set_turn_card(Card(turnCard))
            message = "My Turn:{}. Pick {} State: {}".format(turnPlayer, turnCard, player_sample.state)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
        else:
            player_sample.set_others_turn_card(Card(turnCard))
            message = "{}'s Turn:. Pick {}  Mark it used. State: {}".format(turnPlayer, turnCard, player_sample.state)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)

        opp_pick={}
        opp_pick[turnPlayer]=Card(turnCard)
        if (self.pick_his.get(turnPlayer))!=None:
            pick_card_list=self.pick_his.get(turnPlayer)
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer]=pick_card_list
        else:
            pick_card_list = []
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer] = pick_card_list
        self.round_cards_history.append(Card(turnCard))
        #self.show_pick_history(data,is_timeout,opp_pick)

    def round_end(self,data):
        try:
            # reset self.round_cards = {}
            round_scores=self.get_round_scores(self.expose_card, data) # we calculate the round scores with AH, TC rules!
            # reset strategy
            self.strategy.reset_can_round()
            players = data['players']
            for player in players:
                player_name = player['playerName']
                if player_name == self.player_name:
                    player_sample = self.player_dict[player_name]
                    # set dumpted cards
                    player_sample.set_dumped_card()
                    player_sample.set_score_cards(player['scoreCards'])
                    message = "Player:{}, scoreCards:{} State:{}".format(player_name, player['scoreCards'], player_sample.state)
                    self.system_log.show_message(message)
                    self.system_log.save_logs(message)
                    # mark TC
                    if "TC" in player['scoreCards']:
                        player_sample.set_TC_eaten()
                        message = "Player:{}, TC eaten:{} State:{}".format(player_name, player['scoreCards'], player_sample.state)
                        self.system_log.show_message(message)
                        self.system_log.save_logs(message)
            
            # Penalty if opponent is shooting the moon
            shooting_the_moon = [r for r in round_scores.values() if r > 0]
            for key in round_scores.keys():
                message = "Player name:{}, Round score:{}".format(key, round_scores.get(key))
                self.system_log.show_message(message)
                self.system_log.save_logs(message)
                if key == self.player_name:
                    my_score = round_scores.get(key)
                    if shooting_the_moon:
                        my_score = my_score - shooting_the_moon[0]
                    self.player_dict[self.player_name].set_reward(my_score)
                    message = "Player name:{}, state {}, action {}, reward {} ".format(key,self.player_dict[self.player_name].state, self.player_dict[self.player_name].action, self.player_dict[self.player_name].reward)
                    self.system_log.show_message(message)
                    self.system_log.save_logs(message)
                    self.player_dict[self.player_name].memorize()
        except Exception as e:
            self.system_log.show_message(e)
            self.system_log.save_errors(e)

    def deal_end(self,data):
        self.my_hand_cards=[]
        self.expose_card = False
        deal_scores,initial_cards,receive_cards,picked_cards=self.get_deal_scores(data)
        message = "Me:{}, Pass Cards:{}".format(self.player_name, self.my_pass_card)
        self.system_log.show_message(message)
        self.system_log.save_logs(message)
        for key in deal_scores.keys():
            if key == self.player_name:
                self.set_player_episodes(self.player_dict[key])
                message = "Me:{}, Deal score:{}".format(key,deal_scores.get(key))
                self.system_log.show_message(message)
                self.system_log.save_logs(message)
                #message = "Episode states:{}, Episode actions:{}, Episode rewards:{}".format(self.player_dict[key].states,self.player_dict[key].actions,self.player_dict[key].rewards)
                #self.system_log.show_message(message)
                #self.system_log.save_logs(message)
                episode_s_a_r = [self.player_dict[key].states] + [self.player_dict[key].actions] + [self.player_dict[key].rewards]
                if self.is_save_data:
                    self.save_append_training_data(episode_s_a_r)
                
        self.global_agent.train(self.player_episodes)
        
        message = "Episode saved and trained with thread"
        self.system_log.show_message(message)
        self.system_log.save_logs(message)

        for key in initial_cards.keys():
            message = "Player name:{}, Initial cards:{}, Receive cards:{}, Picked cards:{}".format(key, initial_cards.get(key),receive_cards.get(key),picked_cards.get(key))
            self.system_log.show_message(message)
            self.system_log.save_logs(message)

    def save_append_training_data(self, episode): 
        now = datetime.datetime.now()
        current_folder = os.path.dirname(os.path.abspath(__file__))
        TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ str(now)[:10] + '.pkl')
        directory = os.path.dirname(TRAINDATA_PATH)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        if os.path.exists(directory):
            with open(TRAINDATA_PATH,'ab') as f:
                pickle.dump(episode, f)

    def game_over(self,data):
        game_scores = self.get_game_scores(data)
        for key in game_scores.keys():
            message = "Player name:{}, Game score:{}".format(key, game_scores.get(key))
            self.system_log.show_message(message)
            self.system_log.save_logs(message)

    def show_pick_history(self,data,is_timeout,pick_his):
        for key in pick_his.keys():
            message = "Player name:{}, Pick card:{}, Is timeout:{}".format(key,pick_his.get(key),is_timeout)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
