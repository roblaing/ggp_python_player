# -*- coding: utf-8 -*-
"""
Avoid memory usage problems by not caching the game_tree
"""
import BaseHTTPServer, time, argparse, subprocess, random, itertools

HOST_NAME = "127.0.0.1"
PORT = 9147
PLAYER_NAME = "roblaing"
PROLOG = ['swipl','-s', '/dev/stdin']
# PROLOG = ['yap','-L', '/dev/stdin']
TIME_MARGIN = 0.9
DOT_FILE_NAME = False


################################################################################################
# translators

def str2list(ret_str):
    """Convert output of proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    into a python list
    """
    if ret_str.find('[') == -1:
        return ret_str
    nexts = ret_str[1:-1].split(']')
    nexts = [(base[2:] if base[0:2] == ',[' else base[1:]) for base in nexts if len(base) > 0]
    return tuple(sorted(set(nexts)))
    
def state2trues(state):
    """Convert a state given as a whitespace separated list of prolog-style clauses
    into new line separted 'true(base).' statements to append to prolog rules.
    """
    return "\n".join(["true(" + base + ")." for base in state.split(" ")]) + "\n"

   
################################################################################################

def depthcharge(state, game, timeout):
    if findterminalp(state, game) or time.time() > timeout:
        return findrewards(state, game)
    else:
        move = random.choice(findmoves(state, game))
        next_state = findnext(move, state, game)
        return depthcharge(next_state, game, timeout)

def montecarlo(move, state, game, timeout):
    # print time.time() - timeout
    next_state = findnext(move, state, game)
    count = 1 # start with 1 to avoid divide by zero problems
    values = [0 for dummy in findroles(game)]
    while time.time() < timeout:
        new_values = depthcharge(next_state, game, timeout)
        values = [values[jdx] + new_values[jdx] for jdx in range(len(values))]  
        count += 1
    return (values, count)

def bestmove(role, state, game, timeout):
    idx = findroles(game).index(role)
    actions = findmoves(state, game)
    time_per_move = (timeout - time.time())/float(len(actions))
    # print time_per_move
    move = actions[0]
    av_value = 0.0
    time_count = len(actions) - 1
    for action in actions:
        timelimit = timeout - time_per_move * time_count
        time_count -= 1
        (values, count) = montecarlo(action, state, game, timelimit)
        # print (action, values, count)
        result = float(values[idx])/float(count) # if count > 0 else 0.0
        # print action, result
        if result > av_value:
           av_value = result
           move = action
    return move[idx]

##############################################################################

def findroles(game):
    return game['roles']

def findinits(game):
    """
    Returns a string of prolog-style (but no dots, white space seperated) propositions
    which can be used as a key for nodes in a dictionary or database
    """
    prolog = game['prolog_rules']
    prolog += 'main :- findall([B], init(B), L), write(L), halt.'
    proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    return " ".join(str2list(proc.communicate(input = prolog)[0]))

def findmoves(state, game):
    """
    Return a tuple of tuples for each players' permutation of moves
    Each move-tuple represents an edge from the current state to a new state
    """
    roles = findroles(game)
    prolog = game['prolog_rules']
    prolog += state2trues(state)
    prolog += 'main :- findall([R,M], legal(R,M), L), write(L), halt.'
    proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    legals = str2list(proc.communicate(input = prolog)[0])
    ret_lst = [set() for dummy in game['roles']]
    for legal in legals:
        idx = legal.index(',')
        ret_lst[roles.index(legal[:idx])].add(legal[idx + 1:])
    ret_lst = [sorted(list(move_set)) for move_set in ret_lst]
    edges = tuple(itertools.product(*ret_lst))
    return edges

def findnext(moves, state, game):
    """
    Returns a string of prolog-style (but no dots, white space seperated) propositions
    which can be used as a key for nodes in a dictionary or database
    moves is a tuple like ('move(4,1,3,1)', 'noop')
    state is a string in same format as returned strin
    game is a global dictionary
    """
    roles = findroles(game)
    prolog = game['prolog_rules']
    prolog += state2trues(state)
    for idx in range(len(moves)):
        if moves[idx] != 'noop':
            prolog += 'does(' + roles[idx] + ',' + moves[idx] + '). '
    prolog += 'main :- findall([B], next(B), L), write(L), halt. '
    proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    return " ".join(str2list(proc.communicate(input = prolog)[0]))

def findrewards(state, game):
    """
    Returns a list of values in same sequence as roles
    """
    roles = findroles(game)
    prolog = game['prolog_rules']
    prolog += state2trues(state)
    prolog += 'main :- findall([Role, N], goal(Role, N), L), write(L), halt. '
    proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    rewards = str2list(proc.communicate(input = prolog)[0])
    ret_lst = [0 for dummy in roles]
    for reward in rewards:
        idx = reward.index(',')
        ret_lst[roles.index(reward[:idx])] = int(reward[idx + 1:])
    return ret_lst

def findterminalp(state, game):
    """
    Boolean, true if terminal
    """
    prolog = game['prolog_rules']
    prolog += state2trues(state)
    prolog += "end :- terminal, write('True'). "
    prolog += "end :- \+terminal, write('False'). "
    prolog += 'main :- end, halt. '
    proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    return proc.communicate(input = prolog)[0] == 'True'
      
##################################################################################
# Helper functions for GGP protocol handlers


def rewrite_move(move):
    """
    Convert list to prolog string
    """
    if isinstance(move, str):
        return move
    ret_lst = []
    for item in move:
        if isinstance(item, list):
            ret_lst.append(item[0] + '(' + ",".join(item[1:]) + ')')
        else:
            ret_lst.append(item)
    return tuple(ret_lst)

def prolog_rules(rules):
    """
    Translate rules into prolog and return as a long string.
    Specific "trues" and queries are later appended to this on a case
    by case basis
    """
    def rewrite(rule):
        "Recursive helper for nested s-expressions"
        if all([isinstance(atom, str) for atom in rule]) and rule[0] == 'or':
            return '( ' + ' ; '.join(rule[1:]) + ' )'
        elif all([isinstance(atom, str) for atom in rule]) and rule[0] != '<=':
            return rule[0] + str(rule[1:]).replace('[', '(').replace(']', ')').replace("'", '')
        else:
            rule_copy = list(rule)
            for idx in range(len(rule)):
                if isinstance(rule[idx], list):
                    rule_copy[idx] = rewrite(rule_copy[idx])
            return rewrite(rule_copy)

    prolog = ':- set_prolog_flag(verbose, silent).\n'
    prolog += ':- initialization(main).\n'
    prolog += 'distinct(A, B) :- A \\= B.\n'
    # prolog += 'or(A, B) :- (A ; B). '
    for rule in rules:
        if rule[0] != '<=':
            next_rule = rewrite(rule) + '.\n'
        else:
            next_rule = rewrite(rule[1]) + ' :- ' + ", ".join([rewrite(body) \
              for body in rule[2:]]) + '.\n'
        prolog += next_rule
    return prolog


##########################################################

# GGP protocol handlers as described in http://logic.stanford.edu/ggp/chapters/chapter_04.html
# More up to date http://games.stanford.edu/index.php/communication-protocol

def info():
    return "( ( name " + PLAYER_NAME + " ) ( status available ) )"
    
def start(game_id, player, rules, startclock, playclock):
    # print(rules)
    global game
    timeout = time.time() + TIME_MARGIN * float(startclock)
    game = {}
    game['roles'] = [rule[1] for rule in rules if rule[0] == 'role']
    game['prolog_rules'] = prolog_rules(rules)
    game['playclock'] = playclock
    game['game_id'] = game_id
    game['player'] = player
    game['state'] = findinits(game)
    # print bestmove(game['player'], game['state'], game, timeout)
    return 'ready'

def play(game_id, move):
    global game
    move = rewrite_move(move)
    # print("Move: " + str(move))
    # quit game if moves become garbled due to timeouts or whatever 
    # if move not in ('nil', 'undefined') and move not in game['tree'][game['state']]['actions'].keys():
    #    return 'done'
    timeout = time.time() + TIME_MARGIN * float(game['playclock'])
    if move not in ('nil', 'undefined'):
        game['state'] = findnext(move, game['state'], game)
    return_move = bestmove(game['player'], game['state'], game, timeout)
    idx = return_move.find('(')
    if idx != -1:
        return_move = '( ' + return_move[:idx] + " " + " ".join(return_move[idx + 1: -1].split(',')) + ' )'
    # print ("Return move " + return_move)
    return return_move
    
def stop(game_id, move):
    # global game
    return 'done'

##########################################################################
 
def tokenize(chars):
    "Convert a string of characters into a list of tokens."
    return chars.replace('(', ' ( ').replace(')', ' ) ').split()

def parse(program):
    "Read a Scheme expression from a string."
    return read_from_tokens(tokenize(program))

def read_from_tokens(tokens):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif ')' == token:
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token):
    "constants are title case, everything else lower case"
    if token[0] == '?':
        return token[1:].title()
    else:
        return token.lower()

#################################################################################

# listener

def response(text):
    http.send_response(200)
    http.send_header("Content-type", "text/acl")
    http.send_header("Content-length", len(text))
    http.send_header("Access-Control-Allow-Origin", "*") # replace with origin
    http.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
    http.send_header("Access-Control-Allow-Headers", "Content-Type")
    http.send_header("Access-Control-Allow-Age", 86400)
    http.end_headers()
    http.wfile.write(text)

def http_handler(text):
    # print(text)
    result = parse(text)
    # print(result)
    if result[0].lower() == 'info':
        response(info())
    elif result[0].lower() == 'start':
        response(start(result[1], result[2], result[3], result[4], result[5]))
    elif result[0] == 'play':
        # print("Move " + str(result[2]))
        response(play(result[1], result[2]))
    elif result[0] == 'stop':
        response(stop(result[1], result[2]))
    elif result[0] == 'abort':
        response('done')
    else:
        print("Not sure how to respond to " + str(result))

class myHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        global http, origin   # origin commented out because of bug in ggp-base
        http = self
        origin = self.headers['Origin']
        length = int(self.headers['Content-length'])
        http_handler(self.rfile.read(length))
 
try:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-n", "--hostname", help="hostname, default " + HOST_NAME, type=str)
    arg_parser.add_argument("-p", "--port", help="port to listen at, default " + str(PORT), type=int)
    args = arg_parser.parse_args()
    if args.port:
        PORT = args.port
    if args.hostname:
        HOST_NAME = args.hostname
    server = BaseHTTPServer.HTTPServer((HOST_NAME, PORT), myHTTPRequestHandler)
    print("Started gameplayer on " + str(PORT))
    server.serve_forever()
 
except KeyboardInterrupt:
    print("^C received, shutting down the web server")
    server.server_close()


