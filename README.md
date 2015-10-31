<h1>A Python script for Coursera's General Game Playing course</h1>

<p>This is an unfortunately still fairly rough and buggy attempt to write a Python player for Coursera's <a href="https://www.coursera.org/course/ggp">General Game Playing</a> course offered by Stanford University's Professor Michael Genesereth.</p>

<p>At this stage it needs python2.7 or higher (for argparse) but doesn't work with python3 (yet) because of its dependency on BaseHTTPServer.<p>

<p>The default hostname is 127.0.0.1 and port is 9147 which can be changed by calling, say, <code>python2.7 ggp_python_player.py -n=171.64.71.18 -p=9148</code>.</p>

<p>I'm only an intermediate python programmer, so suggestions from advanced programmers on how to improve this code will be gladly accepted.</p>

<h2>Game Description Language (GDL)</h2>

<p>A key job of this script is to interpret <a href="http://logic.stanford.edu/classes/cs227/2013/readings/gdl_spec.pdf"> Game Description Language (GDL)</a> scripts sent to it via http by the general game playing server. A fine manual is available <a href="http://logic.stanford.edu/ggp/chapters/cover.html">online</a>.</p>

<p>Using a partially completed game of Tic Tac Toe used in <a href="http://ggp.stanford.edu/applications/060401.php">Exercise 6.4.1</a> as an example, the diagram (produced by graphiz from the python dictionary structure I use to store the game in) illustrates how the Montecarlo method explores the game tree and comes up a "best move" from a given state.</p> 

<object data="tictactoe1.svg" type="image/svg+xml" width="1000">
  <p>Oops, no svg</p>
</object>



