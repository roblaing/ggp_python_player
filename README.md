<h1>A Python script for Coursera's General Game Playing course</h1>

<p>This is an early attempt to write a Python player for Coursera's <a href="https://class.coursera.org/ggp-003">General Game Playing</a> course offered by Stanford University's Professor Michael Genesereth.</p>

<p>At this stage, the script handles small games and puzzles like <a href="http://ggp.stanford.edu/applications/050201.php">3-Puzzle</a>, <a href="http://ggp.stanford.edu/applications/050202.php">Buttons and Lights</a> and <a href="http://ggp.stanford.edu/applications/060401.php">Tic Tac Toe</a>.</p>

<p>It unfortunately fails to load larger puzzles like Hunter and games like Alquerque within the time limit, and its ability to interpret different GDL scripts is fairly flakey.</p>

<p>I've tried to keep the libraries "plain vanilla", but it does require python2.7 for argparse which enables you to change the default hostname from 127.0.0.1 and port from 9147 by calling it as, say, <code>python2.7 ggp_python_player.py -n=171.64.71.18 -p=9148</code>.</p>

<p>My line of attack has been to rewrite the <a href=http://games.stanford.edu/games/gdl.html>Game Description Language</a> rules sent to the script as tuples of python sets: the first set is "true" propositions which must be a subset of the current state for the given legal move, next state, goal or terminal to be true. The second tuple are the "not" propositions which must be disjoint from the current state for the given legal move, next state, goal or terminal to be true. A list of these tuples then provides the various "ors" for a legal move or whatever to hold.</p>

<p>As I said above, this works for small games and puzzles, but seems to be too slow for larger games. It's my first ever attempt at writing an interpreter (which I suspect more experienced coders will spot immediately), but I intend hacking away at this to hopefully have a Python alternative for studends of this course by its next itteration.</p>

