import random
from Exchange import Exchange
from Order import OType, Order

# Import Trader strategies:
from Trader import TType, Trader
from Giveaway import Giveaway
from ZIU import ZIU
from ZIC import ZIC
from ZIP import ZIP

class Environment:

    def __init__(self, max_time = 180, min_price = 1, max_price = 1000, replenish_orders = False):
        self.maxtime = max_time
        self.minprice = min_price
        self.maxprice = max_price
        self.replenish_orders = replenish_orders
        self.init = False

    def _get_observation(self):
        observation = {
            'lob': self.exchange.get_public_lob(self.time),
            'trader': self.traders['PLAYER']
        }
        return observation

    # TODO: improve order creation and assigning
    def _generate_order(self, trader_id, order_type, time):
        offset = random.randint(-10, 10)
        price = 50 + offset
        new_order = Order(trader_id, order_type, price, 1, time)
        return new_order

    def reset(self):
        self.exchange = Exchange(self.minprice, self.maxprice)
        self.time = 1
        self.done = False
        self.traders = self._populate_traders()
        self.init = True
        return self._get_observation()

    def step(self, player_action):
        if not self.init:
            raise RuntimeError('Error: step() function in environment called before reset()')

        balance = 0

        ## Shuffle traders in a random order
        trader_keys =  list(self.traders.keys())
        random.shuffle(trader_keys)

        ## Update the traders with the latest public lob
        for trader_key in trader_keys:
            self.traders[trader_key].update(self.exchange.get_public_lob(self.time))

        ## Process trader actions

        # In their random order, traders take an action
        for trader_key in trader_keys:
            trader = self.traders[trader_key]
            order = trader.action(player_action, self.time)
            output = None
            if order != None: # If an order is placed, process it
                output = self.exchange.process_order(order, self.time)
            if output != None: # If a trade occurred due to the order being placed, notify the parties involved
                trader1 = self.traders[output['party1']]
                trader2 = self.traders[output['party2']]
                trader1.notify_transaction(output)
                trader2.notify_transaction(output)
                if output['party1'] == 'PLAYER' or output['party2'] == 'PLAYER': # If the player trader was involved in the trade, this step's reward becomes the balance of the trade
                    player = self.traders['PLAYER']
                    balance = player.balance

        # Assign new orders to the traders who completed the previous ones if the exchange(experiment) rules say so
        # Here we could try preserving which trader bids and which
        # trader asks (chosen), or we could give them random orders (thus upsetting the balance)
        if self.replenish_orders == True:
            for trader_key in trader_keys:
                trader = self.traders[trader_key]
                if trader.order == None:
                    new_order = self._generate_order(trader.tid, trader.otype, self.time)
                    trader.assign_order(new_order)

        # Increment timestep
        if self.time >= self.maxtime:
            self.done = True
        self.time += 1

        observation = self._get_observation()
        reward = balance
        done = self.done
        info = ""
        if self.done: # Return the balance of each trader
            info = "BALANCES: \n"
            trader_keys =  list(self.traders.keys())
            for trader_key in trader_keys:
                trader = self.traders[trader_key]
                balance = trader.balance
                string = trader_key + ":" + str(trader.balance) + "\n"
                info = info + string

        return observation, reward, done, info

    def _populate_traders(self):

        # Create and return a trader of the specified type
        def create_trader(trader_type, trader_id, min_price, max_price):
            if trader_type == TType.GVWY:
                trader = Giveaway(trader_type, trader_id, min_price, max_price)
            elif trader_type == TType.ZIU:
                trader = ZIU(trader_type, trader_id, min_price, max_price)
            elif trader_type == TType.ZIC:
                trader = ZIC(trader_type, trader_id, min_price, max_price)
            elif trader_type == TType.ZIP:
                trader = ZIP(trader_type, trader_id, min_price, max_price)
            else:
                trader = Trader(trader_type, trader_id, min_price, max_price)
            return trader

        # Generates a trader and assigns an order to it
        def generate_trader(self, trader_id, trader_type, order_type, min_price, max_price):
            #trader = Trader(trader_type, trader_id, min_price, max_price) # TODO: Here for reference. Remove.
            trader = create_trader(trader_type, trader_id, min_price, max_price)
            new_order = self._generate_order(trader.tid, order_type, 0)
            trader.assign_order(new_order)
            return trader

        traders = {}

        tid = 'PLAYER'
        initial_otype = OType.BID if random.randint(0,1) == 0 else OType.ASK
        traders[tid] = generate_trader(self, tid, TType.PLAYER, initial_otype, self.minprice, self.maxprice)

        # TODO: For now, modify here to change NPC traders. Make it customizable in the future.
        for i in range(0, 10):
            tid = 'ZIP' + str(i)
            traders[tid] = generate_trader(self, tid, TType.ZIP, OType.BID, self.minprice, self.maxprice)
        for i in range(10, 20): # TODO: Add check and test in exchange so that two traders cannot have same tid
            tid = 'ZIP' + str(i)
            traders[tid] = generate_trader(self, tid, TType.ZIP, OType.ASK, self.minprice, self.maxprice)

        return traders

if __name__ == "__main__":

    environment = Environment(min_price = 1, max_price = 100, replenish_orders = True)
    i = 0
    totalreward = 0
    done = False
    observation = environment.reset()

    # ZIU STRATEGY
    def ziu_strategy(observation):

        # If the player has already traded, idle
        if observation['trader'].order == None:
            return None

        # Obtain details from observation
        time = observation['lob']['time']
        tid = observation['trader'].tid
        order_type = observation['trader'].order.otype
        min_price = observation['trader'].exchange_rules['minprice']
        max_price = observation['trader'].exchange_rules['maxprice']

        # Choose price
        price = random.randint(min_price,max_price)


        # Form and return order
        order = Order(tid, order_type, price, 1, time)
        return order
    #

    # ZIC STRATEGY
    def zic_strategy(observation):

        # If the player has already traded, idle
        if observation['trader'].order == None:
            return None

        # Obtain details from observation
        time = observation['lob']['time']
        tid = observation['trader'].tid
        order_price = observation['trader'].order.price
        order_type = observation['trader'].order.otype
        min_price = observation['trader'].exchange_rules['minprice']
        max_price = observation['trader'].exchange_rules['maxprice']

        # Choose price
        if order_type == OType.BID:
            price = random.randint(min_price,order_price)
        elif order_type == OType.ASK:
            price = random.randint(order_price, max_price)
        else:
            raise RuntimeError('Observation contains malformed order.')

        # Form and return order
        order = Order(tid, order_type, price, 1, time)
        return order
    #

    while not done:
        action = zic_strategy(observation)
        observation, reward, done, info = environment.step(action)
        totalreward += reward
        i += 1
    print("Tape:", observation['lob']['tape'])
    print("Balance at the end of session:", totalreward)
