import logging

class Log(object):
    def __init__(self,is_debug=True):
        self.is_debug=is_debug
        self.msg=None
        self.logger = logging.getLogger('formula_logs')
        hdlr = logging.FileHandler('./log/formula_logs.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)
    def show_message(self,msg):
        if self.is_debug:
            print(msg)
    def save_logs(self,msg):
        self.logger.info(msg)