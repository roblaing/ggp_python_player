#!/usr/bin/env python

import BaseHTTPServer, time, random, argparse, itertools

# constants and globals
HOST_NAME = "127.0.0.1"
PORT = 9147
PLAYER_NAME = "roblaing"
game = {}

# Algorithms to select move

def depthcharge(node, timeout):
    if findterminalp(node, game):
        return findreward(role, node, game)
    if timeout < int(time.time() * 1000):
        return 0
    player = findplayer(role, node)
    move = findlegalx(player, node, game)
    next_state = findnext(player, move, node, game)
    return depthcharge(next_state, timeout)

def montecarlo(node, time_per_action):
    wins = 0
    total = 0
    timeout = int(time.time() * 1000) + time_per_action
    while timeout > int(time.time() * 1000):
        total += 1
        wins += depthcharge(node, timeout)
    return (wins, total)

def bestmove(role, state, game, timeout):
    actions = findlegals(role, state, game)
    move = findlegalx(role, state, game)
    score = 0.0
    # Remember working in milliseconds
    time_per_action = int(float((int(playclock) - 1) * 1000)/float(len(actions)))
    for action in actions:
        (wins, total) = montecarlo(findnext(role, action, state, game), time_per_action)
        if total > 0:
            result = float(wins)/float(total)
        else:
            result = 0.0
        # print action, result
        if result > score:
            move = action
            score = result
    return move

#########################################################################
# gdl functions
# Functions http://logic.stanford.edu/ggp/chapters/chapter_04.html
# findroles(game) - returns a sequence of roles.
# 
# findpropositions(game) - returns a sequence of propositions.
# 
# findactions(role,game) - returns a sequence of actions for a specified role.
#
# findinits(game) - returns a sequence of all propositions that are true in the initial state.
#
# findlegalx(role,state,game) - returns the first action that is legal for the specified role in the specified state.
#
# findlegals(role,state,game) - returns a sequence of all actions that are legal for the specified role in the specified state.
#
# findnext(roles,move,state,game) - returns a sequence of all propositions that are true in the 
# state that results from the specified roles performing the specified move in the specified state.
#
# findreward(role,state,game) - returns the goal value for the specified role in the specified state.
# 
# findterminalp(state,game) - returns a boolean indicating whether the specified state is terminal.
# 
# Additionally 
# findplayer(role, state) - returns the controlling player in the given state.
###############################################################################
    
def findroles(game):
    "Returns a list of roles"
    return game['roles']
   
def findpropositions(game):
    "Return the game's set of base propositions"
    return game['propositions']

def findinits(game): 
    "Returns a sequence of all propositions that are true in the initial state."
    return game['inits']

def findactions(player, game):
    "Returns a set of actions for a specified role."
    return_set = set([])
    moves = game['legals'].keys()
    for move in moves:
        if move[0] == player:
            return_set.add(move[1])
    return return_set
    
def findlegals(player, current_state, game):
    "Returns a list of all actions that are legal for the specified role in the specified state."
    return_list = set([])
    moves = game['legals'].keys()
    for move in moves:
        if isinstance(game['legals'][move][0], set):
            # cases like (legal robot a) for always legal moves
            if len(game['legals'][move][0]) == 0 and len(game['legals'][move][1]) == 0:
                if move[0] == player:
                    return_list.add(move[1])
            elif (len(game['legals'][move][0]) > 0 and game['legals'][move][0].issubset(current_state)) or \
                (len(game['legals'][move][1]) > 0 and current_state.isdisjoint(game['legals'][move][1])):
                if move[0] == player:
                    return_list.add(move[1])
            else:
                pass
        else: # list of possibilities
            for true_nots in game['legals'][move]:
                if (len(true_nots[0]) > 0 and true_nots[0].issubset(current_state)) or \
                    (len(true_nots[1]) > 0 and current_state.isdisjoint(true_nots[1])):
                    if move[0] == player:
                        return_list.add(move[1])
    return list(return_list)


def findlegalx(player, state, game):
    "Returns a random action that is legal for the specified role in the specified state."
    return random.choice(findlegals(player, state, game))

def findnext(roles, move, current_state, game):
    """
    Returns a set of all propositions that are true in the state that results from the 
    specified roles performing the specified move in the specified state.
    """
    next_state = set([])
    current_state_clone = set(current_state)
    if isinstance(roles, str):
        current_state_clone.add((roles, tuplerize(move)))
    else:
        for idx in range(len(roles)):
            current_state_clone.add((roles[idx], tuplerize(move[idx])))
    # print current_state_clone    
    for next in game["nexts"]:
        if isinstance(game["nexts"][next][0], set):
            if game["nexts"][next][0].issubset(current_state_clone) and \
                current_state_clone.isdisjoint(game["nexts"][next][1]):
                next_state.add(next)
        else:
            for true_nots in game["nexts"][next]:
                if true_nots[0].issubset(current_state_clone) and \
                    current_state_clone.isdisjoint(true_nots[1]):
                    next_state.add(next)
    # print next_state
    return next_state

def findreward(player, next_state, game):
    """
    Returns the goal value for the specified role in the specified state.
    Sometimes these seem to be contradictory as in http://ggp.stanford.edu/applications/060401.php
    where there are rules
    ['<=', ['goal', 'black', '50'], ['not', ['line', 'x']], ['not', ['line', 'o']]], 
    ['<=', ['goal', 'black', '50'], ['line', 'x'], ['line', 'o']],
    so we need a minmax system
    """
    if player == role:
        score = 100
    else: # player != role
        score = 0
    for goal in game['goals']:
        # need to handle cases like (set([("cell", "1", "1", "1"), ...]), set([]))
        # ie only contain one rule
        if isinstance(game['goals'][goal][0], set):
            # print game['goals'][goal]
            if (len(game['goals'][goal][0]) > 0 and game['goals'][goal][0].issubset(next_state) or \
                (len(game['goals'][goal][1]) > 0 and next_state.isdisjoint(game['goals'][goal][1]))) and \
                goal[0] == player:
                value = int(goal[1])
                if player == role:
                    score = min(score, value)
                else:
                    score = max(score, value)
        # else contains list of true_not tuples
        else:
            for true_not in game['goals'][goal]:
                if ((len(true_not[0]) > 0 and true_not[0].issubset(next_state)) or \
                    (len(true_not[1]) > 0 and next_state.isdisjoint(true_not[1]))) and \
                    goal[0] == player:
                    value = int(goal[1])
                    if player == role:
                        score = min(score, value)
                    else:
                        score = max(score, value)
    return score

def findterminalp(next_state, game):
    "Returns True if the specified state is terminal."
    if isinstance(game['terminals'][0], set):
        # print game['terminals']
        if (len(game['terminals'][0]) > 0 and game['terminals'][0].issubset(next_state) or \
            len(game['terminals'][1]) > 0 and next_state.isdisjoint(game['terminals'][1])):
            return True
    else:
        for true_not in game['terminals']:
            if (len(true_not[0]) > 0 and true_not[0].issubset(next_state) or \
                len(true_not[1]) > 0 and next_state.isdisjoint(true_not[1])):
                return True
    return False
    
def findplayer(role, state):
    for proposition in list(state):
        if proposition[0] == "control":
            return proposition[1]
    return role

##########################################################################
# Game Description Language interpreter
##########################################################################

def substitute(term, var_name, var_value):
    new_term = []
    for idx in range(len(term)):
        if isinstance(term[idx], list):
            new_term.append(substitute(term[idx], var_name, var_value))
        elif isinstance(term[idx], tuple):
            new_term.append(substitute(list(term[idx]), var_name, var_value))
        elif isinstance(term[idx], str) and term[idx] == var_name:
            new_term.append(var_value)
        else:
            new_term.append(term[idx])
    return new_term
  
def flatten(nested_lists):
    flattened_list = list(itertools.chain.from_iterable(nested_lists))
    if isinstance(flattened_list[0], str):
        return nested_lists
    return flattened_list
  
def collect_tuples(true_not_list):
    new_list = []
    for true_not in true_not_list:
        if isinstance(true_not, tuple):
            new_list.append(true_not)
        elif len(true_not) == 1 and isinstance(true_not[0], tuple):
            new_list.extend((true_not))
        elif isinstance(true_not, list):
            new_list.extend(collect_tuples(true_not))
        else:
            print("collect_tuples can't handle " + str(true_not_list))
    if len(new_list) == 1:
        return new_list[0]
    else:
        return tuple(new_list)
  
def contains(word, list_or_tuple):
    """
    Return True if a word appears in a list of lists or tuple of tuples
    """
    if word == list_or_tuple:
        return True
    valid = False
    for idx in range(len(list_or_tuple)):
        if isinstance(list_or_tuple[idx], str):
            if list_or_tuple[idx] == word:
                return True
        else:
            valid = contains(word, list_or_tuple[idx])
            if valid:
                return True
    return valid
 
def tuplerize(rule):
    """
    Lists can't be stored as keys in python dictionaries
    This helper function leaves strings alone while recursively
    Changing lists to tuples
    """
    if isinstance(rule, str):
        return rule
    else:
        new_list = []
        for term in rule:
            if isinstance(rule, str):
                new_list.append(term)
            else: # list
                new_list.append(tuplerize(term))
        return tuple(new_list)

def add_constants(term, statement_dictionary, constants):
    """
    Only used for 'base' or 'input' which have different patterns
    so need the idx rule
    """
    # print constants
    if term in constants:
        for values in constants[term]:
            const_name = values[0]
            if isinstance(values, str):
                pass
            else:
                if len(values) > 2:
                    const_value = tuple(values[1:])
                else:
                    const_value = values[1]
                if const_name in constants:
                    constants[const_name].append(const_value)
                else:
                    constants[const_name] = [const_value]
    if term == 'base':
        idx = 1
    else:
        idx = 2
    for keys in statement_dictionary.keys():
        if contains(term, keys):
            constant_name = keys[idx][0]
            if isinstance(keys[idx], str):
                constant_name = keys[idx - 1]
                constant_value = keys[idx]
            elif len(keys[idx]) == 2:
                constant_value = tuplerize(keys[idx][1])
            elif len(keys[idx]) > 2:
                constant_value = tuple(keys[idx][1:])
            else:
                constant_value = keys[idx][1]
            if constant_name in constants:
                constants[constant_name].append(constant_value)
            else:
                constants[constant_name] = [constant_value]
    return constants
 
def get_variables(rule, variables_dict, local_variables_dict):
    """
    Create local_variables_dict
    """
    # need to handle cases like (<= terminal (line x)) which needs to figure out  (<= (line ?x) (row ?m ?x))
    for idx in range(len(rule)):
        if all([isinstance(atom, str) for atom in rule[idx]]) and all([atom.istitle() for atom in rule[idx][1:]]):
            if rule[idx][0] in variables_dict:
                if len(rule[idx]) == 2:
                    local_variables_dict[rule[idx][1]] = variables_dict[rule[idx][0]]
                else: # something like (successor 1 2)
                    var_lists = variables_dict[rule[idx][0]]
                    new_list = []
                    for jdx in range(len(rule[idx][1:])):
                        new_list.append([])
                        for kdx in range(len(var_lists)):
                            new_list[jdx].append(var_lists[kdx][jdx])
                    for jdx in range(len(rule[idx][1:])):
                        local_variables_dict[rule[idx][jdx + 1]] = sorted(list(set(new_list[jdx])))
        elif all([isinstance(atom, str) for atom in rule[idx]]) and any([atom.istitle() for atom in rule[idx][1:]]):
            # print rule[idx]
            if rule[idx][0] in variables_dict:
                for jdx in range(len(rule[idx][1:])):
                    if rule[idx][jdx + 1].istitle():
                        var_name = rule[idx][jdx + 1]
                        if var_name not in local_variables_dict:
                            local_variables_dict[var_name] = []
                        for var_val in variables_dict[rule[idx][0]]:
                            local_variables_dict[var_name].append(var_val[jdx])
                        local_variables_dict[var_name] = sorted(list(set(local_variables_dict[var_name])))
        else:
            for jdx in range(len(rule[idx])):
                if isinstance(rule[idx][jdx], list) or isinstance(rule[idx][jdx], tuple):
                    get_variables([rule[idx][jdx]], variables_dict, local_variables_dict)
                if isinstance(rule[idx][jdx], str) and rule[idx][jdx].istitle():
                    if isinstance(rule[idx][jdx - 1], str):
                        if rule[idx][jdx - 1] in ['legal', 'does']:
                            if rule[idx][jdx] not in local_variables_dict:
                                local_variables_dict[rule[idx][jdx]] = variables_dict['role']
                        if rule[idx][jdx - 1] in variables_dict:
                            if rule[idx][jdx] not in local_variables_dict:
                                local_variables_dict[rule[idx][jdx]] = variables_dict['role']    
    return local_variables_dict

def ground(rule):
    """
    True if there are no variables in statement, else False
    """
    no_variables = True
    for atom in rule:
        if isinstance(atom, str) and atom.istitle():
            return False
        if isinstance(atom, list):
            no_variables = ground(atom)
    return no_variables

def verify_constants(rule, constants):
    """
    Boolean to filter out generated things like ['successor, '4, '4']
    which aren't in constants dictionary
    """
    for idx in range(len(rule)):
        if all([isinstance(atom, str) for atom in rule[idx]]):
            if rule[idx][0] in constants and len(rule[idx]) > 2:
                if tuple(rule[idx][1:]) not in constants[rule[idx][0]]:
                    return False
        elif isinstance(rule[idx], list) or isinstance(rule[idx], tuple):
            verify = verify_constants(rule[idx], constants)
            if verify == False:
                return False
        else:
            pass
    return True

def substitute_expression(term, statement_dictionary):
    # tuple(set(tuplerize(statement_dictionary[term])))
    if isinstance(term, str) and term in statement_dictionary:
        return substitute_expression(tuple(set(tuplerize(statement_dictionary[tuplerize(term)]))), statement_dictionary)
    elif isinstance(term[0], str) and tuplerize(term) in statement_dictionary:
        return substitute_expression(tuple(set(tuplerize(statement_dictionary[tuplerize(term)]))), statement_dictionary)
    elif isinstance(term[0], list) or isinstance(term[0], tuple):
        if isinstance(term, tuple):
            term = list(term)
        for idx in range(len(term)):
            term[idx] = substitute_expression(term[idx], statement_dictionary)
        return term
    else:
        return term
 
def update_constants(term, constants):
    if isinstance(term, str):
        return constants
    var_name = term[0]
    # 'input' needs to be handled separately since it has an extra paramater
    # this successfully creates 'mark': [('2', '1'), ('2', '3'), ('3', '1')],
    # from ['<=', ['input', 'R', ['mark', '2', '1']], ['role', 'R']],...
    if term[0] == 'input' and (isinstance(term[2], tuple) or isinstance(term[2], list)):
        constants = update_constants(term[2], constants)
    if var_name in ('legal', 'next', 'goal'):
        return constants
    if len(term) == 2:
        var_val = tuplerize(term[1])
    elif len(term) > 2:
        var_val = tuplerize(term[1:])
    else:
        print("Single term " + str(term) + " can't be added to constants dictionary")
    #print var_val
    if var_name in constants:
        var_set = set(constants[var_name])
        var_set.add(var_val)
        constants[var_name] = sorted(list(var_set))
    else:
        constants[var_name] = [var_val]
    if isinstance(term[1], tuple) or isinstance(term[1], list):
       constants = update_constants(term[1], constants)
    return constants
 
def filter_constants(rule, constants):
    return_list = []
    for term in rule:
        if isinstance(term[0], str):
            if term[0] in constants:
                if len(term) == 2:
                    body = term[1]
                else:
                    body = tuplerize(term[1:])
                if body in constants[term[0]]:
                    return_list.append(term)
            else:
                return_list.append(term)
        else:
            return_list.append(filter_constants(term, constants))
    return return_list

def get_constants(rules):
    """
    Expand the constants dictionary to include values that need to
    be expanded from the provided rules
    """
    # Step 1: Read rules like ['row', '1']
    constants = {}
    rules_clone = rules[:]
    not_grounded = []
    for dummy_idx in range(len(rules_clone)):
        rule = rules_clone.pop(0)
        if rule[0] != '<=':
            if len(rule[1:]) > 1:
                var_val = tuple(rule[1:])
            else:
                if isinstance(rule[1], list):
                    var_val = tuple(rule[1])
                else:
                    var_val = rule[1]
            if rule[0] in constants:
                constants[rule[0]].append(var_val)
            else:
                constants[rule[0]] = [var_val]
        else:
            not_grounded.append(rule)
    # Step 2: expand rules like ['<=', ['base', ['step', 'N']], ['succ', 'M', 'N']]
    # and hoist these values into the constants dictionary
    count = 0
    max_iterations = 3
    while len(not_grounded) > 0 and max_iterations > count:
        rules_clone = not_grounded[:]
        not_grounded = []
        filter_list = []
        for dummy_idx in range(len(rules_clone)):
            rule = rules_clone.pop(0)
            if rule[0] == "<=":
                variables = get_variables(rule[1:], constants, {})
                if len(variables) == 0 and not ground(rule):
                    not_grounded.append(rule)
                if len(variables) > 0:
                    all_variables_have_values = True
                    for variable in variables.keys():
                       if len(variables[variable]) == 0 or not ground(variables[variable]):
                            all_variables_have_values = False
                            not_grounded.append(rule)
                            break
                    if all_variables_have_values:
                        expanded_relations = [rule[1:]]
                        for var_name in variables.keys():
                            temp_list = []
                            for var_value in variables[var_name]:
                                for relation in expanded_relations:
                                    temp_list.append(substitute(relation, var_name, var_value))
                            expanded_relations = temp_list[:]
                        for relation in expanded_relations:
                            if not ground(relation):
                                not_grounded.append(rule)
                            if verify_constants(relation, constants) and ground(relation):
                                filter_list.append(relation)
                    else:
                        print("Missing constants: ", rule[1:])
        for relation in filter_list:
            constants = update_constants(relation[0], constants)
        count += 1
    if len(not_grounded) > 0:
        print("Warning, these constants were not matched: ", str(not_grounded))
    return constants

def expand_rules(rules, constants):
    expressions = {}
    rules_clone = rules[:]
    not_grounded = []
    for dummy_idx in range(len(rules_clone)):
        rule = rules_clone.pop(0)
        if rule[0] == "<=" and not contains("base", rule):
            not_grounded.append(rule)
    rules_clone = not_grounded[:]
    not_grounded = []
    filter_list = []
    for dummy_idx in range(len(rules_clone)):
        rule = rules_clone.pop(0)
        if isinstance(rule[1], str):
            head = rule[1]
        else:
            head = rule[1]
        if len(rule) == 3:
            body = rule[2]
        else:
            body = rule[2:]
        if ground(rule): # no variables need substituting, as above example
            if tuplerize(head) in expressions:
                expressions[tuplerize(head)].append(list(tuplerize(body)))
            else:
                expressions[tuplerize(head)] = [list(tuplerize(body))]
        else:
            variables = get_variables(rule[1:], constants, {})
            all_variables_have_values = True
            for variable in variables.keys():
                if len(variables[variable]) == 0 or not ground(variables[variable]):
                    all_variables_have_values = False
                    not_grounded.append(rule)
                    break
            if all_variables_have_values:
                expanded_relations = [[head] + [body]]
                for var_name in variables.keys():
                    temp_list = []
                    for var_value in variables[var_name]:
                        for relation in expanded_relations:
                            temp_list.append(substitute(relation, var_name, var_value))
                    expanded_relations = temp_list[:]
                for relation in expanded_relations:
                    if not ground(relation):
                        not_grounded.append(rule)
                    if verify_constants(relation, constants)and ground(relation):
                        filter_list.append(relation)
            else:
                print("Missing variables: ", head, body)
    for expression in filter_list:
        if tuplerize(expression[0]) in expressions:
            expressions[tuplerize(expression[0])].append(list(tuplerize(expression[1])))
        else:
            expressions[tuplerize(expression[0])] = [list(tuplerize(expression[1]))]
    # add missed expressions
    if len(not_grounded) > 0:
        print("Warning, these expressions were not matched: ", str(not_grounded))
    return expressions

def logic_tuple(expressions, propositions, constants, statement_dictionary):
    # need to catch things like ['true', '7']
    if isinstance(expressions[0], str):
        expressions = [tuple(expressions)]
    true_set = set([])
    not_set = set([])
    for expression in expressions:
        # ('true', 'q')
        if expression[0] == "true" and expression[1] in propositions:
            true_set.add(expression[1])
        # ('not', ('true', 'p'))
        elif expression[0] == "not" and expression[1][0] == "true" and expression[1][1] in propositions:
            not_set.add(expression[1][1])
        # ('does', 'robot', 'a')
        elif expression[0] == "does":
            true_set.add((expression[1], tuplerize(expression[2])))
        elif expression[0] == "distinct":
            if expression[1] == expression[2]:
                true_set.add("Skip")
        elif expression[0] == "or":
            or_list = []
            for exp in expression[1:]:
                if exp[0] == 'distinct':
                    or_list.append(exp[1] == exp[2])
                else:
                    print("Oops: only now how to 'or' distinct. No rule for " + str(expression))
            if all(or_list):
                true_set.add("Skip")
        # ('successor', '1', '2')
        elif tuplerize(expression[0]) in constants:
            if len(expression) > 2:
                values = tuplerize(expression[1:])
            else:
                values = expression[1]
            if values not in constants[tuplerize(expression[0])]:
                true_set.add("Skip")
        else:
            print("Problem expressions " + str(expressions))
            print("Oops, no rule for " + str(expression))
    return (true_set, not_set)
  
def translate_expressions(expressions, propositions, constants, statement_dictionary):
    # print "Expressions " + str(expressions)
    or_list = []
    for expression in expressions:
        # ['line', 'x']
        if tuplerize(expression) in statement_dictionary:
            expanded_expressions = flatten(substitute_expression(tuplerize(expression), statement_dictionary))
            if isinstance(expanded_expressions[0], tuple):
                (true_set, not_set) =  logic_tuple(expanded_expressions, propositions, constants, statement_dictionary)
                if "Skip" not in true_set:
                    or_list.append((true_set, not_set))
            else:
                rule_list = []
                for expanded_expression in expanded_expressions:
                    (true_set, not_set) = logic_tuple(expanded_expression, propositions, constants, statement_dictionary)
                    if "Skip" not in true_set:
                        rule_list.append((true_set, not_set))
                or_list.append(rule_list)
        # ['not', 'open']
        elif isinstance(expression[0], str) and expression[0] == "not" and \
            tuplerize(expression[1]) in statement_dictionary:
            expanded_expressions = flatten(substitute_expression(tuplerize(expression[1]), statement_dictionary))
            if isinstance(expanded_expressions[0], tuple):
                (true_set, not_set) =  logic_tuple(expanded_expressions, propositions, constants, statement_dictionary)
                if "Skip" not in true_set:
                    or_list.append((not_set, true_set))
            else:
                for expanded_expression in expanded_expressions:
                    (true_set, not_set) = logic_tuple(expanded_expression, propositions, constants, statement_dictionary)
                    if "Skip" not in true_set:
                        or_list.append((not_set, true_set))
        # [('not', ('line', 'x')), ('not', ('line', 'o')), ('not', 'open')] or
        # [('line', 'x'), ('not', ('line', 'o'))]
        elif (isinstance(expression[0], tuple) and expression[0][0] == "not" and \
            tuplerize(expression[0][1]) in statement_dictionary) or \
            (isinstance(expression[0], tuple) and expression[0] in statement_dictionary) :
            for subexpression in expression:
                if subexpression[0] == "not":
                    expanded_expressions = flatten(substitute_expression(tuplerize(subexpression[1]), statement_dictionary))
                    if isinstance(expanded_expressions[0], tuple):
                        (true_set, not_set) =  logic_tuple(expanded_expressions, propositions, constants, statement_dictionary)
                        if "Skip" not in true_set:
                            or_list.append((not_set, true_set))
                    else:
                        for expanded_expression in expanded_expressions:
                            (true_set, not_set) = logic_tuple(expanded_expression, propositions, constants, statement_dictionary)
                            if "Skip" not in true_set:
                                or_list.append((not_set, true_set))
                else:
                    expanded_expressions = flatten(substitute_expression(tuplerize(subexpression), statement_dictionary))
                    if isinstance(expanded_expressions[0], tuple):
                        (true_set, not_set) =  logic_tuple(expanded_expressions, propositions, constants, statement_dictionary)
                        if "Skip" not in true_set:
                            or_list.append((true_set, not_set))
                    else:
                        for expanded_expression in expanded_expressions:
                            (true_set, not_set) = logic_tuple(expanded_expression, propositions, constants, statement_dictionary)
                            if "Skip" not in true_set:
                                or_list.append((true_set, not_set))
        else:
            (true_set, not_set) =  logic_tuple(expression, propositions, constants, statement_dictionary)
            if "Skip" not in true_set:
                or_list.append((true_set, not_set))
    return or_list
    
def add_rules(term, constants, statement_dictionary):
    return_dict = {}
    if term in constants:
        for expression in constants[term]:
            return_dict[expression] = [(set([]), set([]))]    
    for key in statement_dictionary.keys():
        if contains(term, key):
            expressions = statement_dictionary[key]
            or_list = translate_expressions(expressions, constants["base"], constants, statement_dictionary)
            if len(key) == 2:
                new_key = key[1]
            else:
                new_key = tuple(list(key[1:]))
            return_dict[new_key] = or_list
    for entry in return_dict:
        return_dict[entry] = collect_tuples(return_dict[entry])
    return return_dict

    
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
    "Variables are title case, everything else lower case"
    if token[0] == '?':
        return token[1:].title()
    else:
        return token.lower()

#################################################################################

class myHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        global http #, origin
        http = self
        # origin = self.headers['Origin']
        length = int(self.headers['Content-length'])
        http_handler(self.rfile.read(length))

# listener
def http_handler(text):
    result = parse(text)
    if result[0].lower() == 'info':
        response("((name " + PLAYER_NAME + ")(status available))")
    if result[0].lower() == 'start':
        global gameid, game, role, playclock, constants, statement_dictionary
        # print result[3]
        #f = open("rules.py", "w")
        #f.write(str(result[3]))
        gameid = result[1]
        role = result[2]
        startclock = result[4]
        playclock = result[5]
        timeout = int(time.time() * 1000) + (int(startclock) - 1) * 1000
        # moving what was done in interpret_rules to hear
        # so as to handle games where interpretation can only be partially completed here        
        constants = get_constants(result[3])
        statement_dictionary = expand_rules(result[3], constants)
        game["inits"] = set(constants['init'])
        game["roles"] = constants['role']
        game["propositions"] = set(constants['base'])
        game["actions"] = constants['input']
        if timeout > int(time.time() * 1000):
            game["nexts"] = add_rules("next", constants, statement_dictionary)
        else:
            response('ready')
        if timeout > int(time.time() * 1000):
            game["legals"] = add_rules("legal", constants, statement_dictionary)
        else:
            response('ready')
        if timeout > int(time.time() * 1000):
            game["goals"] = add_rules("goal", constants, statement_dictionary)
        else:
            response('ready')
        if timeout > int(time.time() * 1000):
            game["terminals"] = []
            for key in statement_dictionary.keys():
                if key == 'terminal':
                    expressions = statement_dictionary[key]
                    or_list = translate_expressions(expressions, constants["base"], constants, statement_dictionary)
                    game["terminals"].append(or_list)
            game["terminals"] = collect_tuples(game["terminals"])
        else:
            response('ready')
        if timeout > int(time.time() * 1000):
            # start probing for opening move
            print "Wasting " + str(timeout - int(time.time() * 1000)) + \
            " milliseconds that should be used to prepare first move"
        response('ready')
        # f = open("game.py", "w")
        # f.write(str(game))
        # print game
        #print 'roles: ', findroles(game)
        # print 'propositions: ', findpropositions(game)
        # print 'actions: ', role, findactions(role,game)
        #print 'inits: ', findinits(game)
    if result[0] == 'play':
        global state
        timeout = int(time.time() * 1000) + (int(playclock) - 1) * 1000
        # if reading the rules was not completed during the startclock, need to continue here
        if ("nexts" not in game) and (timeout > int(time.time() * 1000)):
            game["nexts"] = add_rules("next", constants, statement_dictionary)
        if ("legals" not in game) and (timeout > int(time.time() * 1000)):
            game["legals"] = add_rules("legal", constants, statement_dictionary)
        if ("goals" not in game) and (timeout > int(time.time() * 1000)):
            game["goals"] = add_rules("goal", constants, statement_dictionary)
        if ("terminals" not in game) and (timeout > int(time.time() * 1000)):
            game["terminals"] = []
            for key in statement_dictionary.keys():
                if key == 'terminal':
                    expressions = statement_dictionary[key]
                    or_list = translate_expressions(expressions, constants["base"], constants, statement_dictionary)
                    game["terminals"].append(or_list)
            game["terminals"] = collect_tuples(game["terminals"])
        # Hopefully the above is usually just passed over and play starts here
        move = result[2]
        if move != 'nil':
            state = findnext(findroles(game), move, state, game)
        else:
            state = findinits(game)
        legals = findlegals(role, state, game)
        if legals[0] == "noop":
             print "Should be thinking ahead"
             response("noop")
        else:
            action = bestmove(role, state, game, playclock)
            response(action)
    if result[0] == 'stop':
        response('done')
        game = {}
        # print 'goals: ', game['goals']
    if result[0] == 'abort':
        response('done')
        game = {}
        
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

