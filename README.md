<h1>A Python script for Coursera's General Game Playing course</h1>

<p>This is my attempt to write a Python player for Coursera's <a href="https://www.coursera.org/course/ggp">General Game Playing</a> course offered by Stanford University's Professor Michael Genesereth.</p>

<p>It requires Prolog &mdash; <a href="http://www.dcc.fc.up.pt/~vsc/Yap/">yap</a>, <a href="http://www.swi-prolog.org/">swipl</a> or any other <a href="http://www.gprolog.org/">Prolog</a> should work provided it can be called from the command line as a script.</p>

<p>After many hours of trying to write my own interpreter and looking at the various Prolog interfaces available for Python, I opted for the kludge of having my Python script generate a Prolog script which is then executed via <a href="https://docs.python.org/2/library/subprocess.html"><code>subprocess.Popen(PROLOG, stdin = subprocess.PIPE, stdout = subprocess.PIPE)</code></a>, where the constant PROLOG is defined near the top of the file as:</p>

<p><code>PROLOG = ['swipl','-s', '/dev/stdin']</code></p>

<p>If you prefer yap, you can change that to:<br>
<code>PROLOG = ['yap','-L', '/dev/stdin']</code></p>

<p>Presumably other prologs would work the same with whatever flags they need to read a script (which is read from /dev/stdin for the above two prologs since they don't respect Unix's '-' convention).</p>

<p>At this stage, my script needs python2.7 or higher (for argparse) but doesn't work with python3 (yet) because of its dependency on BaseHTTPServer.<p>

<p>The default hostname is 127.0.0.1 and port is 9147 which can be changed by calling, say, <code>python2.7 ggp_python_player.py -n 171.64.71.18 -p 9148</code>.</p>

<p>There are two versions, a "no cache" version which I did to work around the problem that my hosting service quickly switches off the instance of the player because it uses too much memory, and a "with cache version" which creates a stronger player and also has the option of writing the game tree created as python dictionary out as a graphviz graphic.</p>

<p>Adding <code>-g <i>filename</i></code> will generate a <a href ="http://www.graphviz.org/content/dot-language">graphviz dot</a> file which can the be used to generate a graphic of the game tree like the example below.</p>

<p>I'm only an intermediate Python and novice Prolog programmer, so suggestions from advanced programmers on how to improve this code will be gladly accepted.</p>

<p>A third version which stores the game tree as a postgres database is work in progress.</p>

<h2>Game Description Language (GDL)</h2>

<p>A key job of this script is to interpret <a href="http://logic.stanford.edu/classes/cs227/2013/readings/gdl_spec.pdf"> Game Description Language (GDL)</a> scripts sent to it via http by the general game playing server. A fine manual is available <a href="http://logic.stanford.edu/ggp/chapters/cover.html">online</a>.</p>

<p>Using a partially completed game of Tic Tac Toe used in <a href="http://ggp.stanford.edu/applications/060401.php">Exercise 6.4.1</a> as an example, the diagram (produced by graphiz from the python dictionary structure I use to store the game in) illustrates how the Montecarlo method explores the game tree and comes up a "best move" from a given state.</p> 

<object data="tictactoe1.svg" type="image/svg+xml" width="1000">
  <p><img src="tictactoe1.png" /></p>
</object>


<h2>Glossary</h2>
<dl>
<dt><a href="https://en.wikipedia.org/wiki/Game_tree">Game Tree</a></dt>
<dd>A directed graph whose nodes are positions in a game and whose edges are moves.</dd>
<dt><a href="https://en.wikipedia.org/wiki/Percept_%28artificial_intelligence%29">Percept</a></dt>
<dd>A percept is detected and acted upon by an actuator.</dd>
<dt><a href="https://en.wikipedia.org/wiki/Ply_%28game_theory%29">Ply</a></dt>
<dd>One ply corresponds to one level of the game tree. </dd>
</dl>


