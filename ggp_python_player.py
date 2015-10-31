# -*- coding: utf-8 -*-
"""
This is an implementation of the Game Description Language
with its subroutines described in
http://logic.stanford.edu/ggp/chapters/chapter_04.html
It is open source software written by a hobby programer, Robert Laing
https://github.com/roblaing/ggp_python_player
"""

import BaseHTTPServer, time, random, argparse, re, ast

HOST_NAME = "127.0.0.1"
PORT = 9147
PLAYER_NAME = "roblaing"

def depthcharge(state, game, timeout):
    if findterminalp(state, game) or time.time() > timeout:
        if 'values' not in game['game_tree'][state]:
           findreward(findroles(game)[0], state, game) 
        return game['game_tree'][state]['values']
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
            game['game_tree'][state]['actions'][move]['score_count'][idx] += values[idx]
        game['game_tree'][state]['actions'][move]['score_count'][idx + 1] += 1
    return game['game_tree'][state]['actions'][move]['score_count']

def bestmove(role, state, game, timeout):
    move = tuple([findlegalx(player, state, game) for player in findroles(game)])
    actions = findmoves(state, game)
    idx = findroles(game).index(role)
    average_score = 0.0
    time_per_move = (timeout - time.time())/float(len(actions))
    for count in range(len(actions)):
        if 'score_count' not in game['game_tree'][state]['actions'][actions[count]]:
            game['game_tree'][state]['actions'][actions[count]]['score_count'] = [0 for dummy in findroles(game)] + [1]
        timelimit = timeout - time_per_move*(len(actions) - count - 1)
        scores = montecarlo(actions[count], state, game, timelimit)
        estimated_utility = float(scores[idx])/float(scores[-1]), actions[count]
        if estimated_utility > average_score:
            average_score = estimated_utility
            move = actions[count] 
    return move[idx]

########################################################################

def findroles(game):
    """
    Return a list of roles in the same order as in the original rules list
    """
    return [role[1] for role in game['relation_constants']['role']]

def findpropositions(game):
    """
    Returns a tuple of all propositions
    """
    ret_set = set()
    for base in prune(generate('base', [], game), [], game):
        if base[0] == 'base':
            ret_set.add(list2tuple(base[1]))
        if base[0] == '<=' and base[1][0] == 'base':
            ret_set.add(list2tuple(base[1][1]))
    return tuple(sorted(ret_set))

def findactions(role, game):
    """
    Returns a sequence of actions for a specified role.
    """
    ret_set = set()
    for action in prune(generate('input', [], game), [], game):
        if action[0] == 'input' and action[1] == role:
            ret_set.add(list2tuple(action[2]))
        if action[0] == '<=' and action[1][0] == 'input' and action[1][1] == role:
            ret_set.add(list2tuple(action[1][2]))
    return tuple(sorted(ret_set))

def findinits(game):
    """
    Returns the start state.
    States are a tuple of propositions without "true" prefix
    which are used as node names in the game tree
    """
    ret_set = set()
    for init in generate_prune('init', [], game):
        if init[0] == 'init':
            ret_set.add(list2tuple(init[1]))
        if init[0] == '<=' and init[1][0] == 'init':
            ret_set.add(list2tuple(init[1][1]))
    state = tuple(sorted(ret_set))
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    return state

def findmoves(state, game):
    """
    A modification of findlegals that returns the "edges" with a move for each role
    even if it's just 'noop' to make traversing the game tree easier
    """
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    if findterminalp(state, game):
        return 'noop'
    if 'findmoves_completed' not in game['game_tree'][state]:
        game['game_tree'][state]['findmoves_completed'] = False
    if game['game_tree'][state]['findmoves_completed']:
        return sorted(game['game_tree'][state]['actions'].keys())
    if 'actions' not in game['game_tree'][state]:
        game['game_tree'][state]['actions'] = {}
        trues = [['true', list(base) if isinstance(base, tuple) else base] for base in state]
        roles = findroles(game)
        actions = ['noop' for role in roles]
        legals = generate_prune('legal', trues, game)
        for legal in legals:
            # print legal
            if legal[0] != '<=':
                actions[roles.index(legal[1])] = list2tuple(legal[2])
            else:
                actions[roles.index(legal[1][1])] = list2tuple(legal[1][2])
            if actions != ['noop' for role in roles]:
                game['game_tree'][state]['actions'][tuple(actions)] = {}
        game['game_tree'][state]['findmoves_completed'] = True
    # print sorted(game['game_tree'][state]['actions'].keys())
    return sorted(game['game_tree'][state]['actions'].keys())

def findlegals(role, state, game):
    """
    Legals are either a string or tuple describing an action for a given role.
    A move is a tuple of actions in the roles order used as edge names in the game tree
    """
    idx = findroles(game).index(role)
    return list2tuple(sorted(set([action[idx] for action in findmoves(state, game)])))

def findlegalx(role, state, game):
    """
    Returns the first action that is legal for the specified role in the specified state.
    """
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    if findterminalp(state, game):
        return 'noop'
    if 'findmoves_completed' in game['game_tree'][state] and \
      game['game_tree'][state]['findmoves_completed'] == True:
        return sorted(game['game_tree'][state]['actions'].keys())[0][findroles(game).index(role)]
    else:
        legals = game['relation_constants']['legal']
        # put grounded terms at start of list to speed things up
        temp_lst = []
        for legal in legals:
            if ground(legal):
                temp_lst = [legal] + temp_lst
            else:
                temp_lst.append(legal)
        legals = list(temp_lst)
        trues = [['true', list(base) if isinstance(base, tuple) else base] for base in state]
        for legal in legals:
            expanded_rules = expand_rule(legal, game)
            if expanded_rules[0] == 'legal' and expanded_rules[1] == role:
                return list2tuple(expanded_rules[2])
            if len(expanded_rules) > 0 and isinstance(expanded_rules[0], list):
                for expanded_rule in expanded_rules:
                    pruned_rules = prune(generate(expanded_rule, trues, game), trues, game)
                    if len(pruned_rules) > 0 and isinstance(pruned_rules[0], str):
                        pruned_rules = [pruned_rules]
                    for pruned_rule in pruned_rules:
                        if pruned_rule[1][1] == role:
                            return list2tuple(pruned_rule[1][2])

def findnext(move, state, game):
    """
    Left out the 'roles' parameter since it seems easier to just use 'move' as sent to player()
    Return the state (ie node) the given move by the give role (ie edge) leads to
    Modified to take move as handed from player() ie as ['a'] or ['noop', ['mark', '1', '2']]
    """
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    if 'actions' not in game['game_tree'][state]:
        game['game_tree'][state]['actions'] = {}
    if not isinstance(move, tuple):
        move = list2tuple(move)
    if move not in game['game_tree'][state]['actions']:
        game['game_tree'][state]['actions'][move] = {}
    if 'next' not in game['game_tree'][state]['actions'][move]:
        trues = [['true', list(base) if isinstance(base, tuple) else base] for base in state]
        roles = findroles(game)
        for idx in range(len(roles)):
            if move[idx] != 'noop':
                if isinstance(move[idx], tuple):
                    trues.append(['does', roles[idx], list(move[idx])])
                else:
                    trues.append(['does', roles[idx], move[idx]])
        ret_set = set()
        for next_gdl in generate_prune('next', trues, game):
            if next_gdl[0] == 'next':
                ret_set.add(list2tuple(next_gdl[1]))
            if next_gdl[0] == '<=' and next_gdl[1][0] == 'next':
                ret_set.add(list2tuple(next_gdl[1][1]))
        next_state = tuple(sorted(ret_set))
        game['game_tree'][state]['actions'][move]['next'] = next_state
    return game['game_tree'][state]['actions'][move]['next']

def findreward(role, state, game):
    """
    Returns the goal value for the specified role in the specified state.
    """
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    if 'values' not in game['game_tree'][state]:
        trues = [['true', list(base) if isinstance(base, tuple) else base] for base in state]
        roles = findroles(game)
        values = [set() for dummy in roles]
        goals = generate_prune('goal', trues, game)
        # print goals
        for idx in range(len(roles)):
            for goal in goals:
                if goal[0] == '<=' and goal[1][1] == roles[idx]:
                    values[idx].add(int(goal[1][2]))
                    # break
                if goal[1] == roles[idx]:
                    values[idx].add(int(goal[2]))
                    # break
        # hack to workaround bug in generate_prune('goal', trues, game)
        if not all([len(value) == 1 for value in values]):
            print("Problem with findreward for ", values, state)
            tmp_lst = [0 for dummy in values]
            for idx in range(len(values)):
                if max([int(num) for num in values[idx]]) == 100:
                    tmp_lst[idx] = 100
                else:
                    tmp_lst[idx] = min([int(num) for num in values[idx]]) 
            values = list(tmp_lst)
        else:
            tmp_lst = []
            for value in values:
                tmp_lst.append(int(list(value)[0]))
            values = list(tmp_lst)
            # print values
        game['game_tree'][state]['values'] = tuple(values)
    return game['game_tree'][state]['values'][findroles(game).index(role)]

def findterminalp(state, game):
    """
    Returns a boolean indicating whether the specified state is terminal.
    """
    if 'game_tree' not in game:
        game['game_tree'] = {}
    if state not in game['game_tree']:
        game['game_tree'][state] = {}
    if 'terminal' not in game['game_tree'][state]:
        trues = [['true', list(base) if isinstance(base, tuple) else base] for base in state]
        terminals = generate_prune('terminal', trues, game)
        game['game_tree'][state]['terminal'] = (len(terminals) > 0)
        for terminal in terminals:
            if str(terminal).find("['not',") != -1 and ground(terminal):
                game['game_tree'][state]['terminal'] = False
                break
    return game['game_tree'][state]['terminal']

# Helper functions

def ground(term):
    """
    True if there are no variables in statement, else False
    """
    return re.search('[A-Z]', str(term)) == None

def substitute(term, var_name, var_value):
    """
    Quick 'n dirty way to substitute variables no matter how
    nested the list, tuple or whatever is
    """
    return ast.literal_eval(str(term).replace(var_name, var_value))

def list2tuple(nested_list):
    """
    Convert a list, no matter how deeply nested, into an equivalently
    deeply nested tuple. Also handle Python's rule that a single element list
    ['a'] converts to ('a',)
    """
    if isinstance(nested_list, str):
        return nested_list
    elif len(nested_list) == 1 and isinstance(nested_list[0], list):
        return (tuple(nested_list[0]),)
    elif len(nested_list) == 1:
        return tuple(nested_list)
    else:
        return ast.literal_eval(str(nested_list).replace('[', '(').replace(']', ')'))

def create_game_dictionary(rules):
    """
    rule can be one of
     - fact eg ['successor', '1', '2']
     - ['<=', head, body_rule...]
    head can be
    - constant eg terminal
    - reference rule eg ['<=', ['input', 'R', ['mark', '2', '1']], ['role', 'R']]
    """
    game = {}
    game['relation_constants'] = {}
    for rule in rules:
        if rule[0] != '<=': # rule is a fact
            relation_constant = rule[0]
        else: # head body clause
            if isinstance(rule[1], str): # head is a constant
                relation_constant = rule[1]
            else: # head is a relation function
                relation_constant = rule[1][0]
        if relation_constant not in game['relation_constants']:
            game['relation_constants'][relation_constant] = [rule]
        else:
            game['relation_constants'][relation_constant].append(rule)
    return game


def expand_body_rule(body_rule, game):
    """
    body_rule can be something like ['line', 'x'] which points to rules like
    ['<=', ['line', 'X'], ['row', 'M', 'X']],
    ['<=', ['line', 'X'], ['column', 'M', 'X']],
    ['<=', ['line', 'X'], ['diagonal', 'X']] which point to rules....
    """
    def unpack(nested_list):
        "Hack to work around problem of things like ['not', [['true', ['cell', 'M', 'N', 'b']]]]"
        while len(nested_list) == 1 and isinstance(nested_list[0], list):
            nested_list = nested_list[0]
        return nested_list

    def dictionary_substitution(head):
        "Replace ['line', 'X'] with ['row', 'M', 'X']] etc"
        ret_lst = []
        if isinstance(head, str):
            for clause in game['relation_constants'][head]:
                if clause[0] == '<=':
                    ret_lst.append(unpack(clause[2:]))
        else:
            for clause in game['relation_constants'][head[0]]:
                if clause[0] == '<=':
                    new_clause = clause[2:]
                    for idx in range(len(head)):
                        if clause[1][idx] != head[idx]:
                            new_clause = substitute(new_clause, clause[1][idx], head[idx])
                    ret_lst.append(unpack(new_clause))
        return unpack(ret_lst)

    def recursive_helper(body_rule):
        """
        body rule can be
         - a string like open
         - a list starting with a relation_constant like ['line', 'x']
         - a list of lists like [['row', 'M', 'X'], ['column', 'M', 'X'], ['diagonal', 'X']]
        """
        if isinstance(body_rule, str):
            if body_rule in game['relation_constants']:
                new_body_rule = dictionary_substitution(body_rule)
                if len(new_body_rule) > 0:
                    return recursive_helper(new_body_rule)
                else:
                    return body_rule
            else:
                return body_rule
        if isinstance(body_rule[0], str):
            if body_rule[0] in game['relation_constants']:
                new_body_rule = dictionary_substitution(body_rule)
                if len(new_body_rule) > 0:
                    return recursive_helper(new_body_rule)
                else:
                    return body_rule
            else:
                return body_rule
        if all([isinstance(element, list) for element in body_rule]):
            # need to avoid creating a tree of nested lists
            # so need to check if expanded_body_rule returns
            # a list of lists
            ret_lst = []
            for element in body_rule:
                new_element = recursive_helper(element)
                if len(new_element) > 1 and \
                  all([isinstance(exp_body_rule, list) for exp_body_rule in new_element]) and \
                  isinstance(new_element[0][0], list):
                    ret_lst.extend(new_element)
                else:
                    ret_lst.append(new_element)
            return ret_lst
        return body_rule

    if body_rule[0] == 'not':
        return ['not'] + [recursive_helper(body_rule[1])]
    else:
        return recursive_helper(body_rule)

def expand_rule(rule, game):
    """
    If rule isn't a fact, send each body rule to expand_body_rule(body_rule, game)
    and return the cartesian product of the
    original head and expanded body rules
    """
    if rule[0] != '<=':
        return rule
    ret_lst = [rule[0:2]]
    for body_rule in rule[2:]:
        expanded_body_rules = expand_body_rule(body_rule, game)
        if isinstance(expanded_body_rules[0], str):
            tmp_lst = []
            for element in ret_lst:
                tmp_lst.append(element + [expanded_body_rules])
            ret_lst = tmp_lst[:]
        else:
            tmp_lst = []
            for expanded_body_rule in expanded_body_rules:
                for element in ret_lst:
                    if isinstance(expanded_body_rule[0], str):
                        tmp_lst.append(element + [expanded_body_rule])
                    else:
                        tmp_lst.append(element + expanded_body_rule)
            ret_lst = tmp_lst[:]
    return ret_lst

def generate(expanded_rule, trues, game):

    def build_var_dict(body_rule, var_dict):
        if all([isinstance(element, list) for element in body_rule]):
            for sub_body_rule in body_rule:
                var_dict = build_var_dict(sub_body_rule, var_dict)
            return var_dict
        if body_rule[0] == 'not':
            return build_var_dict(body_rule[1], var_dict)
        if body_rule[0] == 'true':
            for prop in trues:
                if prop[0] == 'true':
                    if isinstance(prop[1], list) and isinstance(body_rule[1], list) and \
                      len(prop[1]) == len(body_rule[1]):
                        match = True
                        tmp_var_dict = {}
                        for idx in range(len(body_rule[1])):
                            if prop[1][idx] != body_rule[1][idx] and \
                              not body_rule[1][idx].istitle():
                                match = False
                                break
                            if body_rule[1][idx].istitle():
                                if body_rule[1][idx] not in tmp_var_dict:
                                    tmp_var_dict[body_rule[1][idx]] = set([prop[1][idx]])
                                else:
                                    tmp_var_dict[body_rule[1][idx]].add(prop[1][idx])
                        if match:
                            for var_name in tmp_var_dict:
                                if var_name not in var_dict:
                                    var_dict[var_name] = tmp_var_dict[var_name]
                                else:
                                    var_dict[var_name] = \
                                      var_dict[var_name].union(tmp_var_dict[var_name])
        if body_rule[0] == 'does':
            for prop in trues:
                if prop[0] == 'does':
                    if isinstance(prop[2], list) and isinstance(body_rule[2], list) and \
                      len(prop[2]) == len(body_rule[2]):
                        match = True
                        tmp_var_dict = {}
                        for idx in range(len(body_rule[2])):
                            if prop[2][idx] != body_rule[2][idx] and \
                              not body_rule[2][idx].istitle():
                                match = False
                                break
                            if body_rule[2][idx].istitle():
                                if body_rule[2][idx] not in tmp_var_dict:
                                    tmp_var_dict[body_rule[2][idx]] = set([prop[2][idx]])
                                else:
                                    tmp_var_dict[body_rule[2][idx]].add([prop[2][idx]])
                        if match:
                            if body_rule[1].istitle():
                                if body_rule[1] not in tmp_var_dict:
                                    tmp_var_dict[body_rule[1]] = set([prop[1]])
                                else:
                                    tmp_var_dict[body_rule[1]].add([prop[1]])
                            for var_name in tmp_var_dict:
                                if var_name not in var_dict:
                                    var_dict[var_name] = tmp_var_dict[var_name]
                                else:
                                    var_dict[var_name] = \
                                      var_dict[var_name].union(tmp_var_dict[var_name])
        if body_rule[0] in game['relation_constants']:
            for fact in game['relation_constants'][body_rule[0]]:
                if len(body_rule) == len(fact) and body_rule[0] == fact[0]:
                    match = True
                    tmp_var_dict = {}
                    for idx in range(len(body_rule)):
                        if fact[idx] != body_rule[idx] and not body_rule[idx].istitle():
                            match = False
                            break
                        if body_rule[idx].istitle():
                            if body_rule[idx] not in tmp_var_dict:
                                tmp_var_dict[body_rule[idx]] = set([fact[idx]])
                            else:
                                tmp_var_dict[body_rule[idx]].add(fact[idx])
                    if match:
                        for var_name in tmp_var_dict:
                            if var_name not in var_dict:
                                var_dict[var_name] = tmp_var_dict[var_name]
                            else:
                                var_dict[var_name] = \
                                  var_dict[var_name].union(tmp_var_dict[var_name])
        return var_dict

    def expand_literal(literal, var_dict):
        list1 = [literal]
        for var_name in var_dict:
            list2 = []
            for exp_rule in list1:
                exp_rule_copy = list(exp_rule)
                for var_val in var_dir[var_name]:
                    list2.append(substitute(exp_rule_copy, var_name, var_val))
            list1 = list(list2)
        return list1

    if ground(expanded_rule):
        return expanded_rule
    ret_lst = []
    var_dir = {}
    for body_rule in expanded_rule[2:]:
        var_dir = build_var_dict(body_rule, var_dir)
        exp_rules = expand_literal(expanded_rule, var_dir)
        if isinstance(exp_rules[0], str):
            ret_lst.append(exp_rules)
        else:
            ret_lst.extend(exp_rules)
    return ret_lst

def prune(generated_list, trues, game):

    def body_rule_true(body_rule):
        if all([isinstance(element, list) for element in body_rule]) and\
          all([isinstance(element, list) for element in body_rule[0]]):
            return body_rule_true(['or'] + body_rule)
        elif all([isinstance(element, list) for element in body_rule]) and\
          isinstance(body_rule[0][0], str):
            # if all([body_rule_true(sub_body_rule) for sub_body_rule in body_rule]):
            #    print body_rule
            return all([body_rule_true(sub_body_rule) for sub_body_rule in body_rule])
        elif body_rule[0] in ('true', 'does'):
            return body_rule in trues
        # elif body_rule[0] == 'not' and all([isinstance(element, list) for element in body_rule[1]]):
        #    return any([body_rule_true(element) for element in body_rule[1]])
        elif body_rule[0] == 'not':
            # print body_rule, not body_rule_true(body_rule[1])
            return not body_rule_true(body_rule[1])
        elif body_rule[0] == 'distinct':
            return body_rule[1] != body_rule[2]
        elif body_rule[0] == 'or':
            return any([body_rule_true(element) for element in body_rule[1:]])
        elif isinstance(body_rule[0], str) and body_rule[0] in game['relation_constants']:
            return body_rule in game['relation_constants'][body_rule[0]]
        else:
            print("Prune can't handle ", str(body_rule))
            return True

    ret_lst = []
    if isinstance(generated_list[0], str):
        generated_list = [generated_list]
    for rule in generated_list:
        if ground(rule) and rule[0] != '<=':
            ret_lst.append(rule)
        else:
            match = True
            for body_rule in rule[2:]:
                if not body_rule_true(body_rule):
                    match = False
                    break
            if match:
                ret_lst.append(rule)
    return ret_lst


def generate_prune(relation_constant, trues, game):
    ret_list = []
    for rule in game['relation_constants'][relation_constant]:
        expanded_rules = expand_rule(rule, game)
        if isinstance(expanded_rules[0], str):
            expanded_rules = [expanded_rules]
        for expanded_rule in expanded_rules:
            # pruned_rule = not_filter(prune(generate(expanded_rule, trues, game), trues, game), trues, game)
            pruned_rule = prune(generate(expanded_rule, trues, game), trues, game)
            if len(pruned_rule) > 0 and isinstance(pruned_rule[0], str):
                ret_list += [pruned_rule]
            else:
                ret_list += pruned_rule
    return ret_list




##########################################################

# GGP protocol handlers as described in http://logic.stanford.edu/ggp/chapters/chapter_04.html
# More up to date http://games.stanford.edu/index.php/communication-protocol

def info():
    return "((name " + PLAYER_NAME + ")(status available))"
    
def start(game_id, player, rules, startclock, playclock):
    # print rules
    global game
    timeout = time.time() + float(startclock) - 1.0
    game = create_game_dictionary(rules)
    game['playclock'] = playclock
    game['game_id'] = game_id
    game['player'] = player
    game['state'] = findinits(game)
    bestmove(game['player'], game['state'], game, timeout)
    return 'ready'

def play(game_id, move):
    global game
    # print "Move: ", move
    timeout = time.time() + float(game['playclock']) - 1
    if move != 'nil':
        game['state'] = findnext(list2tuple(move), game['state'], game)
    return_move = bestmove(game['player'], game['state'], game, timeout)
    return str(return_move).replace(', ', ' ').replace("'", '')

    
def stop(game_id, move):
    global game
    game['state'] = findnext(list2tuple(move), game['state'], game)
    # game2dot(game['game_tree'], "game.gv")
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
    result = parse(text)
    if result[0].lower() == 'info':
        response(info())
    elif result[0].lower() == 'start':
        response(start(result[1], result[2], result[3], result[4], result[5]))
    elif result[0] == 'play':
        response(play(result[1], result[2]))
    elif result[0] == 'stop':
        response(stop(result[1], result[2]))
    elif result[0] == 'abort':
        response('done')
    else:
        print("Not sure how to respond to " + str(result))

class myHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        global http #, origin   # origin commented out because of bug in ggp-base
        http = self
        # origin = self.headers['Origin']
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




