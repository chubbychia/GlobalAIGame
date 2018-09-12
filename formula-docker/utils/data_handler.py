import tempfile

class FileModifierError(Exception):
    pass

class FileModifier(object):

    def __init__(self, fname):
        self.__write_dict = {}
        self.__filename = fname
        self.__tempfile = tempfile.TemporaryFile()
        with open(fname, 'rb') as fp:
            for line in fp:
                self.__tempfile.write(line)
        self.__tempfile.seek(0)

    def write(self, s, line_number = 'END'):
        if line_number != 'END' and not isinstance(line_number, (int, float)):
            raise FileModifierError("Line number %s is not a valid number" % line_number)
        try:
            self.__write_dict[line_number].append(s)
        except KeyError:
            self.__write_dict[line_number] = [s]

    def writeline(self, s, line_number = 'END'):
        self.write('%s\n' % s, line_number)

    def writelines(self, s, line_number = 'END'):
        for ln in s:
            self.writeline(s, line_number)

    def __popline(self, index, fp):
        try:
            ilines = self.__write_dict.pop(index)
            for line in ilines:
                fp.write(line)
        except KeyError:
            pass

    def close(self):
        self.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        with open(self.__filename,'w') as fp:
            for index, line in enumerate(self.__tempfile.readlines()):
                self.__popline(index, fp)
                # fp.write(line)
            for index in sorted(self.__write_dict):
                for line in self.__write_dict[index]:
                    fp.write(line)
        self.__tempfile.close()



class TrainingDataCollector(object):

    def __init__(self,path):
        self.states=[]
        self.hand_cards_record = []
        self.played_cards=[]
        self.action=[]
        self.order=[]
        self.text_file_path=path
        text_file = open(self.text_file_path, "w")
        text_file.close()
        #with FileModifier(self.text_file_path) as fp:
            #message="round,position,hcard1,hcard2,hcard3,hcard4,hcard5,hcard6,hcard7,hcard8,hcard9,hcard10,hcard11,hcard12,hcard13,rcard1,rcard2,rcard3,rcard4,1_0,1_1,1_2,1_3,1_4,1_5,1_6,1_7,1_8,1_9,1_10,1_11,1_12,2_0,2_1,2_2,2_3,2_4,2_5,2_6,2_7,2_8,2_9,2_10,2_11,2_12,2_13,2_14,2_15,2_16,2_17,2_18,2_19,2_20,2_21,2_22,2_23,3_0,3_1,3_2,3_3,3_4,3_5,3_6,3_7,3_8,3_9,4_0,4_1,4_2,4_3,4_4,4_5,4_6,4_7,4_8,4_9,4_10,4_11,4_12,4_13,5_0,5_1,5_2,5_3,5_4,5_5,5_6,5_7,5_8,5_9,5_10,5_11,strategy,score"
            #fp.writeline(message)  # To write the title
    def set_record(self,order,played_cards, state,action,hand_cards):
        self.order.append(order)
        self.played_cards.append(played_cards)
        self.states.append(state)
        self.action.append(action)
        self.hand_cards_record.append(hand_cards)

    def save_data_direct(self,message):
        with FileModifier(self.text_file_path) as fp:
            fp.writeline(message)  # To write at the end of the file
        self.reflush()

    def save_records_and_flush(self,rewards,rank):
        with FileModifier(self.text_file_path) as fp:
            for i in range(len(self.order)):
                round=i+1
                message= str(round)+","+str(self.order[i])+","
                hand_cards=self.hand_cards_record[i]
                for card in hand_cards:
                    message += card.to_string() + ","
                remain=13-len(hand_cards)
                if remain>0:
                    for j in range(remain):
                        message += "null,"
                round_cards=self.played_cards[i]
                for card in round_cards:
                    message+=card.to_string()+","
                current_state=self.states[i]
                for state_value in current_state:
                    message += str(state_value) + ","
                message+=str(self.action[i])+","+str(rewards[i])+","
                message +=str(rank)
                fp.writeline(message)  # To write at the end of the file
        self.reflush()

    def reflush(self):
        self.states=[]
        self.hand_cards_record = []
        self.played_cards=[]
        self.action=[]
        self.order=[]

