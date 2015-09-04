import argparse
import threading
import xmlrpc.client
import time
import math
import sys
from xmlrpc.server import SimpleXMLRPCServer

# table_spec['player'][#] is tuple ((int) stack, (bool) playing, (bool) betting)
def my_state(table_spec):
    players = table_spec.get('players', None)
    pocket_cards = table_spec.get('pocket_cards', None)
    pot = table_spec.get('pot', None)
    button = table_spec.get('button', None)
    tocall = table_spec.get('tocall', None)



class PlayerControl(threading.Thread):
    def __init__(self, host, port, threadID, name, stack=2000, playing=True, ai_flag=False):
        super(PlayerControl, self).__init__()
        self._server = xmlrpc.client.ServerProxy('http://localhost:8000')
        self.daemon = True

        self._ai_flag = ai_flag
        self._name = name
        self._host = host
        self._port = port
        self._threadID = threadID
        self._stack =  stack
        self._hand = []

    def run(self):
        # self._server.add_player(self._threadID, self._name, self._stack, self._host, self._port)
        table_state = self._server.get_table_state(self._threadID)
        print(table_state)
        while True:
            table_state_new = self._server.get_table_state(self._threadID)
            print(table_state)
            if table_state_new != table_state:
                table_state = table_state_new
                # self.show_table(table_state)

            self._server.start_game()
            time.sleep(10)
            if not table_state:
                print("not in hand... waiting")
                time.sleep(10)
                continue

    # def show_table(self, table_spec):

    def update_localstate(table_state):
        self._stack = table_state.get('stack')
        self._hand = table_state.get('pocket')

    def player_move(self, table_state):
        update_localstate(table_state)
        show_table(table_state)
        tocall = table_state.get('tocall')

        if not self._ai_flag:
            if tocall == 0:
                print("1) Raise")
                print("2) Check")
                choice = input("Choose your option: ")
                if choice == 1:
                    choice2 = input("How much would you like to raise? (min = {}, max = {})".format(tocall,self._stack))
                    while choice2 < tocall:
                        choice2 = input("(Invalid input) How much would you like to raise? (min = {}, max = {})".format(tocall,self._stack))
                    move = ('raise',min(choice2, self._stack))
                    self._stack -= choice2
                if choice ==2:
                    move = ('check', 0)
            else:
                print("1) Raise")
                print("2) Call")
                print("3) Fold")
            choice = input("Choose your option: ")
            if choice == 1:
                choice2 = input("How much would you like to raise? (min = {}, max = {})".format(tocall,self._stack))
                while choice2 < tocall:
                    choice2 = input("(Invalid input) How much would you like to raise? (min = {}, max = {})".format(tocall,self._stack))
                move = ('raise',min(choice2, self._stack))
                self._stack -= choice2
            elif choice == 2:
                move = ('call', tocall)
                self._stack -= tocall
            elif choice == 3:
                move = ('fold', -1)
            return move
        else:
            bet_size = nnholdem(table_state)
            if bet_size < tocall:
                if bet_size >= self._stack:
                    move = ('allin', self._stack)
                else:
                    move = ('fold',-1)
            elif bet_size > tocall:
                bet_size -= bet_size % table_state.get('bigblind')
                if bet_size >tocall:
                    self._stack -= min(bet_size, self._stack)
                    move = ('raise', min(bet_size, self._stack))
                else:
                    move = ('call', tocall)
            elif bet_size == tocall:
                self._stack -= tocall
                move = ('call', tocall)
            return move

    def add_to_server(self):
        self._server.add_player(self._threadID, self._name, self._stack, self._host, self._port)

class PlayerProxy(object):
    def __init__(self,player):
        self._player = player

    def player_move(self, output_spec):
        print(output_spec)
        return ('raise',50)

    # def get_table_state(self, threadID):
    def add_to_server(self):
        self._player.add_to_server()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("num_players", type=int, default="2")
    parser.add_argument("ai", type=bool, default=True)
    args = parser.parse_args()


    players = []
    for num in range(args.num_players):
        player = PlayerControl("localhost", 8001+num, num, args.ai)
        player_proxy = PlayerProxy(player)

        players.append(player)
        server = SimpleXMLRPCServer(("localhost", 8001+num), logRequests=False, allow_none=True)
        server.register_instance(player_proxy, allow_dotted_names=True)
    for player in players:
        player.add_to_server()
    for player in players:
        player.start()
        player.join()


    # server = SimpleXMLRPCServer(("0.0.0.0", 8000), Handler)

    # server.register_introspection_functions()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        server.server_close()
        sys.exit(0)