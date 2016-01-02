# -*- coding: utf-8 -*-
"""
This is an implementation of the Game Description Language
with its subroutines described in
http://logic.stanford.edu/ggp/chapters/chapter_04.html
It is open source software written by a hobby programer, Robert Laing
https://github.com/roblaing/ggp_python_player
"""
from __future__ import print_function
import BaseHTTPServer, time, argparse, subprocess, random, itertools

HOST_NAME = "127.0.0.1"
PORT = 9147
PLAYER_NAME = "roblaing"
PROLOG = ['swipl','-s', '/dev/stdin']
# PROLOG = ['yap','-L', '/dev/stdin']
TIME_MARGIN = 0.9
DOT_FILE_NAME = False


def depthcharge(state, game, timeout):
    if findterminalp(state, game) or time.time() > timeout:
        if 'values' not in game['tree'][state]:
           findreward(findroles(game)[0], state, game)
        return game['tree'][state]['values']
    else:
        moves = findmoves(state, game)
        if len(moves) == 0:
            print(moves, state, findterminalp(state, game))
        move = random.choice(moves)
        next_state = findnext(move, state, game)
        return depthcharge(next_state, game, timeout)

def montecarlo(move, state, game, timeout):
    next_state = findnext(move, state, game)
    while time.time() < timeout:
        values = depthcharge(next_state, game, timeout)
        for idx in range(len(findroles(game))):
            game['tree'][state]['actions'][move]['score_count'][idx] += values[idx]
        game['tree'][state]['actions'][move]['score_count'][idx + 1] += 1
    return game['tree'][state]['actions'][move]['score_count']

def bestmove(role, state, game, timeout):
    idx = findroles(game).index(role)
    actions = findmoves(state, game)
    move = random.choice(actions)
    average_score = 0.0
    time_per_move = (timeout - time.time())/float(len(actions))
    for count in range(len(actions)):
        if 'score_count' not in game['tree'][state]['actions'][actions[count]]:
            game['tree'][state]['actions'][actions[count]]['score_count'] = [0 for dummy in findroles(game)] + [1]
        timelimit = timeout - time_per_move*(len(actions) - count - 1)
        scores = montecarlo(actions[count], state, game, timelimit)
        estimated_utility = float(scores[idx])/float(scores[-1])
        if estimated_utility > average_score:
            average_score = estimated_utility
            move = actions[count]
    return move[idx]

def findroles(game):
    if 'roles' not in game:
        game['roles'] = [rule[1] for rule in game['rules'] if rule[0] == 'role']
    return game['roles']

def findinits(game):
    ret_lst = []
    for rule in game['rules']:
        if rule[0] == 'init':
            if isinstance(rule[1], str):
                ret_lst.append(rule[1])
            else:
                ret_lst.append(rule[1][0] + '(' + ",".join(rule[1][1:]) + ')')
    return tuple(sorted(ret_lst))

def findmoves(state, game):
    """
    state is a tuple of bases
    game is a global dictionary
    output is a list of tuples of the Cartesian product of all players' legal moves
    which double as the edges of the game tree
    """
    if state not in game['tree']:
        game['tree'][state] = {}
    if findterminalp(state, game):
        return None
    if 'actions' not in game['tree'][state]:
        game['tree'][state]['actions'] = {}
        roles = findroles(game)
        ret_lst = [set() for dummy in roles]
        prolog = game['prolog_rules']
        for prop in state:
            prolog += 'true(' + prop + '). '
        prolog += 'main :- findall([R,M], legal(R,M), L), write(L), halt.'
        proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        legals = str2list(proc.communicate(input = prolog)[0])
        for legal in legals:
            idx = legal.index(',')
            ret_lst[roles.index(legal[:idx])].add(legal[idx + 1:])
        ret_lst = [sorted(list(move_set)) for move_set in ret_lst]
        edges = tuple(itertools.product(*ret_lst))
        for edge in edges:
            game['tree'][state]['actions'][edge] = {}
    return sorted(game['tree'][state]['actions'].keys())

def findlegals(role, state, game):
    """
    This filters out other player moves to only include those of the given role
    """
    if findterminalp(state, game):
        return None
    ret_set = set()
    idx = findroles(game).index(role)
    for move in findmoves(state, game):
        ret_set.add(move[idx])
    return sorted(ret_set)

def findnext(moves, state, game):
    """
    moves is a tuple like ('move(4,1,3,1)', 'noop')
    state is a tuple of bases
    game is a global dictionary
    """
    if state not in game['tree']:
        game['tree'][state] = {}
    if 'actions' not in game['tree'][state]:
        findmoves(state, game)
    # bug here that causes crashes
    if 'next' not in game['tree'][state]['actions'][moves]:
        roles = findroles(game)
        prolog = game['prolog_rules']
        for idx in range(len(moves)):
            if moves[idx] != 'noop':
                prolog += 'does(' + roles[idx] + ',' + moves[idx] + '). '
        for prop in state:
            prolog += 'true(' + prop + '). '
        prolog += 'main :- findall([B], next(B), L), write(L), halt. '
        proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        game['tree'][state]['actions'][moves]['next'] = str2list(proc.communicate(input = prolog)[0])
    return game['tree'][state]['actions'][moves]['next']

def findreward(role, state, game):
    """
    Returns an integer, with 100 indicating victory and 0 maybe defeat or nothing
    """
    if state not in game['tree']:
        game['tree'][state] = {}
    if 'values' not in game['tree'][state]:
        roles = findroles(game)
        prolog = game['prolog_rules']
        for prop in state:
            prolog += 'true(' + prop + '). '
        prolog += 'main :- findall([Role, N], goal(Role, N), L), write(L), halt. '
        proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        rewards = str2list(proc.communicate(input = prolog)[0])
        ret_lst = [0 for dummy in roles]
        for reward in rewards:
            idx = reward.index(',')
            ret_lst[roles.index(reward[:idx])] = int(reward[idx + 1:])
        game['tree'][state]['values'] = tuple(ret_lst)
    return game['tree'][state]['values'][findroles(game).index(role)]

def findterminalp(state, game):
    """
    Boolean, true if terminal
    """
    if state not in game['tree']:
        game['tree'][state] = {}
    if 'terminal' not in game['tree'][state]:
        prolog = game['prolog_rules']
        for prop in state:
            prolog += 'true(' + prop + '). '
        prolog += "end :- terminal, write('True'). "
        prolog += "end :- \+terminal, write('False'). "
        prolog += 'main :- end, halt. '
        proc = subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        game['tree'][state]['terminal'] = (proc.communicate(input = prolog)[0] == 'True')            
    return game['tree'][state]['terminal'] 
      
##################################################################################
# Helper functions for GGP protocol handlers

def str2list(ret_str):
    if ret_str.find('[') == -1:
        return ret_str
    nexts = ret_str[1:-1].split(']')
    nexts = [(base[2:] if base[0:2] == ',[' else base[1:]) for base in nexts if len(base) > 0]
    return tuple(sorted(set(nexts)))

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

def game2dot(game_dict, filename):
    """
    Creates a graphviz dot file (http://www.graphviz.org/content/dot-language)
    which can be converted into an svg file to view in a browser by calling
    dot -Tsvg -ofilename.svg filename
    dot files have a .gv suffix by convention
    """
    graph_list = []
    terminal_list = []
    for node in sorted(game_dict.keys()):
        if not game_dict[node]['terminal']:
            for edge in game_dict[node]['actions']:
                if len(node) > 1:
                    from_node = str(node).replace(', ', ' ').replace("'", '') 
                else:
                    from_node = node[0]
                if 'values' in game_dict[node]:
                    from_node += '\\n' + str(game_dict[node]['values'])
                if len(game_dict[node]['actions'][edge]['next']) > 1:
                    to_node = str(game_dict[node]['actions'][edge]['next']).replace(', ', ' ').replace("'", '') 
                else:
                    to_node = game_dict[node]['actions'][edge]['next'][0]
                if 'values' in game_dict[game_dict[node]['actions'][edge]['next']]:
                    to_node += '\\n' + str(game_dict[game_dict[node]['actions'][edge]['next']]['values'])
                if len(edge) > 1:
                    edge_label = str(edge).replace(', ', ' ').replace("'", '')
                else:
                    edge_label = edge[0]
                if 'score_count' in game_dict[node]['actions'][edge]:
                    score_count = []
                    for idx in range(len(game_dict[node]['actions'][edge]['score_count']) - 1):
                        score_count.append(int(float(game_dict[node]['actions'][edge]['score_count'][idx]) \
                                          / float(game_dict[node]['actions'][edge]['score_count'][-1])))
                    edge_label += '\\n' + str(score_count)
                graph_list.append('"' + from_node + '" -> "' + to_node + '" [label = "' + edge_label + '"];')
        else:
            if len(node) > 1:
                from_node = str(node).replace(', ', ' ').replace("'", '')
            else:
                from_node = node[0]
            from_node += '\\n' + str(game_dict[node]['values'])
            terminal_list.append('"' + from_node + '"')
    dot_file = open(filename, "w")
    print("digraph game_tree {", file = dot_file)
    print("node [shape = doublecircle]; " + " ".join(terminal_list) + ";", file = dot_file)
    print("node [shape = circle];", file = dot_file)
    for element in graph_list:
        print(element, file = dot_file)
    print("}", file = dot_file)
        

##########################################################

# GGP protocol handlers as described in http://logic.stanford.edu/ggp/chapters/chapter_04.html
# More up to date http://games.stanford.edu/index.php/communication-protocol

def info():
    return "((name " + PLAYER_NAME + ")(status available))"
    
def start(game_id, player, rules, startclock, playclock):
    # print(rules)
    global game
    timeout = time.time() + TIME_MARGIN * float(startclock)
    game = {}
    game['tree'] = {}
    game['rules'] = rules
    game['prolog_rules'] = prolog_rules(rules)
    game['playclock'] = playclock
    game['game_id'] = game_id
    game['player'] = player
    game['state'] = findinits(game)
    bestmove(game['player'], game['state'], game, timeout)
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
    print ("Return move " + return_move)
    return return_move
    
def stop(game_id, move):
    global game
    move = rewrite_move(move)
    # print("Move: ", move)
    game['state'] = findnext(move, game['state'], game)
    # print("State: ", game['state'])
    # os.remove(PROLOG_FILE_NAME)
    if DOT_FILE_NAME != False:
        game2dot(game['tree'], DOT_FILE_NAME)
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
    arg_parser.add_argument("-g", "--graphviz", help="generate a dot file for graphviz", type=str)
    args = arg_parser.parse_args()
    if args.port:
        PORT = args.port
    if args.hostname:
        HOST_NAME = args.hostname
    if args.graphviz:
        DOT_FILE_NAME = args.graphviz
    server = BaseHTTPServer.HTTPServer((HOST_NAME, PORT), myHTTPRequestHandler)
    print("Started gameplayer on " + str(PORT))
    server.serve_forever()
 
except KeyboardInterrupt:
    print("^C received, shutting down the web server")
    server.server_close()


