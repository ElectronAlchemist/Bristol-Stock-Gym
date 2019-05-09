from enum import Enum

# An order can either be a BID or an ASK
class OType(Enum):
    BID = 'BID'
    ASK = 'ASK'

# an Order/quote has a trader id, a type (buy/sell) price, quantity, timestamp, and unique i.d.
class Order:

        def __init__(self, tid, otype, price, qty, time, qid = 0):
                self.tid = tid      # trader i.d.
                self.otype = otype  # order type
                self.price = price  # price
                self.qty = qty      # quantity
                self.time = time    # timestamp
                self.qid = qid      # quote i.d. (unique to each quote)

        def __str__(self):
                return '[%s %s P=%03d Q=%s T=%5.2f QID:%d]' % \
                       (self.tid, self.otype, self.price, self.qty, self.time, self.qid)
