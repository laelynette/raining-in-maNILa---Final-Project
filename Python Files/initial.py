import pandas as pd
import numpy as np
import math


class air_predictor:
    def __init__(self, dataset, params):
      ## User inputs (numeric)
      self.orig_code = ''
      self.dest_code = ''
      self.user_airlines = 0
      self.date_range = list(params[0])
      self.predicted = params[1]

      self.init_start = ''
      self.place = []
      self.dataset = dataset

    def separate_strings_with_dash(self):
        string_list = self.dataset['Route'].values
        # Split each string in the list by "-" and flatten the result
        separated_strings = [substring for string in string_list for substring in string.split("-")]
        waypoint =  list(sorted(set(separated_strings)))
        self.place = waypoint

        return waypoint

    def delay_cat(self, idx):
        if np.round(float(self.predicted[idx]), 2) >= 15:
            return True
        else:
            return False

    def choose_delay(self, delay_input):
        delay_idx = self.date_range.index(delay_input)
        #is_delay = self.delay_cat(delay_idx)

        self.init_start = delay_input
        #return is_delay

    def choose_orig(self, start):
        self.orig_code = start.upper()
        return str(start.upper())

    def choose_dest(self, end):
        self.dest_code = end.upper()
        return str(end.upper())

    
    def date_parse(self):
        days_31 = ['01', '03', '05', '07', '08', '10', '12']
        init_date = self.init_start

        start = init_date[:8] + '01' + init_date[10:]

        if init_date[5:7] in days_31:
            end = init_date[:8] + '31' + init_date[10:]
        elif init_date[5:7] == '02' and int(init_date[0:4])%4 != 0:
            end = init_date[:8] + '28' + init_date[10:]
        elif init_date[5:7] == '02' and int(init_date[0:4])%4 == 0:
            end = init_date[:8] + '29' + init_date[10:]
        else:
            end = init_date[:8] + '30' + init_date[10:]

        return start, end
    
    def run_airlines(self):
        #self.choose_delay()
        self.separate_strings_with_dash(self.dataset['Route'].values)
        #self.choose_orig_dest()

        return self.orig_code, self.dest_code, self.place