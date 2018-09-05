import collections
from random import randint
from utils.poker import Card

SCORE_CARDS = ["QS", "TC", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "TH", "JH", "QH", "KH", "AH"]

        
class Strategy(object):

    def __init__(self): 
        self.candidates = [] # Card
        self.round_cards = [] # Card. # round_cards were the card your previous players handed out. None if your are the first player
       

    def set_candidates(self, candi):
        for c in candi:
            self.candidates.append(Card(c))
    
    def set_roundcards(self, round_cards):
        for r in round_cards:
            if isinstance (r, Card):
                self.round_cards.append(r)
            else:
                self.round_cards.append(Card(r))

    def reset_can_round(self):
        self.candidates = []
        self.round_cards = [] 

    def dispatcher(self, num): 
        if num == 0:
            return self.least_suit_min_value()
        elif num == 1:
            return self.least_suit_max_value()
        elif num == 2:
            return self.most_suit_min_value()
        elif num == 3:
            return self.most_suit_max_value()
        elif num == 4:
            return self.score_suit_min_value()
        elif num == 5:
            return self.score_suit_max_value()
        elif num == 6:
            return self.non_score_suit_min_value()
        elif num == 7:
            return self.non_score_suit_max_value()
        elif num == 8:
            return self.same_suit_smaller()
        elif num == 9:
            return self.same_suit_larger()
        elif num == 10:
            return self.diff_suit_score()
        elif num == 11:
            return self.diff_suit_non_score()
        else:
            return self.dispatcher(randint(0, 11))
  
    
    #0
    def least_suit_min_value(self): 
        num = 0
        # if candidates are uni suit, exactly = choose min value
        suit_dict = collections.defaultdict(int)
        for card in self.candidates:
            suit_dict[card.suit] += 1
        asc_suit = self._sorting_suit(suit_dict) #[('S', 0), ('D', 1), ('C', 5), ('H', 7)]
        filtered = self._pick_suit_cards(asc_suit[0][0], self.candidates)
        return self._sorting_value_asc(filtered)[0], num
    #1
    def least_suit_max_value(self):
        num = 1
        # if uni suit, exactly = choose min value
        suit_dict = collections.defaultdict(int)
        for card in self.candidates:
            suit_dict[card.suit] += 1
        asc_suit = self._sorting_suit(suit_dict) #[('S', 0), ('D', 1), ('C', 5), ('H', 7)]
        filtered = self._pick_suit_cards(asc_suit[0][0], self.candidates)
        return self._sorting_value_asc(filtered)[len(filtered)-1], num
           
    #2
    def most_suit_min_value(self):
        num = 2
        suit_dict = collections.defaultdict(int)
        for card in self.candidates:
            suit_dict[card.suit] += 1
        desc_suit = self._sorting_suit(suit_dict, reverse=True)
        filtered = self._pick_suit_cards(desc_suit[0][0], self.candidates)
        return self._sorting_value_asc(filtered)[0], num
    #3
    def most_suit_max_value(self):
        num = 3
        suit_dict = collections.defaultdict(int)
        for card in self.candidates:
            suit_dict[card.suit] += 1
        desc_suit = self._sorting_suit(suit_dict, reverse=True)
        filtered = self._pick_suit_cards(desc_suit[0][0], self.candidates)
        return self._sorting_value_asc(filtered)[len(filtered)-1], num
            
    #4
    def score_suit_min_value(self):
        num = 4
        global SCORE_CARDS
        score_candidates = [card for card in self.candidates if card.toString() in SCORE_CARDS]
        if score_candidates:
            return self._sorting_value_asc(score_candidates)[0], num
        else: # fallback
            return self.non_score_suit_min_value()
    #5
    def score_suit_max_value(self):
        num = 5
        global SCORE_CARDS
        score_candidates = [card for card in self.candidates if card.toString() in SCORE_CARDS]
        if score_candidates:
            return self._sorting_value_asc(score_candidates)[len(score_candidates)-1], num
        else: # fallback
            return self.non_score_suit_max_value()
    #6
    def non_score_suit_min_value(self):
        num = 6
        global SCORE_CARDS
        normal_candidates = [card for card in self.candidates if card.toString() not in SCORE_CARDS]
        if normal_candidates:
            return self._sorting_value_asc(normal_candidates)[0], num
        else: # fallback
            return self.score_suit_min_value()
    
    #7
    def non_score_suit_max_value(self):
        num = 7
        global SCORE_CARDS
        normal_candidates = [card for card in self.candidates if card.toString() not in SCORE_CARDS]
        if normal_candidates:
            return self._sorting_value_asc(normal_candidates)[len(normal_candidates)-1], num
        else: # fallback
            return self.score_suit_max_value()
    #8
    def same_suit_smaller(self):
        num = 8
        # Not first player
        if self.round_cards:
            target_suit = self.round_cards[0].suit # base suit
            target_can = [card for card in self.candidates if card.suit==target_suit]
            target_round = [card for card in self.round_cards if card.suit==target_suit]
            # Candidates and base suit are the same
            if target_can:
                asc_round = self._sorting_value_asc(target_round)
                asc_can = self._sorting_value_asc(target_can)
                asc_can.reverse()
                for c in asc_can:
                    if c.value < asc_round[len(asc_round)-1].value:
                        return c, num
                # No smaller in candidates. return smallest
                return asc_can[len(asc_can)-1], num
            else: # Candidates are in other suit
                return self.diff_suit_non_score()
        return self.least_suit_min_value()
           
    #9
    def same_suit_larger(self):
        num = 9
        # Choose the same suit card that is a bit larger 
        if self.round_cards:
            target_suit = self.round_cards[0].suit # base suit
            target_can = [card for card in self.candidates if card.suit==target_suit]
            target_round = [card for card in self.round_cards if card.suit==target_suit]
            if target_can:
                asc_round = self._sorting_value_asc(target_round)
                asc_can = self._sorting_value_asc(target_can)
                for c in asc_can:
                    if c.value > asc_round[len(asc_round)-1].value:
                        return c, num
                # No larger in candidates. return largest
                return asc_can[len(asc_can)-1], num
            else: # Candidates are in other suit
                return self.diff_suit_score()
        return self.least_suit_max_value()

    #10
    def diff_suit_score(self):
        num = 10
        # Diff from base. Choose the card that is a bit smaller than the largest round card
        if self.round_cards:
            target_suit = self.round_cards[0].suit # base suit
            target_can = [card for card in self.candidates if card.suit==target_suit] #has same suit cards, must hand out
            if target_can:
                return self.same_suit_smaller()
            else: # diff from base
               return self.score_suit_min_value()
        # First
        return self.most_suit_min_value()
            
    #11
    def diff_suit_non_score(self):
        num = 11
        # Diff from base. Choose the card that is a bit larger than the largest round card 
        if self.round_cards:
            target_suit = self.round_cards[0].suit # base suit
            target_can = [card for card in self.candidates if card.suit==target_suit] #has same suit cards, must hand out
            if target_can:
                return self.same_suit_larger()
            else: # diff from base
                return self.non_score_suit_min_value()
        # First
        return self.most_suit_max_value()


    def _is_uni_suit(self, cards):
        suit = collections.defaultdict(list)
        if cards:
            for card in cards:
                c = Card(card)
                suit[c.suit] += 1
            if len(suit.keys()) == 1:
                return True
        return False
    
    def _sorting_suit(self, suit_dict, reverse=False):
        return sorted(suit_dict.items(), key=lambda d: d[1], reverse=reverse)
    
    def _pick_suit_cards(self, suit, allcards):
       return [card for card in allcards if card.suit == suit]
           
    def _sorting_value_asc(self, cards):
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
                return _quicksort(minor)+pivotlist+_quicksort(larger)
        
        return _quicksort(cards)
        
def _assert_unisuit_candidates(s):
    print("Candidates:{}, Round Cards:{}".format(s.candidates,s.round_cards))
    # uni candidates
    # uni_0 : least suit min value
    result, actual_action = s.dispatcher(0)
    assert (result.toString() == 'JC'), 'uni_0 failed {}'.format(result.toString())
    # uni_1 : least suit max value
    result, actual_action= s.dispatcher(1)
    assert (result.toString() == 'AC'), 'uni_1 failed {}'.format(result.toString())
    # uni_2 : most suit min value
    result, actual_action= s.dispatcher(2)
    assert (result.toString() == 'JC'), 'uni_2 failed {}'.format(result.toString())
    # uni_3 : most suit max value
    result, actual_action= s.dispatcher(3)
    assert (result.toString() == 'AC'), 'uni_3 failed {}'.format(result.toString())
    # uni_4 : score suit min value
    result, actual_action= s.dispatcher(4)
    print ('uni_4 fallback {} choice {}'.format(actual_action, result.toString()))
    # uni_5 : score suit max value
    result, actual_action= s.dispatcher(5)
    print ('uni_5 fallback {} choice {}'.format(actual_action, result.toString()))
    # uni_6 : non_score suit min value
    result, actual_action= s.dispatcher(6)
    assert (result.toString() == 'JC'), 'uni_6 failed {}'.format(result.toString())
    # uni_7 : non_score suit max value
    result, actual_action= s.dispatcher(7)
    assert (result.toString() == 'AC'), 'uni_7 failed {}'.format(result.toString())
    # uni_8 : same suit smaller value
    result, actual_action= s.dispatcher(8)
    assert (result.toString() == 'JC'), 'uni_8 failed {}'.format(result.toString())
    # uni_9 : same suit larger value
    result, actual_action= s.dispatcher(9)
    assert (result.toString() == 'JC'), 'uni_9 failed {}'.format(actual_action, result.toString())
    # uni_10 : diff suit score value
    result, actual_action= s.dispatcher(10)
    print ('uni_10 fallback {} choice {}'.format(actual_action, result.toString()))
    # uni_11 : diff suit non score value
    result, actual_action= s.dispatcher(11)
    print ('uni_11 fallback {} choice {}'.format(actual_action,result.toString()))

def _assert_multisuit_candidates(s):
    print("Candidates:{}, Round Cards:{}".format(s.candidates,s.round_cards))
    # multi candidates
    # least suit min value
    # multi_0 : least suit min value
    result, actual_action= s.dispatcher(0)
    assert (result.toString() == 'JC'), 'multi_0 failed {}'.format(result.toString())
    # multi_1 : least suit max value
    result, actual_action= s.dispatcher(1)
    assert (result.toString() == 'QC'), 'multi_1 failed {}'.format(result.toString())
    # multi_2 : most suit min value
    result, actual_action= s.dispatcher(2)
    assert (result.toString() == '5S'), 'multi_2 failed {}'.format(result.toString())
    # multi_3 : most suit max value
    result, actual_action= s.dispatcher(3)
    assert (result.toString() == 'KS'), 'multi_3 failed {}'.format(result.toString())
    # multi_4 : score suit min value
    result, actual_action= s.dispatcher(4)
    assert (result.toString() == 'QS'), 'multi_4 failed {}'.format(result.toString())
    # multi_5 : score suit max value
    result, actual_action= s.dispatcher(5)
    assert (result.toString() == 'QS'), 'multi_5 failed {}'.format(result.toString())
    # multi_6 : non_score suit min value
    result, actual_action= s.dispatcher(6)
    assert (result.toString() == '4D'), 'multi_6 failed {}'.format(result.toString())
    # multi_7 : non_score suit max value
    result, actual_action= s.dispatcher(7)
    assert (result.toString() == 'AD'), 'multi_7 failed {}'.format(result.toString())
    # multi_8 : same suit smaller value
    result, actual_action= s.dispatcher(8)
    print ('multi_8 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_9 : same suit larger value
    result, actual_action= s.dispatcher(9)
    print ('multi_9 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_10 : diff suit score value
    result, actual_action= s.dispatcher(10)
    print ('multi_10 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_11 : diff suit non score value
    result, actual_action= s.dispatcher(11)
    print ('multi_11 fallback {} choice {}'.format(actual_action, result.toString()))

def _assert_multisuit_candidates_not_first(s):
    print("Candidates:{}, Round Cards:{}".format(s.candidates,s.round_cards))
    # multi candidates
    # least suit min value
    # multi_0 : least suit min value
    result, actual_action= s.dispatcher(0)
    assert (result.toString() == '9D'), 'multi_0 failed {}'.format(result.toString())
    # multi_1 : least suit max value
    result, actual_action= s.dispatcher(1)
    assert (result.toString() == 'JD'), 'multi_1 failed {}'.format(result.toString())
    # multi_2 : most suit min value
    result, actual_action= s.dispatcher(2)
    assert (result.toString() == '7S'), 'multi_2 failed {}'.format(result.toString())
    # multi_3 : most suit max value
    result, actual_action= s.dispatcher(3)
    assert (result.toString() == 'AS'), 'multi_3 failed {}'.format(result.toString())
    # multi_4 : score suit min value
    result, actual_action= s.dispatcher(4)
    print ('multi_4 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_5 : score suit max value
    result, actual_action= s.dispatcher(5)
    print ('multi_5 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_6 : non_score suit min value
    result, actual_action= s.dispatcher(6)
    assert (result.toString() == '7S'), 'multi_6 failed {}'.format(result.toString())
    # multi_7 : non_score suit max value
    result, actual_action= s.dispatcher(7)
    assert (result.toString() == 'AS'), 'multi_7 failed {}'.format(result.toString())
    # multi_8 : same suit smaller value
    result, actual_action= s.dispatcher(8)
    print ('multi_8 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_9 : same suit larger value
    result, actual_action= s.dispatcher(9)
    print ('multi_9 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_10 : diff suit score value
    result, actual_action= s.dispatcher(10)
    print ('multi_10 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_11 : diff suit non score value
    result, actual_action= s.dispatcher(11)
    print ('multi_11 fallback {} choice {}'.format(actual_action, result.toString()))
   
def _assert_heart_candidates(s):
    print("Candidates:{}, Round Cards:{}".format(s.candidates,s.round_cards))
    # multi candidates
    # least suit min value
    # multi_0 : least suit min value
    result, actual_action= s.dispatcher(0)
    assert (result.toString() == '2H'), 'multi_0 failed {}'.format(result.toString())
    # multi_1 : least suit max value
    result, actual_action= s.dispatcher(1)
    assert (result.toString() == 'TH'), 'multi_1 failed {}'.format(result.toString())
    # multi_2 : most suit min value
    result, actual_action= s.dispatcher(2)
    assert (result.toString() == '2H'), 'multi_2 failed {}'.format(result.toString())
    # multi_3 : most suit max value
    result, actual_action= s.dispatcher(3)
    assert (result.toString() == 'TH'), 'multi_3 failed {}'.format(result.toString())
     # multi_4 : score suit min value
    result, actual_action= s.dispatcher(4)
    assert (result.toString() == '2H'), 'multi_4 failed {}'.format(result.toString())
    # multi_5 : score suit max value
    result, actual_action= s.dispatcher(5)
    assert (result.toString() == 'TH'), 'multi_5 failed {}'.format(result.toString())
    # multi_6 : non_score suit min value
    result, actual_action= s.dispatcher(6)
    print ('multi_6 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_7 : non_score suit max value
    result, actual_action= s.dispatcher(7)
    print ('multi_7 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_8 : same suit smaller value
    result, actual_action= s.dispatcher(8)
    assert (result.toString() == '5H'), 'multi_8 failed {}'.format(result.toString())
    # multi_9 : same suit larger value
    result, actual_action= s.dispatcher(9)
    assert (result.toString() == '9H'), 'multi_9 failed {}'.format(result.toString())
    # multi_10 : diff suit score value
    result, actual_action= s.dispatcher(10)
    print ('multi_10 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_11 : diff suit score value
    result, actual_action= s.dispatcher(11)
    print ('multi_11 fallback {} choice {}'.format(actual_action, result.toString()))
    
def _assert_heart_normal_candidates(s):
    print("Candidates:{}, Round Cards:{}".format(s.candidates,s.round_cards))
    # Strategy(['KH', '7H', 'JC', '8D'],['5S','QS']))
    # multi candidates
    # least suit min value
    # multi_0 : least suit min value
    result, actual_action = s.dispatcher(0)
    assert (result.toString() == 'JC'), 'multi_0 failed {}'.format(result.toString())
    # multi_1 : least suit max value
    result, actual_action = s.dispatcher(1)
    assert (result.toString() == 'JC'), 'multi_1 failed {}'.format(result.toString())
    # multi_2 : most suit min value
    result, actual_action = s.dispatcher(2)
    assert (result.toString() == '7H'), 'multi_2 failed {}'.format(result.toString())
    # multi_3 : most suit max value
    result, actual_action = s.dispatcher(3)
    assert (result.toString() == 'KH'), 'multi_3 failed {}'.format(result.toString())
     # multi_4 : score suit min value
    result, actual_action = s.dispatcher(4)
    assert (result.toString() == '7H'), 'multi_4 failed {}'.format(result.toString())
    # multi_5 : score suit max value
    result, actual_action = s.dispatcher(5)
    assert (result.toString() == 'KH'), 'multi_5 failed {}'.format(result.toString())
    # multi_6 : non_score suit min value
    result, actual_action = s.dispatcher(6)
    assert (result.toString() == '8D'), 'multi_4 failed {}'.format(result.toString())
    # multi_7 : non_score suit max value
    result, actual_action = s.dispatcher(7)
    assert (result.toString() == 'JC'), 'multi_4 failed {}'.format(result.toString())
    # multi_8 : same suit smaller value
    result, actual_action = s.dispatcher(8)
    print ('multi_8 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_9 : same suit larger value
    result, actual_action = s.dispatcher(9)
    print ('multi_9 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_10 : multi suit smaller value
    result, actual_action  = s.dispatcher(10)
    print ('multi_10 fallback {} choice {}'.format(actual_action, result.toString()))
    # multi_11 : multi suit larger value
    result, actual_action = s.dispatcher(11)
    print ('multi_11 fallback {} choice {}'.format(actual_action, result.toString()))
       
if __name__ == "__main__":
    s = Strategy()
    
    s.set_candidates(['AC', 'QC', 'JC'])
    s.set_roundcards(['2C','5C','3C'])
    _assert_unisuit_candidates(s)
    s.reset_can_round()

    s.set_candidates(['KS', 'QS', 'JS', '8S', '7S', '5S', 'QC', 'JC', 'AD', '8D', '7D', '4D'])
    _assert_multisuit_candidates(s)
    s.reset_can_round()

    s.set_candidates(['AS', 'JS', '9S', '7S', 'JD', '9D'])
    s.set_roundcards(['2C','TD','4C'])
    _assert_multisuit_candidates_not_first(s)
    s.reset_can_round()

    s.set_candidates(['TH', '9H', '5H', '4H', '3H', '2H'])
    s.set_roundcards(['6H','QS','4C'])
    _assert_heart_candidates(s)
    s.reset_can_round()
 
    s.set_candidates(['KH', '7H', 'JC', '8D'])
    s.set_roundcards(['5S','QS'])
    _assert_heart_normal_candidates(s)
    s.reset_can_round()

    