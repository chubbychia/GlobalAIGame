import logging
import os
class Log(object):
    def __init__(self,is_debug=False):
        self.is_debug=is_debug
        self.msg=None
        self.logger = logging.getLogger('hearts_logs')
        if os.path.exists("/log"):
            hdlr = logging.FileHandler('/log/hearts_logs.log')
        else:
            hdlr = logging.FileHandler('hearts_logs.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
   
    def show_message(self,msg):
        if self.is_debug:
            print(msg)
            
    def save_logs(self,msg):
        self.logger.info(msg)
   
    def save_errors(self,msg):
        self.logger.error(msg)
