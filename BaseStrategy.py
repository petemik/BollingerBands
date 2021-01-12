from utils import *
import pandas as pd


class BaseStrategy:
    """
    This is the parent to all strategies that will be created and has the fundamental necessary properties of any
    strategy. i.e. buy long, buy short, close position, transaction dataframes and return dataframes
    """
    def __init__(self):
        """

        """
        self.rets_df = pd.DataFrame(columns=['symbol', 'entry_date', 'close_date', 'days_held', 'direction',
                                             'entry_price', 'close_price', 'return'])
        self.trans_df = pd.DataFrame(columns=['symbol', 'date', 'direction', 'close', 'price'])
        # This can be overwritten in the actual strategy
        self.stop_loss_perc = 0.1
        self.open_pos = None
        self.entry_price = None
        self.target_price = None
        self.stop_price = None
        self.entry_date = None
        self.close_price = None

    def _reset_vars(self):
        self.entry_price = None
        self.entry_date = None
        self.close_price = None
        self.open_pos = None
        self.target_price = None
        self.stop_price = None

    def _open_short(self, tckr, row):
        self._open_pos(tckr, row, direction=-1)

    def _open_long(self, tckr, row):
        self._open_pos(tckr, row, direction=1)

    def _open_pos(self, tckr, row, direction):
        self.open_pos = direction
        self.entry_date = row['date']
        self.entry_price = row['next_open']
        self.stop_price = (1-direction*self.stop_loss_perc)*self.entry_price
        self.trans_df = self.trans_df.append(
            {'symbol': tckr, 'date': self.entry_date, 'direction': direction, 'close': 0, 'price': self.entry_price},
            ignore_index=True)

    def _close_pos(self, tckr, row):
        close_date = row['date']
        close_price = row['next_open']
        returns = (close_price / self.entry_price - 1) * self.open_pos
        days_held = calc_diff(self.entry_date, close_date, type='days')
        self.trans_df = self.trans_df.append(
            {'symbol': tckr, 'date': close_date, 'direction': self.open_pos, 'close': 1, 'price': close_price},
            ignore_index=True)
        self.rets_df = self.rets_df.append({'symbol': tckr, 'entry_date': self.entry_date, 'close_date': close_date,
                                            'days_held': days_held, 'direction': self.open_pos,
                                            'entry_price': self.entry_price, 'close_price': close_price,
                                            'return': returns}, ignore_index=True)
        # reset Variables
        self._reset_vars()

    def run(self):
        # This should include
        print("Make sure you include a run function in the Strategy class")

    def _set_params(self, params):
        # See skeleton class file for an idea how it works
        print("Make sure you include this function in the Strategy class")



