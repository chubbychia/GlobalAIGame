from abc import abstractmethod
from utils.poker import Card
from utils.log import Log


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
    #@abstractmethod
    def receive_cards(self,data):
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
    def pick_history(self,data,is_timeout,pick_his):
        err_msg = self.__build_err_msg("pick_history")
        raise NotImplementedError(err_msg)

    def reset_card_his(self):
        self.round_cards_history = []
        self.pick_his={}

    def get_card_history(self):
        return self.round_cards_history

    def turn_end(self,data):
        turnCard=data['turnCard']
        turnPlayer=data['turnPlayer']
        players=data['players']
        is_timeout=data['serverRandom']
        for player in players:
            player_name=player['playerName']
            if player_name==self.player_name:
                current_cards=player['cards']
                for card in current_cards:
                    self.players_current_picked_cards.append(Card(card))
        self.round_cards[turnPlayer]=Card(turnCard)
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
        self.pick_history(data,is_timeout,opp_pick)

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
        except Exception, e:
            self.system_log.show_message(e.message)
            return None

    def get_round_scores(self,is_expose_card=False,data=None):
        if data!=None:
            players=data['roundPlayers']
            picked_user = players[0]
            round_card = self.round_cards.get(picked_user)
            score_cards=[]
            for i in range(len(players)):
                card=self.round_cards.get(players[i])
                if card in self.game_score_cards:
                    score_cards.append(card)
                if round_card.suit_index==card.suit_index:
                    if round_card.value<card.value:
                        picked_user = players[i]
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
        except Exception, e:
            self.system_log.show_message(e.message)
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
        except Exception, e:
            self.system_log.show_message(e.message)
            return None


class LowPlayBot(PokerBot):

    def __init__(self,name,system_log):
        super(LowPlayBot,self).__init__(name, system_log)
        self.my_hand_cards=[]
        self.expose_card=False
        self.my_pass_card=[]
    
    def receive_cards(self,data):
        self.my_hand_cards=self.get_cards(data)

    def _sorting_desc(self):
        def _quicksort(unsort_cards):
            if len(unsort_cards) <= 1:
                return unsort_cards
            else:
                last_idx = len(unsort_cards)-1
                pivot = unsort_cards[last_idx] 
                rest_of_cards = unsort_cards[:last_idx]
                minor = []
                larger = []
                pivotlist = []
                for card in rest_of_cards:
                    if pivot.value > card.value:
                        minor.append(card)
                    else:
                        larger.append(card)                  
                pivotlist.append(pivot)
                return _quicksort(larger)+pivotlist+_quicksort(minor)
        
        return _quicksort(self.my_hand_cards)
        
    def pass_cards(self,data):
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        pass_cards=[]
        count=0
        for card in self.my_hand_cards:
            if card==Card("QS"): # -13
                pass_cards.append(card)
                count+=1
            elif card==Card("TC"): # - double your score in this deal (except shooting the moon)
                pass_cards.append(card)
                count += 1
            elif card.suit_index == 2: # pick largest Heart (already desc sort)
                pass_cards.append(card)
                count += 1
                if count == 3:
                    break
        if count < 3:
            suit_dict = defaultdict(int)
            for card in self.my_hand_card:
                suit_dict[card.suit_index] += 1 
            minn = None
            for k,v in suit_dict.items():
                if minn is None or v < minn:
                    minn = k
            for card in self.my_hand_card: 
                if card.suit_index == minn: # pick the least suit
                    pass_cards.append(card)
                    count += 1
                if count < 3: 
                    pass_cards.append(card)
                if count == 3:
                    break

        return_values=[]
        for card in pass_cards:
            return_values.append(card.toString())
        message="Pass Cards:{}".format(return_values)
        self.system_log.show_message(message)
        self.system_log.save_logs(message)
        self.my_pass_card=return_values
        return return_values

    def pick_card(self,data):
        cadidate_cards=data['self']['candidateCards'] # Action
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        message = "My Cards:{}".format(self.my_hand_cards)
        self.system_log.show_message(message)
        card_index=0
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
            except Exception, e:
                self.system_log.show_message(e.message)
                self.system_log.save_logs(e.message)
        if expose_player!=None and expose_card!=None:
            message="Player:{}, Expose card:{}".format(expose_player,expose_card)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
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
                message = "User Name:{}, Picked Cards:{}, Receive Cards:{}".format(player_name, picked_cards,receive_cards)
                self.system_log.show_message(message)
                self.system_log.save_logs(message)

    def round_end(self,data):
        try:
            round_scores=self.get_round_scores(self.expose_card, data)
            for key in round_scores.keys():
                message = "Player name:{}, Round score:{}".format(key, round_scores.get(key))
                self.system_log.show_message(message)
                self.system_log.save_logs(message)
        except Exception, e:
            self.system_log.show_message(e.message)

    def deal_end(self,data):
        self.my_hand_cards=[]
        self.expose_card = False
        deal_scores,initial_cards,receive_cards,picked_cards=self.get_deal_scores(data)
        message = "Player name:{}, Pass Cards:{}".format(self.player_name, self.my_pass_card)
        self.system_log.show_message(message)
        self.system_log.save_logs(message)
        for key in deal_scores.keys():
            message = "Player name:{}, Deal score:{}".format(key,deal_scores.get(key))
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
        for key in initial_cards.keys():
            message = "Player name:{}, Initial cards:{}, Receive cards:{}, Picked cards:{}".format(key, initial_cards.get(key),receive_cards.get(key),picked_cards.get(key))
            self.system_log.show_message(message)
            self.system_log.save_logs(message)

    def game_over(self,data):
        game_scores = self.get_game_scores(data)
        for key in game_scores.keys():
            message = "Player name:{}, Game score:{}".format(key, game_scores.get(key))
            self.system_log.show_message(message)
            self.system_log.save_logs(message)

    def pick_history(self,data,is_timeout,pick_his):
        for key in pick_his.keys():
            message = "Player name:{}, Pick card:{}, Is timeout:{}".format(key,pick_his.get(key),is_timeout)
            self.system_log.show_message(message)
            self.system_log.save_logs(message)
