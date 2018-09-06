#! /usr/bin/env python
# -*- coding:utf-8 -*-

from websocket import create_connection
import sys
import json
from bot import HeartPlayBot
from utils.log import Log


IS_DEBUG=False
IS_SAVE_DATA=False
system_log=Log(IS_DEBUG)


class PokerSocket(object):
    ws = ""
    def __init__(self,player_name,player_number,token,connect_url,poker_bot):
        self.player_name=player_name
        self.connect_url=connect_url
        self.player_number=player_number
        self.poker_bot=poker_bot
        self.token=token

  
    def takeAction(self,action, data):
        if action=="new_game":
            self.poker_bot.new_game(data)
        # unit : episode
        # init also reset Player
        # init state (init value = 0)
        # init strategy
        elif action=="new_deal":
            self.poker_bot.new_deal(data)
        elif action=="new_round":
            self.poker_bot.new_round(data)
        # rule-based pick passed card
        elif action=="pass_cards":
            pass_cards=self.poker_bot.pass_cards(data)
            self.ws.send(json.dumps(
                {
                    "eventName": "pass_my_cards",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "cards": pass_cards
                    }
                }))
        elif action=="receive_opponent_cards":
            self.poker_bot.receive_opponent_cards(data)
        # set 1 to received + owned cards 
        elif action=="pass_cards_end":
            self.poker_bot.pass_cards_end(data)   
        elif action=="expose_cards":
            export_cards = self.poker_bot.expose_my_cards(data)
            if export_cards!=None:
                self.ws.send(json.dumps(
                    {
                       "eventName": "expose_my_cards",
                       "data": {
                           "dealNumber": data['dealNumber'],
                           "cards": export_cards
                       }
                    }))
         # set 1 to exposed card 
        elif action=="expose_cards_end":
            self.poker_bot.expose_cards_end(data)
        # predict
        # set action
        elif action=="your_turn":
            pick_card = self.poker_bot.pick_card(data)
            message="Send message:{}".format(json.dumps(
                {
                    "eventName": "pick_card",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "roundNumber": data['roundNumber'],
                        "turnCard": pick_card
                    }
                }))
            system_log.show_message(message)
            system_log.save_logs(message)
            self.ws.send(json.dumps(
                {
                    "eventName": "pick_card",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "roundNumber": data['roundNumber'],
                        "turnCard": pick_card
                    }
                }))

        # set 2 to handed out card in the player's turn
        elif action=="turn_end":
            self.poker_bot.turn_end(data)
        # set -1 to all dumpted cards
        # set 3 to my score cards location over dumpted cards
        # set 4/5/6 to oppo1/2/3 score cards location over dumpted cards
        # set TC eaten if it shows -> idx 53 (TC) to 1
        # set reward 
        # memorize the this round
        # reset strategy
        elif action=="round_end":
            self.poker_bot.round_end(data)
        # train
        # reset player_dict
        elif action=="deal_end":
            self.poker_bot.deal_end(data)
            self.poker_bot.reset_card_his()
            self.poker_bot.reset_player_dict()
        elif action=="game_end":
            self.poker_bot.game_over(data)
            self.ws.close()
    def doListen(self):
        try:
            self.ws = create_connection(self.connect_url)
            self.ws.send(json.dumps({
                "eventName": "join",
                "data": {
                    "playerNumber":self.player_number,
                    "playerName":self.player_name,
                    "token":self.token
                }
            }))
            while 1:
                result = self.ws.recv()
                msg = json.loads(result)
                event_name = msg["eventName"]
                data = msg["data"]
                system_log.show_message(event_name)
                system_log.save_logs(event_name)
                system_log.show_message(data)
                system_log.save_logs(data)
                self.takeAction(event_name, data)
        except Exception as e:
            system_log.show_message(e)
            system_log.save_errors(e)
            self.doListen()


def main():
    argv_count=len(sys.argv)
    if argv_count>2:
        player_name = sys.argv[1]
        player_number = sys.argv[2]
        token= sys.argv[3]
        connect_url = sys.argv[4]
    else:
        player_name="JoJoTrain"
        player_number=777
        token="12345678"
        connect_url="ws://10.1.229.94:8080/"
    sample_bot=HeartPlayBot(player_name, system_log, IS_SAVE_DATA)
    myPokerSocket=PokerSocket(player_name,player_number,token,connect_url,sample_bot)
    myPokerSocket.doListen()

if __name__ == "__main__":
    main()