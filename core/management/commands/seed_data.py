"""
Management command: seed_data
Populates the database with authentic PCEP-30-02 exam content.

Content inventory
-----------------
  4  domains  — official weights 18 / 29 / 25 / 28 %
  25 topics   — mapped to PCEP objective codes
  14 lessons  — rich-text study material (3–4 per domain)
  50 flashcards — active-recall pairs covering every topic
  80 questions  — MC, code-output, true/false, fill-in-the-blank
  16 coding challenges — including all 12 required challenge types

Usage
-----
  python manage.py seed_data           # load / refresh all content
  python manage.py seed_data --flush   # wipe everything first, then seed
"""

from django.core.management.base import BaseCommand

from labs.models import CodingChallenge
from learning.models import Domain, Flashcard, Lesson, Topic
from quizzes.models import AnswerChoice, Question


class Command(BaseCommand):
    help = "Seed PCEP Prep Coach with authentic PCEP-30-02 exam content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing content before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing content…")
            CodingChallenge.objects.all().delete()
            Flashcard.objects.all().delete()
            Lesson.objects.all().delete()
            Topic.objects.all().delete()
            Domain.objects.all().delete()
            Question.objects.all().delete()

        steps = [
            ("Domains",             self._seed_domains),
            ("Topics",              self._seed_topics),
            ("Lessons",             self._seed_lessons),
            ("Flashcards",          self._seed_flashcards),
            ("Quiz questions",      self._seed_questions),
            ("Coding challenges",   self._seed_challenges),
        ]
        for label, fn in steps:
            self.stdout.write(f"  Seeding {label}…")
            fn()

        self.stdout.write(self.style.SUCCESS("✅  Seed data loaded successfully."))
        self._print_summary()

    # ── Summary ────────────────────────────────────────────────────────
    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write("Content counts:")
        self.stdout.write(f"  Domains    {Domain.objects.count()}")
        self.stdout.write(f"  Topics     {Topic.objects.count()}")
        self.stdout.write(f"  Lessons    {Lesson.objects.count()}")
        self.stdout.write(f"  Flashcards {Flashcard.objects.count()}")
        self.stdout.write(f"  Questions  {Question.objects.count()}")
        self.stdout.write(f"  Challenges {CodingChallenge.objects.count()}")

    # ══════════════════════════════════════════════════════════════════
    # DOMAINS
    # ══════════════════════════════════════════════════════════════════
    def _seed_domains(self):
        for d in [
            {
                "slug": "fundamentals", "order": 1, "weight_percent": 18,
                "title": "Computer Programming and Python Fundamentals",
                "description": (
                    "How computers run programs, Python basics, data types, "
                    "variables, operators, type casting, and I/O."
                ),
                "icon": "bi-cpu",
            },
            {
                "slug": "control-flow", "order": 2, "weight_percent": 29,
                "title": "Control Flow: Conditional Blocks and Loops",
                "description": (
                    "Decision-making with if/elif/else, iteration with while "
                    "and for, and flow control with break, continue, and pass."
                ),
                "icon": "bi-arrow-repeat",
            },
            {
                "slug": "data-collections", "order": 3, "weight_percent": 25,
                "title": "Data Collections: Tuples, Dictionaries, Lists, and Strings",
                "description": (
                    "Python's built-in data structures: lists, tuples, "
                    "dictionaries, and strings with their methods."
                ),
                "icon": "bi-collection",
            },
            {
                "slug": "functions-exceptions", "order": 4, "weight_percent": 28,
                "title": "Functions and Exceptions",
                "description": (
                    "Defining functions, parameter passing, scope, recursion, "
                    "and handling errors with try/except."
                ),
                "icon": "bi-gear",
            },
        ]:
            Domain.objects.update_or_create(slug=d["slug"], defaults=d)

    # ══════════════════════════════════════════════════════════════════
    # TOPICS  (25 total across 4 domains)
    # ══════════════════════════════════════════════════════════════════
    def _seed_topics(self):
        spec = {
            "fundamentals": [
                ("Interpreter vs Compiler",                 "interpreter-vs-compiler",          "easy",   "1.1.1"),
                ("Lexis, Syntax, and Semantics",            "lexis-syntax-semantics",           "easy",   "1.1.2"),
                ("Keywords, Indentation, Comments",         "keywords-indentation-comments",    "easy",   "1.1.3"),
                ("Literals and Variables",                  "literals-variables",               "easy",   "1.2.1"),
                ("Naming Conventions and PEP 8",            "naming-conventions-pep8",          "easy",   "1.2.2"),
                ("Numeric and String Operators",            "numeric-string-operators",         "medium", "1.3.1"),
                ("Boolean, Relational, and Bitwise Ops",   "boolean-relational-bitwise",       "medium", "1.3.2"),
                ("Type Casting",                            "type-casting",                     "easy",   "1.4.1"),
                ("print() and input()",                     "print-input",                      "easy",   "1.4.2"),
            ],
            "control-flow": [
                ("if / if-else / if-elif-else",             "conditionals",                     "easy",   "2.1.1"),
                ("while Loops",                             "while-loops",                      "medium", "2.2.1"),
                ("for Loops and range()",                   "for-loops-range",                  "medium", "2.2.2"),
                ("break, continue, pass",                   "break-continue-pass",              "medium", "2.2.3"),
                ("Nested Loops and Logic",                  "nested-loops",                     "hard",   "2.3.1"),
            ],
            "data-collections": [
                ("Lists and List Methods",                  "lists-methods",                    "medium", "3.1.1"),
                ("List Slicing and Comprehensions",         "list-slicing-comprehensions",      "medium", "3.1.2"),
                ("Nested Lists",                            "nested-lists",                     "hard",   "3.1.3"),
                ("Tuples and Immutability",                 "tuples-immutability",              "easy",   "3.2.1"),
                ("Dictionaries",                            "dictionaries",                     "medium", "3.3.1"),
                ("Strings, Escaping, and String Methods",   "strings-methods",                  "medium", "3.4.1"),
            ],
            "functions-exceptions": [
                ("Defining Functions and return",           "functions-return",                 "medium", "4.1.1"),
                ("Parameters, Arguments, Defaults",         "parameters-arguments",             "medium", "4.1.2"),
                ("Scope, Shadowing, and global",            "scope-global",                     "hard",   "4.2.1"),
                ("Recursion",                               "recursion",                        "hard",   "4.2.2"),
                ("Exceptions and try/except",               "exceptions-try-except",            "medium", "4.3.1"),
            ],
        }
        for domain_slug, rows in spec.items():
            domain = Domain.objects.get(slug=domain_slug)
            for i, (name, slug, diff, obj_code) in enumerate(rows):
                Topic.objects.update_or_create(
                    domain=domain, slug=slug,
                    defaults={
                        "name": name, "order": i + 1,
                        "difficulty": diff, "pcep_objective": obj_code,
                        "description": f"Learn about {name.lower()} in Python.",
                    },
                )

    # ══════════════════════════════════════════════════════════════════
    # LESSONS  (14 total; at least 3 per domain)
    # ══════════════════════════════════════════════════════════════════
    def _seed_lessons(self):
        # (topic_slug, domain_slug, title, html_content)
        lessons = [
            # ── Domain 1 ──────────────────────────────────────────────
            ("interpreter-vs-compiler", "fundamentals",
             "How Python Runs Your Code",
             """<h3>Interpreter vs Compiler</h3>
<p>A <strong>compiler</strong> translates the entire source file into machine
code before execution (C, C++). An <strong>interpreter</strong> reads and
executes code <em>line by line</em>.</p>
<p>Python uses <strong>CPython</strong>, which first compiles source to
<em>bytecode</em> (<code>.pyc</code> files), then interprets that bytecode
on the Python Virtual Machine (PVM).</p>
<table class="table table-bordered table-sm">
<thead><tr><th></th><th>Compiler</th><th>Interpreter</th></tr></thead>
<tbody>
<tr><td>Translation</td><td>Whole program at once</td><td>Line by line</td></tr>
<tr><td>Error reporting</td><td>After full compilation</td><td>At the failing line</td></tr>
<tr><td>Speed</td><td>Faster to run</td><td>Slower (no pre-compilation)</td></tr>
</tbody>
</table>
<pre><code>print("Line 1 runs")
print(1 / 0)        # Error here — line 1 already executed
print("Never reached")</code></pre>"""),

            ("lexis-syntax-semantics", "fundamentals",
             "Lexis, Syntax, and Semantics",
             """<h3>The Three Layers of a Language</h3>
<p><strong>Lexis</strong> — the vocabulary: valid tokens such as keywords
(<code>if</code>, <code>for</code>, <code>def</code>), operators
(<code>+</code>, <code>=</code>), and identifiers.</p>
<p><strong>Syntax</strong> — the grammar: rules for combining tokens.
<code>if x &gt; 0:</code> is valid; <code>if &gt; x 0:</code> is not.</p>
<p><strong>Semantics</strong> — the meaning: what syntactically valid code
actually does at runtime.</p>
<pre><code># Syntax error — grammar broken
print("Hello"         # missing closing paren

# Semantic error — valid syntax but wrong meaning
age = "25" + 1        # TypeError at runtime
</code></pre>
<p class="alert alert-info">PCEP tip: a <em>SyntaxError</em> is detected
before the program runs; a semantic error crashes or produces wrong output
at runtime.</p>"""),

            ("keywords-indentation-comments", "fundamentals",
             "Keywords, Indentation, and Comments",
             """<h3>Python Keywords</h3>
<p>Reserved words: <code>False True None and as assert break class continue
def del elif else except finally for from global if import in is lambda
nonlocal not or pass raise return try while with yield</code>.</p>
<p>You cannot use these as variable names.</p>
<h3>Indentation</h3>
<p>Python uses indentation (4 spaces recommended) instead of braces to
define code blocks.</p>
<pre><code>if True:
    print("inside block")   # 4-space indent
print("outside block")      # back to column 0</code></pre>
<h3>Comments</h3>
<pre><code># Single-line comment
x = 42  # inline comment
# There are no block comment tokens in Python:
# use consecutive # lines, or a triple-quoted string as a docstring.
</code></pre>"""),

            ("literals-variables", "fundamentals",
             "Literals and Variables",
             """<h3>Literals</h3>
<p>Hard-coded values in source code:</p>
<pre><code>42        # int
3.14      # float
"hello"   # str
True      # bool
None      # NoneType
0o17      # octal  → 15
0xFF      # hex    → 255
0b1010    # binary → 10</code></pre>
<h3>Variables</h3>
<p>Named references to values. Created by assignment; no type declaration
needed (dynamic typing).</p>
<pre><code>name = "Alice"
age  = 25
pi   = 3.14159

# Multiple assignment
x = y = z = 0

# Swap (Pythonic)
a, b = 1, 2
a, b = b, a   # a=2, b=1</code></pre>
<p>Naming rules: start with a letter or underscore, then letters, digits,
or underscores. Case-sensitive. Cannot be a keyword.</p>"""),

            # ── Domain 2 ──────────────────────────────────────────────
            ("conditionals", "control-flow",
             "Conditional Statements in Python",
             """<h3>if / if-else / if-elif-else</h3>
<pre><code>x = 10

if x > 0:
    print("positive")

if x % 2 == 0:
    print("even")
else:
    print("odd")

score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"
print(grade)   # B</code></pre>
<ul>
<li>Only the first matching branch runs.</li>
<li><code>else</code> is optional.</li>
<li>Conditions are any expression that evaluates to truthy / falsy.</li>
</ul>
<h4>Truthy / Falsy</h4>
<p>Falsy values: <code>0</code>, <code>0.0</code>, <code>""</code>,
<code>[]</code>, <code>{}</code>, <code>()</code>, <code>None</code>,
<code>False</code>. Everything else is truthy.</p>"""),

            ("while-loops", "control-flow",
             "while Loops",
             """<h3>while Loops</h3>
<p>Repeat while a condition is True.</p>
<pre><code>count = 0
while count < 5:
    print(count)
    count += 1
# Output: 0 1 2 3 4</code></pre>
<h4>while-else</h4>
<p>The <code>else</code> block runs when the condition becomes False
(not when exited via <code>break</code>).</p>
<pre><code>n = 3
while n > 0:
    n -= 1
else:
    print("done")   # prints</code></pre>
<h4>break / continue inside while</h4>
<pre><code>i = 0
while True:
    if i == 5:
        break
    if i % 2 == 0:
        i += 1
        continue
    print(i)
    i += 1
# Output: 1 3</code></pre>"""),

            ("for-loops-range", "control-flow",
             "for Loops and range()",
             """<h3>for Loops</h3>
<p>Iterate over any iterable: list, string, range, dict…</p>
<pre><code>for fruit in ["apple", "banana"]:
    print(fruit)

for char in "Hi":
    print(char)
</code></pre>
<h3>range()</h3>
<pre><code>range(5)          # 0,1,2,3,4
range(2, 6)       # 2,3,4,5
range(0, 10, 2)   # 0,2,4,6,8
range(5, 0, -1)   # 5,4,3,2,1</code></pre>
<h4>for-else</h4>
<p><code>else</code> runs after the loop finishes normally (no break).</p>
<pre><code>for i in range(5):
    if i == 10:
        break
else:
    print("no break")   # prints</code></pre>"""),

            # ── Domain 3 ──────────────────────────────────────────────
            ("lists-methods", "data-collections",
             "Lists and List Methods",
             """<h3>Lists</h3>
<p>Ordered, <strong>mutable</strong>, zero-indexed collections.</p>
<pre><code>nums = [3, 1, 4, 1, 5, 9]
print(nums[0])   # 3
print(nums[-1])  # 9
nums[0] = 100    # mutate</code></pre>
<h3>Common methods</h3>
<pre><code>nums.append(2)       # add to end
nums.insert(0, 7)    # insert at index
nums.remove(1)       # remove first occurrence of value
nums.pop()           # remove & return last item
nums.pop(1)          # remove & return item at index 1
nums.sort()          # sort in place
nums.reverse()       # reverse in place
nums.index(4)        # index of first 4
nums.count(1)        # how many times 1 appears
sorted(nums)         # returns new sorted list (non-destructive)
len(nums)            # number of elements</code></pre>"""),

            ("tuples-immutability", "data-collections",
             "Tuples and Immutability",
             """<h3>Tuples</h3>
<p>Ordered, <strong>immutable</strong> sequences.</p>
<pre><code>point   = (3, 4)
colors  = ("red", "green", "blue")
single  = (42,)      # trailing comma required for 1-element tuple
empty   = ()

print(point[0])      # 3
x, y = point         # unpacking</code></pre>
<h4>Why use tuples?</h4>
<ul>
<li>Faster than lists for fixed data</li>
<li>Can be used as dictionary keys (lists cannot)</li>
<li>Signal "this data should not change"</li>
</ul>
<pre><code># Raises TypeError:
point[0] = 10   # TypeError: 'tuple' does not support item assignment</code></pre>"""),

            ("dictionaries", "data-collections",
             "Dictionaries",
             """<h3>Dictionaries</h3>
<p>Key-value pairs. Keys must be <strong>immutable</strong> (str, int, tuple).</p>
<pre><code>student = {"name": "Alice", "age": 20, "grade": "A"}
print(student["name"])      # Alice
student["age"] = 21         # update
student["email"] = "a@b.c"  # add new key
del student["grade"]        # delete</code></pre>
<h3>Safe access</h3>
<pre><code>student.get("gpa")          # None (no KeyError)
student.get("gpa", 0.0)     # 0.0 default</code></pre>
<h3>Iteration</h3>
<pre><code>for k in student:                   # iterate keys
    print(k, student[k])

for k, v in student.items():       # key-value pairs
    print(f"{k}: {v}")

list(student.keys())
list(student.values())</code></pre>"""),

            # ── Domain 4 ──────────────────────────────────────────────
            ("functions-return", "functions-exceptions",
             "Defining Functions and return",
             """<h3>Functions</h3>
<p>Reusable named blocks defined with <code>def</code>.</p>
<pre><code>def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))   # Hello, Alice!</code></pre>
<h4>return</h4>
<ul>
<li>Sends a value back to the caller.</li>
<li>A function without an explicit <code>return</code> returns
<code>None</code>.</li>
<li>Code after <code>return</code> is unreachable.</li>
</ul>
<pre><code>def add(a, b):
    return a + b       # returns the sum

def nothing():
    pass               # implicitly returns None

result = nothing()
print(result)          # None</code></pre>"""),

            ("parameters-arguments", "functions-exceptions",
             "Parameters, Arguments, and Defaults",
             """<h3>Parameters vs Arguments</h3>
<p><strong>Parameters</strong> appear in the function definition.
<strong>Arguments</strong> are the values passed at the call site.</p>
<pre><code>def power(base, exponent=2):   # parameters
    return base ** exponent

power(3)                       # argument 3 → base, exponent defaults to 2
power(3, 3)                    # positional arguments
power(base=2, exponent=10)     # keyword arguments</code></pre>
<h4>Rules</h4>
<ul>
<li>Parameters with defaults must come <em>after</em> those without.</li>
<li>Positional arguments must come before keyword arguments in a call.</li>
</ul>
<pre><code>def wrong(x=1, y):   # SyntaxError
    pass</code></pre>"""),

            ("scope-global", "functions-exceptions",
             "Scope, Shadowing, and global",
             """<h3>Scope — where variables live</h3>
<p>Python uses <strong>LEGB</strong> order: Local → Enclosing → Global → Built-in.</p>
<pre><code>x = "global"

def my_func():
    x = "local"    # shadows the global x
    print(x)       # local

my_func()
print(x)           # global  ← unchanged</code></pre>
<h3>global keyword</h3>
<pre><code>counter = 0

def increment():
    global counter     # refers to the module-level counter
    counter += 1

increment()
increment()
print(counter)     # 2</code></pre>
<p class="alert alert-warning">Use <code>global</code> sparingly — it makes
code harder to reason about.</p>"""),

            ("exceptions-try-except", "functions-exceptions",
             "Exceptions and try/except",
             """<h3>Exception Handling</h3>
<pre><code>try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")
finally:
    print("Always runs")</code></pre>
<h3>Multiple except blocks</h3>
<pre><code>try:
    x = int(input())
    print(10 / x)
except ValueError:
    print("Not a number")
except ZeroDivisionError:
    print("Cannot be zero")
except Exception as e:
    print(f"Unexpected: {e}")</code></pre>
<h3>Common PCEP exceptions</h3>
<ul>
<li><code>ZeroDivisionError</code> — dividing by zero</li>
<li><code>IndexError</code> — sequence index out of range</li>
<li><code>KeyError</code> — dict key not found</li>
<li><code>TypeError</code> — operation on wrong type</li>
<li><code>ValueError</code> — right type, wrong value (e.g. int("abc"))</li>
<li><code>NameError</code> — variable not defined</li>
</ul>"""),
        ]
        for topic_slug, domain_slug, title, content in lessons:
            topic = Topic.objects.get(slug=topic_slug, domain__slug=domain_slug)
            slug = title.lower().replace(" ", "-")[:48].rstrip("-")
            Lesson.objects.update_or_create(
                topic=topic, slug=slug,
                defaults={"title": title, "content": content.strip(), "order": 1},
            )

    # ══════════════════════════════════════════════════════════════════
    # FLASHCARDS  (50 total)
    # ══════════════════════════════════════════════════════════════════
    def _seed_flashcards(self):
        # (topic_slug, domain_slug, front, back)
        cards = [
            # ── Domain 1: Fundamentals (17 cards) ─────────────────────
            ("interpreter-vs-compiler", "fundamentals",
             "What does a Python interpreter do?",
             "Executes source code line by line, stopping at the first error it encounters."),
            ("interpreter-vs-compiler", "fundamentals",
             "Is Python compiled or interpreted?",
             "Both — CPython compiles source to bytecode, then interprets the bytecode on the PVM."),
            ("lexis-syntax-semantics", "fundamentals",
             "What is the difference between a syntax error and a semantic error?",
             "A syntax error breaks grammar rules and is caught before running. "
             "A semantic error is valid syntax but produces wrong behaviour at runtime."),
            ("lexis-syntax-semantics", "fundamentals",
             "Name the three layers of a programming language.",
             "Lexis (vocabulary), Syntax (grammar), Semantics (meaning)."),
            ("keywords-indentation-comments", "fundamentals",
             "How does Python define code blocks?",
             "With indentation (spaces or tabs) — not curly braces."),
            ("keywords-indentation-comments", "fundamentals",
             "How do you write a single-line comment in Python?",
             "Start the line (or the comment) with #. Everything after # is ignored."),
            ("keywords-indentation-comments", "fundamentals",
             "Can you use 'class' as a variable name?",
             "No — 'class' is a reserved keyword. Using it raises a SyntaxError."),
            ("literals-variables", "fundamentals",
             "What is a literal?",
             "A fixed value written directly in source code, e.g. 42, 3.14, 'hello', True, None."),
            ("literals-variables", "fundamentals",
             "What is 0xFF in decimal?",
             "255 — it is a hexadecimal literal."),
            ("literals-variables", "fundamentals",
             "What is 0o17 in decimal?",
             "15 — it is an octal literal."),
            ("naming-conventions-pep8", "fundamentals",
             "What naming style does PEP 8 recommend for variables?",
             "snake_case: all lowercase, words separated by underscores."),
            ("numeric-string-operators", "fundamentals",
             "What does the ** operator do?",
             "Exponentiation. 2 ** 8 = 256."),
            ("numeric-string-operators", "fundamentals",
             "What does // do?",
             "Floor (integer) division — result is rounded toward negative infinity. 7 // 2 = 3."),
            ("numeric-string-operators", "fundamentals",
             "What is operator precedence for: 2 + 3 * 4?",
             "14 — multiplication before addition (PEMDAS / BODMAS)."),
            ("boolean-relational-bitwise", "fundamentals",
             "What does 'not True' evaluate to?",
             "False."),
            ("type-casting", "fundamentals",
             "What does int('42') return?",
             "The integer 42."),
            ("print-input", "fundamentals",
             "What type does input() always return?",
             "str — you must cast to int or float if you need a number."),

            # ── Domain 2: Control Flow (12 cards) ─────────────────────
            ("conditionals", "control-flow",
             "What happens when no condition matches and there is no else?",
             "Nothing — the entire if block is skipped."),
            ("conditionals", "control-flow",
             "Are 0, '', [], and None truthy or falsy?",
             "All are falsy. Any non-zero number and non-empty container is truthy."),
            ("while-loops", "control-flow",
             "When does a while loop's else block run?",
             "When the condition becomes False normally — NOT when the loop exits via break."),
            ("while-loops", "control-flow",
             "What causes an infinite loop?",
             "A condition that never becomes False and no break statement to exit."),
            ("for-loops-range", "control-flow",
             "What does range(2, 9, 2) produce?",
             "2, 4, 6, 8"),
            ("for-loops-range", "control-flow",
             "What does range(5, 0, -1) produce?",
             "5, 4, 3, 2, 1"),
            ("break-continue-pass", "control-flow",
             "What does break do?",
             "Immediately exits the nearest enclosing loop."),
            ("break-continue-pass", "control-flow",
             "What does continue do?",
             "Skips the rest of the current iteration and goes back to the loop condition."),
            ("break-continue-pass", "control-flow",
             "What does pass do?",
             "Nothing — it is a syntactic placeholder for an empty block."),
            ("nested-loops", "control-flow",
             "How many times does the inner body run if outer runs 3 times and inner runs 4 times?",
             "12 times — outer_count × inner_count."),
            ("for-loops-range", "control-flow",
             "Can you iterate over a string with a for loop?",
             "Yes — for ch in 'Python': iterates over each character."),

            # ── Domain 3: Data Collections (11 cards) ─────────────────
            ("lists-methods", "data-collections",
             "Are lists mutable or immutable?",
             "Mutable — you can change, add, or remove elements after creation."),
            ("lists-methods", "data-collections",
             "What does list.pop() return?",
             "The last element (removed from the list). pop(i) removes and returns index i."),
            ("list-slicing-comprehensions", "data-collections",
             "What does my_list[1:4] return?",
             "A new list with elements at indices 1, 2, 3 (the stop index is exclusive)."),
            ("list-slicing-comprehensions", "data-collections",
             "What is [x**2 for x in range(4)]?",
             "[0, 1, 4, 9] — a list comprehension."),
            ("tuples-immutability", "data-collections",
             "Can you change a tuple element after creation?",
             "No — tuples are immutable. Attempting it raises TypeError."),
            ("tuples-immutability", "data-collections",
             "How do you create a one-element tuple?",
             "(42,) — the trailing comma is required. (42) is just parentheses around an int."),
            ("dictionaries", "data-collections",
             "What does dict.get(key, default) do?",
             "Returns the value for key if it exists; returns default (or None) otherwise. No KeyError."),
            ("dictionaries", "data-collections",
             "Can you use a list as a dictionary key?",
             "No — keys must be immutable. Lists are mutable, so they raise TypeError."),
            ("strings-methods", "data-collections",
             "Are Python strings mutable?",
             "No — strings are immutable. str methods return new strings."),
            ("strings-methods", "data-collections",
             "What does 'Hello World'.split() return?",
             "['Hello', 'World'] — splits on whitespace by default."),
            ("strings-methods", "data-collections",
             "What does 'python'.upper() return?",
             "'PYTHON'"),

            # ── Domain 4: Functions & Exceptions (10 cards) ────────────
            ("functions-return", "functions-exceptions",
             "What does a function return if it has no return statement?",
             "None."),
            ("functions-return", "functions-exceptions",
             "Can a function return more than one value?",
             "Yes — return a, b returns a tuple (a, b)."),
            ("parameters-arguments", "functions-exceptions",
             "What is a default parameter?",
             "A parameter with a preset value: def f(x=10). Used when no argument is passed."),
            ("parameters-arguments", "functions-exceptions",
             "Must default parameters come before or after non-default ones?",
             "After. def f(x, y=2) is valid; def f(x=1, y) is a SyntaxError."),
            ("scope-global", "functions-exceptions",
             "What does the global keyword do inside a function?",
             "Allows the function to read and modify the module-level (global) variable."),
            ("scope-global", "functions-exceptions",
             "What is variable shadowing?",
             "When a local variable has the same name as a global one, hiding the global inside that scope."),
            ("recursion", "functions-exceptions",
             "What is a base case in recursion?",
             "The condition that stops the recursion. Without it the function recurses infinitely."),
            ("exceptions-try-except", "functions-exceptions",
             "Name five common built-in exceptions.",
             "ZeroDivisionError, IndexError, KeyError, TypeError, ValueError."),
            ("exceptions-try-except", "functions-exceptions",
             "When does the finally block run?",
             "Always — whether or not an exception was raised or caught."),
            ("exceptions-try-except", "functions-exceptions",
             "What does 'except Exception as e' do?",
             "Catches any exception derived from Exception and binds it to the variable e."),
        ]
        for topic_slug, domain_slug, front, back in cards:
            topic = Topic.objects.get(slug=topic_slug, domain__slug=domain_slug)
            Flashcard.objects.update_or_create(
                topic=topic, front=front,
                defaults={"back": back, "order": 0},
            )

    # ══════════════════════════════════════════════════════════════════
    # QUIZ QUESTIONS  (80 total — 20 per domain)
    # ══════════════════════════════════════════════════════════════════
    def _seed_questions(self):
        Question.objects.all().delete()
        for q in self._all_questions():
            topic = Topic.objects.get(slug=q["topic"], domain__slug=q["domain"])
            obj = Question.objects.create(
                topic=topic,
                text=q["text"],
                question_type=q.get("qtype", "mc"),
                code_snippet=q.get("code", ""),
                explanation=q.get("why", ""),
                hint=q.get("hint", ""),
                difficulty=q.get("diff", "medium"),
            )
            for i, (text, correct) in enumerate(q["choices"]):
                AnswerChoice.objects.create(question=obj, text=text, is_correct=correct, order=i)

    def _all_questions(self):  # noqa: PLR0915 — intentionally long data method
        return [

            # ══ DOMAIN 1: FUNDAMENTALS (20 questions) ══════════════════

            {   "domain": "fundamentals", "topic": "interpreter-vs-compiler",
                "diff": "easy",
                "text": "Which statement best describes how CPython executes a script?",
                "why": "CPython compiles to bytecode first, then the PVM interprets that bytecode.",
                "choices": [
                    ("It compiles the source to native machine code, then runs it", False),
                    ("It compiles source to bytecode, then interprets the bytecode on the PVM", True),
                    ("It interprets source directly without any compilation step", False),
                    ("It sends source code to the OS kernel for execution", False),
                ],
            },
            {   "domain": "fundamentals", "topic": "interpreter-vs-compiler",
                "diff": "easy",
                "text": "An interpreter stops at the first error it encounters. What does this mean for a 10-line script with an error on line 6?",
                "why": "Lines 1–5 execute; then the interpreter hits line 6 and raises an exception.",
                "choices": [
                    ("Lines 1–5 execute, then an error is raised on line 6", True),
                    ("No lines execute — the whole script is checked first", False),
                    ("Lines 7–10 execute instead", False),
                    ("All 10 lines execute and errors are shown at the end", False),
                ],
            },
            {   "domain": "fundamentals", "topic": "lexis-syntax-semantics",
                "diff": "easy",
                "text": "Which of the following contains a syntax error?",
                "choices": [
                    ('x = 1 + 2', False),
                    ('if x > 0', False),
                    ('print("hello"', True),
                    ('y = x * 2', False),
                ],
                "why": 'print("hello" is missing the closing parenthesis — a syntax error.',
            },
            {   "domain": "fundamentals", "topic": "lexis-syntax-semantics",
                "diff": "easy",
                "text": 'Which layer of a language does "the rules for combining tokens" describe?',
                "choices": [
                    ("Lexis", False),
                    ("Syntax", True),
                    ("Semantics", False),
                    ("Pragmatics", False),
                ],
                "why": "Syntax is the grammar — how tokens may legally be combined.",
            },
            {   "domain": "fundamentals", "topic": "keywords-indentation-comments",
                "diff": "easy",
                "text": "Which of these is NOT a Python keyword?",
                "choices": [
                    ("pass", False),
                    ("global", False),
                    ("until", True),
                    ("yield", False),
                ],
                "why": "'until' does not exist in Python. Use 'while not ...' instead.",
            },
            {   "domain": "fundamentals", "topic": "keywords-indentation-comments",
                "diff": "easy",
                "text": "What does Python use to define code blocks?",
                "choices": [
                    ("Curly braces {}", False),
                    ("BEGIN/END keywords", False),
                    ("Consistent indentation", True),
                    ("Semicolons", False),
                ],
                "why": "Python relies on indentation, not braces or keywords, to delimit blocks.",
            },
            {   "domain": "fundamentals", "topic": "literals-variables",
                "diff": "easy",
                "text": "What is the decimal value of the octal literal 0o17?",
                "choices": [
                    ("7", False),
                    ("15", True),
                    ("17", False),
                    ("23", False),
                ],
                "why": "0o17 = 1×8 + 7×1 = 15.",
            },
            {   "domain": "fundamentals", "topic": "literals-variables",
                "diff": "easy",
                "text": "Which of these is a valid Python variable name?",
                "choices": [
                    ("2fast", False),
                    ("my-var", False),
                    ("_count", True),
                    ("class", False),
                ],
                "why": "_count starts with an underscore, which is allowed. The others are invalid.",
            },
            {   "domain": "fundamentals", "topic": "naming-conventions-pep8",
                "diff": "easy",
                "text": "PEP 8 recommends which naming style for ordinary variables and function names?",
                "choices": [
                    ("camelCase", False),
                    ("PascalCase", False),
                    ("snake_case", True),
                    ("SCREAMING_SNAKE_CASE", False),
                ],
                "why": "PEP 8 uses snake_case for variables/functions, PascalCase for classes.",
            },
            {   "domain": "fundamentals", "topic": "numeric-string-operators",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What does this expression evaluate to?",
                "code": "print(2 + 3 * 4)",
                "choices": [
                    ("20", False),
                    ("14", True),
                    ("24", False),
                    ("11", False),
                ],
                "why": "Multiplication before addition: 3*4=12, then 2+12=14.",
            },
            {   "domain": "fundamentals", "topic": "numeric-string-operators",
                "diff": "easy",
                "text": "What is the result of 17 // 5?",
                "choices": [
                    ("3", True),
                    ("3.4", False),
                    ("2", False),
                    ("4", False),
                ],
                "why": "// is floor division: 17 ÷ 5 = 3 remainder 2, so the result is 3.",
            },
            {   "domain": "fundamentals", "topic": "numeric-string-operators",
                "diff": "easy",
                "text": "What does 17 % 5 evaluate to?",
                "choices": [
                    ("3", False),
                    ("2", True),
                    ("3.4", False),
                    ("0", False),
                ],
                "why": "% is modulo: 17 = 3×5 + 2, so the remainder is 2.",
            },
            {   "domain": "fundamentals", "topic": "boolean-relational-bitwise",
                "diff": "easy",
                "qtype": "tf",
                "text": "True: The expression (True and False) evaluates to False.",
                "choices": [
                    ("True", True),
                    ("False", False),
                ],
                "why": "and requires both operands to be truthy; False makes the whole thing False.",
            },
            {   "domain": "fundamentals", "topic": "type-casting",
                "diff": "easy",
                "text": "What does int('3.5') do?",
                "choices": [
                    ("Returns 3", False),
                    ("Returns 4", False),
                    ("Raises ValueError", True),
                    ("Returns 3.5", False),
                ],
                "why": "int() cannot convert a string containing a decimal point — use float() first.",
            },
            {   "domain": "fundamentals", "topic": "type-casting",
                "diff": "easy",
                "text": "What does float(True) return?",
                "choices": [
                    ("1.0", True),
                    ("0.0", False),
                    ("True", False),
                    ("TypeError", False),
                ],
                "why": "True is treated as 1 in numeric contexts, so float(True) = 1.0.",
            },
            {   "domain": "fundamentals", "topic": "print-input",
                "diff": "easy",
                "text": "What does input() always return regardless of what the user types?",
                "choices": [
                    ("int", False),
                    ("float", False),
                    ("str", True),
                    ("The type depends on what the user enters", False),
                ],
                "why": "input() always returns a str. You must cast it if you need a number.",
            },
            {   "domain": "fundamentals", "topic": "print-input",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "print(1, 2, 3, sep='-')",
                "choices": [
                    ("1 2 3", False),
                    ("1-2-3", True),
                    ("123", False),
                    ("1, 2, 3", False),
                ],
                "why": "sep='-' replaces the default space separator with a hyphen.",
            },
            {   "domain": "fundamentals", "topic": "literals-variables",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = 5\ny = x\nx = 10\nprint(y)",
                "choices": [
                    ("10", False),
                    ("5", True),
                    ("None", False),
                    ("Error", False),
                ],
                "why": "y = x copies the value 5 into y. Reassigning x does not change y.",
            },
            {   "domain": "fundamentals", "topic": "numeric-string-operators",
                "diff": "medium",
                "text": "What is the result of 2 ** 10?",
                "choices": [
                    ("20", False),
                    ("512", False),
                    ("1024", True),
                    ("210", False),
                ],
                "why": "** is exponentiation. 2^10 = 1024.",
            },
            {   "domain": "fundamentals", "topic": "type-casting",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "print(str(True))",
                "choices": [
                    ("1", False),
                    ("True", True),
                    ("'True'", False),
                    ("true", False),
                ],
                "why": "str(True) returns the string 'True' (capital T).",
            },

            # ══ DOMAIN 2: CONTROL FLOW (20 questions) ══════════════════

            {   "domain": "control-flow", "topic": "conditionals",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = 7\nif x > 10:\n    print('big')\nelif x > 5:\n    print('medium')\nelse:\n    print('small')",
                "choices": [
                    ("big", False),
                    ("medium", True),
                    ("small", False),
                    ("big\nmedium", False),
                ],
                "why": "x=7 is not > 10, but is > 5, so 'medium' prints.",
            },
            {   "domain": "control-flow", "topic": "conditionals",
                "diff": "easy",
                "text": "Which value is falsy in Python?",
                "choices": [
                    ("1", False),
                    ("'False'", False),
                    ("[]", True),
                    ("[0]", False),
                ],
                "why": "An empty list [] is falsy. A non-empty list (even [0]) is truthy.",
            },
            {   "domain": "control-flow", "topic": "conditionals",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = 0\nif x:\n    print('yes')\nelse:\n    print('no')",
                "choices": [
                    ("yes", False),
                    ("no", True),
                    ("0", False),
                    ("Error", False),
                ],
                "why": "0 is falsy, so the else branch runs.",
            },
            {   "domain": "control-flow", "topic": "while-loops",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "n = 3\nwhile n > 0:\n    print(n)\n    n -= 1",
                "choices": [
                    ("3 2 1", False),
                    ("3\n2\n1", True),
                    ("1\n2\n3", False),
                    ("0\n1\n2\n3", False),
                ],
                "why": "Loop prints 3, 2, 1 on separate lines (each print adds a newline).",
            },
            {   "domain": "control-flow", "topic": "while-loops",
                "diff": "medium",
                "text": "A while loop's else block does NOT run when:",
                "choices": [
                    ("The condition becomes False naturally", False),
                    ("The loop body completes all iterations", False),
                    ("A break statement exits the loop", True),
                    ("The loop runs zero times", False),
                ],
                "why": "break skips the else block. A natural exit runs the else.",
            },
            {   "domain": "control-flow", "topic": "for-loops-range",
                "diff": "easy",
                "text": "What does range(2, 8, 2) produce?",
                "choices": [
                    ("2, 4, 6", True),
                    ("2, 4, 6, 8", False),
                    ("0, 2, 4, 6", False),
                    ("2, 3, 4, 5, 6, 7", False),
                ],
                "why": "range(start=2, stop=8, step=2): 2, 4, 6. 8 is excluded.",
            },
            {   "domain": "control-flow", "topic": "for-loops-range",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "for i in range(3):\n    print(i)",
                "choices": [
                    ("1\n2\n3", False),
                    ("0\n1\n2", True),
                    ("0\n1\n2\n3", False),
                    ("3", False),
                ],
                "why": "range(3) produces 0, 1, 2.",
            },
            {   "domain": "control-flow", "topic": "for-loops-range",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "for ch in 'Hi':\n    print(ch)",
                "choices": [
                    ("Hi", False),
                    ("H\ni", True),
                    ("H i", False),
                    ("Error", False),
                ],
                "why": "Iterating a string yields one character per iteration.",
            },
            {   "domain": "control-flow", "topic": "break-continue-pass",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "for i in range(5):\n    if i == 3:\n        break\n    print(i)",
                "choices": [
                    ("0\n1\n2", True),
                    ("0\n1\n2\n3", False),
                    ("3\n4", False),
                    ("0\n1\n2\n3\n4", False),
                ],
                "why": "break exits the loop when i==3. 0, 1, 2 have already printed.",
            },
            {   "domain": "control-flow", "topic": "break-continue-pass",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "for i in range(5):\n    if i % 2 == 0:\n        continue\n    print(i)",
                "choices": [
                    ("0\n2\n4", False),
                    ("1\n3", True),
                    ("1\n2\n3", False),
                    ("0\n1\n2\n3\n4", False),
                ],
                "why": "continue skips even numbers (i%2==0). Only odd values 1 and 3 print.",
            },
            {   "domain": "control-flow", "topic": "break-continue-pass",
                "diff": "easy",
                "text": "Which statement is a valid use of pass?",
                "choices": [
                    ("As a substitute for break inside a loop", False),
                    ("To skip to the next iteration", False),
                    ("As a placeholder in an empty function body", True),
                    ("To exit a function early", False),
                ],
                "why": "pass is a no-op placeholder used where Python syntax requires a statement.",
            },
            {   "domain": "control-flow", "topic": "for-loops-range",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "total = 0\nfor i in range(1, 5):\n    total += i\nprint(total)",
                "choices": [
                    ("10", True),
                    ("9", False),
                    ("15", False),
                    ("4", False),
                ],
                "why": "1+2+3+4 = 10.",
            },
            {   "domain": "control-flow", "topic": "nested-loops",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is printed?",
                "code": "for i in range(2):\n    for j in range(3):\n        print(i, j)",
                "choices": [
                    ("0 0\n0 1\n0 2\n1 0\n1 1\n1 2", True),
                    ("0 0\n1 1\n2 2", False),
                    ("0 1 2\n0 1 2", False),
                    ("6 pairs with different ordering", False),
                ],
                "why": "Outer loop i: 0,1. For each i, inner loop j: 0,1,2. 6 pairs total.",
            },
            {   "domain": "control-flow", "topic": "while-loops",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "i = 0\nwhile i < 3:\n    i += 1\nelse:\n    print('done')",
                "choices": [
                    ("done", True),
                    ("0\n1\n2\ndone", False),
                    ("Nothing", False),
                    ("Error", False),
                ],
                "why": "The else runs after the while condition naturally becomes False.",
            },
            {   "domain": "control-flow", "topic": "conditionals",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = 5\nif x > 5:\n    print('A')\nelif x == 5:\n    print('B')\nelif x > 0:\n    print('C')",
                "choices": [
                    ("A", False),
                    ("B", True),
                    ("C", False),
                    ("B\nC", False),
                ],
                "why": "Only the first matching branch runs. x==5 matches elif, so 'B' prints.",
            },
            {   "domain": "control-flow", "topic": "for-loops-range",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "for i in range(5):\n    if i == 3:\n        break\nelse:\n    print('no break')",
                "choices": [
                    ("no break", False),
                    ("Nothing", True),
                    ("3", False),
                    ("Error", False),
                ],
                "why": "break prevents the else from running. Nothing is printed.",
            },
            {   "domain": "control-flow", "topic": "nested-loops",
                "diff": "hard",
                "text": "How many times does print() execute?",
                "code": "for i in range(3):\n    for j in range(4):\n        print(i * j)",
                "choices": [
                    ("7", False),
                    ("12", True),
                    ("3", False),
                    ("4", False),
                ],
                "why": "3 outer × 4 inner = 12 iterations.",
            },
            {   "domain": "control-flow", "topic": "break-continue-pass",
                "diff": "easy",
                "text": "What does pass do at runtime?",
                "choices": [
                    ("Exits the current block", False),
                    ("Skips to the next loop iteration", False),
                    ("Does nothing — it is a no-op", True),
                    ("Pauses execution", False),
                ],
                "why": "pass is purely syntactic — it lets you write empty blocks without errors.",
            },
            {   "domain": "control-flow", "topic": "while-loops",
                "diff": "easy",
                "text": "Which code creates an infinite loop?",
                "choices": [
                    ("while True: break", False),
                    ("while True: pass", True),
                    ("while False: print('x')", False),
                    ("for i in range(0): pass", False),
                ],
                "why": "'while True: pass' never changes the condition or breaks out.",
            },
            {   "domain": "control-flow", "topic": "conditionals",
                "diff": "easy",
                "qtype": "tf",
                "text": "True: You can have multiple elif clauses in a single if statement.",
                "choices": [("True", True), ("False", False)],
                "why": "Python allows any number of elif clauses between if and else.",
            },

            # ══ DOMAIN 3: DATA COLLECTIONS (20 questions) ══════════════

            {   "domain": "data-collections", "topic": "lists-methods",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "nums = [10, 20, 30]\nprint(nums[1])",
                "choices": [
                    ("10", False),
                    ("20", True),
                    ("30", False),
                    ("Error", False),
                ],
                "why": "List indices start at 0. nums[1] is the second element, 20.",
            },
            {   "domain": "data-collections", "topic": "lists-methods",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "nums = [1, 2, 3, 4, 5]\nprint(nums[-2])",
                "choices": [
                    ("4", True),
                    ("5", False),
                    ("2", False),
                    ("Error", False),
                ],
                "why": "Negative index -1 is last, -2 is second-to-last: 4.",
            },
            {   "domain": "data-collections", "topic": "list-slicing-comprehensions",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = [0, 1, 2, 3, 4]\nprint(x[1:4])",
                "choices": [
                    ("[1, 2, 3]", True),
                    ("[1, 2, 3, 4]", False),
                    ("[0, 1, 2, 3]", False),
                    ("[2, 3, 4]", False),
                ],
                "why": "Slicing [1:4] includes indices 1, 2, 3. The stop index (4) is excluded.",
            },
            {   "domain": "data-collections", "topic": "list-slicing-comprehensions",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "print([x * 2 for x in range(4)])",
                "choices": [
                    ("[2, 4, 6, 8]", False),
                    ("[0, 2, 4, 6]", True),
                    ("[1, 2, 3, 4]", False),
                    ("[0, 1, 2, 3]", False),
                ],
                "why": "range(4) is 0,1,2,3. Doubling: 0,2,4,6.",
            },
            {   "domain": "data-collections", "topic": "lists-methods",
                "diff": "easy",
                "text": "What does list.append(x) do?",
                "choices": [
                    ("Inserts x at index 0", False),
                    ("Adds x to the end of the list", True),
                    ("Removes x from the list", False),
                    ("Returns a new list with x added", False),
                ],
                "why": "append() mutates the list in place by adding to the end.",
            },
            {   "domain": "data-collections", "topic": "lists-methods",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "a = [3, 1, 4, 1, 5]\na.sort()\nprint(a)",
                "choices": [
                    ("[3, 1, 4, 1, 5]", False),
                    ("[1, 1, 3, 4, 5]", True),
                    ("[5, 4, 3, 1, 1]", False),
                    ("Error", False),
                ],
                "why": "sort() sorts in place. The list becomes [1, 1, 3, 4, 5].",
            },
            {   "domain": "data-collections", "topic": "tuples-immutability",
                "diff": "easy",
                "text": "Which of these creates a tuple with one element?",
                "choices": [
                    ("(42)", False),
                    ("(42,)", True),
                    ("[42]", False),
                    ("{42}", False),
                ],
                "why": "(42) is just parentheses around 42. The trailing comma is required: (42,).",
            },
            {   "domain": "data-collections", "topic": "tuples-immutability",
                "diff": "easy",
                "text": "What error is raised when you try to assign to a tuple element?",
                "choices": [
                    ("ValueError", False),
                    ("IndexError", False),
                    ("TypeError", True),
                    ("AttributeError", False),
                ],
                "why": "Tuples are immutable. Assigning to an index raises TypeError.",
            },
            {   "domain": "data-collections", "topic": "tuples-immutability",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "t = (1, 2, 3)\nx, y, z = t\nprint(y)",
                "choices": [
                    ("1", False),
                    ("2", True),
                    ("3", False),
                    ("(1,2,3)", False),
                ],
                "why": "Tuple unpacking assigns 1→x, 2→y, 3→z. y is 2.",
            },
            {   "domain": "data-collections", "topic": "dictionaries",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "d = {'a': 1, 'b': 2}\nprint(d.get('c', 99))",
                "choices": [
                    ("None", False),
                    ("KeyError", False),
                    ("99", True),
                    ("0", False),
                ],
                "why": "'c' is not in d, so .get() returns the default value 99.",
            },
            {   "domain": "data-collections", "topic": "dictionaries",
                "diff": "medium",
                "text": "Which of these cannot be used as a dictionary key?",
                "choices": [
                    ("42", False),
                    ("(1, 2)", False),
                    ("[1, 2]", True),
                    ('"hello"', False),
                ],
                "why": "List [1, 2] is mutable and unhashable — it raises TypeError as a key.",
            },
            {   "domain": "data-collections", "topic": "dictionaries",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "d = {'x': 10, 'y': 20}\nfor k, v in d.items():\n    print(k, v)",
                "choices": [
                    ("x\ny", False),
                    ("x 10\ny 20", True),
                    ("10\n20", False),
                    ("Error", False),
                ],
                "why": ".items() yields (key, value) pairs. Each is unpacked into k and v.",
            },
            {   "domain": "data-collections", "topic": "strings-methods",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "s = 'Hello'\nprint(s[1:4])",
                "choices": [
                    ("Hel", False),
                    ("ell", True),
                    ("ello", False),
                    ("Hell", False),
                ],
                "why": "s[1:4] = characters at indices 1, 2, 3 = 'e', 'l', 'l' → 'ell'.",
            },
            {   "domain": "data-collections", "topic": "strings-methods",
                "diff": "easy",
                "text": "What does 'Python'.upper() return?",
                "choices": [
                    ("'PYTHON'", True),
                    ("'python'", False),
                    ("'Python'", False),
                    ("None", False),
                ],
                "why": "upper() returns a new string with all letters uppercase.",
            },
            {   "domain": "data-collections", "topic": "strings-methods",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "print('ab' * 3)",
                "choices": [
                    ("ababab", True),
                    ("ab ab ab", False),
                    ("6", False),
                    ("Error", False),
                ],
                "why": "String repetition: 'ab' repeated 3 times = 'ababab'.",
            },
            {   "domain": "data-collections", "topic": "strings-methods",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "print('  hello  '.strip())",
                "choices": [
                    ("'  hello  '", False),
                    ("hello", True),
                    ("  hello", False),
                    ("hello  ", False),
                ],
                "why": "strip() removes leading and trailing whitespace.",
            },
            {   "domain": "data-collections", "topic": "nested-lists",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "matrix = [[1, 2], [3, 4]]\nprint(matrix[1][0])",
                "choices": [
                    ("1", False),
                    ("2", False),
                    ("3", True),
                    ("4", False),
                ],
                "why": "matrix[1] = [3, 4]; [3, 4][0] = 3.",
            },
            {   "domain": "data-collections", "topic": "lists-methods",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "nums = [1, 2, 3]\nnums.pop()\nprint(nums)",
                "choices": [
                    ("[1, 2]", True),
                    ("[2, 3]", False),
                    ("[1, 2, 3]", False),
                    ("[1]", False),
                ],
                "why": "pop() removes and returns the last element. [1, 2, 3] → [1, 2].",
            },
            {   "domain": "data-collections", "topic": "list-slicing-comprehensions",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = [0, 1, 2, 3, 4]\nprint(x[::2])",
                "choices": [
                    ("[0, 2, 4]", True),
                    ("[1, 3]", False),
                    ("[0, 1, 2]", False),
                    ("[4, 2, 0]", False),
                ],
                "why": "x[::2] starts at 0, steps by 2: indices 0, 2, 4 → [0, 2, 4].",
            },
            {   "domain": "data-collections", "topic": "dictionaries",
                "diff": "easy",
                "qtype": "tf",
                "text": "True: Dictionaries in Python 3.7+ preserve insertion order.",
                "choices": [("True", True), ("False", False)],
                "why": "Since Python 3.7 dicts are ordered by insertion as a language guarantee.",
            },

            # ══ DOMAIN 4: FUNCTIONS AND EXCEPTIONS (20 questions) ══════

            {   "domain": "functions-exceptions", "topic": "functions-return",
                "diff": "easy",
                "text": "What does a function return when it has no return statement?",
                "choices": [
                    ("0", False),
                    ("None", True),
                    ("False", False),
                    ("Error", False),
                ],
                "why": "Python implicitly returns None from functions with no return statement.",
            },
            {   "domain": "functions-exceptions", "topic": "functions-return",
                "diff": "easy",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "def add(a, b):\n    return a + b\n\nprint(add(3, 4))",
                "choices": [
                    ("7", True),
                    ("34", False),
                    ("None", False),
                    ("Error", False),
                ],
                "why": "add(3, 4) returns 3 + 4 = 7.",
            },
            {   "domain": "functions-exceptions", "topic": "functions-return",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "def f():\n    return 1, 2\n\nresult = f()\nprint(type(result))",
                "choices": [
                    ("<class 'list'>", False),
                    ("<class 'tuple'>", True),
                    ("<class 'int'>", False),
                    ("Error", False),
                ],
                "why": "return 1, 2 returns a tuple (1, 2).",
            },
            {   "domain": "functions-exceptions", "topic": "parameters-arguments",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "def greet(name, msg='Hello'):\n    print(f'{msg}, {name}!')\n\ngreet('Alice')",
                "choices": [
                    ("Hello, Alice!", True),
                    ("Alice, Hello!", False),
                    ("Error — msg is required", False),
                    ("None", False),
                ],
                "why": "msg has a default value 'Hello', so it is optional.",
            },
            {   "domain": "functions-exceptions", "topic": "parameters-arguments",
                "diff": "medium",
                "text": "Which function definition raises a SyntaxError?",
                "choices": [
                    ("def f(x, y=2):", False),
                    ("def f(x=1, y=2):", False),
                    ("def f(x=1, y):", True),
                    ("def f(x, y):", False),
                ],
                "why": "Non-default parameters cannot follow default ones.",
            },
            {   "domain": "functions-exceptions", "topic": "scope-global",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "x = 'global'\n\ndef f():\n    x = 'local'\n    print(x)\n\nf()\nprint(x)",
                "choices": [
                    ("local\nlocal", False),
                    ("global\nglobal", False),
                    ("local\nglobal", True),
                    ("global\nlocal", False),
                ],
                "why": "x inside f is a local variable; it does not affect the global x.",
            },
            {   "domain": "functions-exceptions", "topic": "scope-global",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "total = 0\n\ndef add(n):\n    global total\n    total += n\n\nadd(5)\nadd(3)\nprint(total)",
                "choices": [
                    ("0", False),
                    ("5", False),
                    ("8", True),
                    ("Error", False),
                ],
                "why": "global total makes the function modify the module-level variable.",
            },
            {   "domain": "functions-exceptions", "topic": "recursion",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "def fact(n):\n    if n == 0:\n        return 1\n    return n * fact(n - 1)\n\nprint(fact(4))",
                "choices": [
                    ("10", False),
                    ("24", True),
                    ("4", False),
                    ("Error", False),
                ],
                "why": "4! = 4×3×2×1 = 24.",
            },
            {   "domain": "functions-exceptions", "topic": "recursion",
                "diff": "hard",
                "text": "What happens if a recursive function has no base case?",
                "choices": [
                    ("It returns None after a fixed number of calls", False),
                    ("It raises RecursionError (maximum depth exceeded)", True),
                    ("It runs forever without error", False),
                    ("Python detects the loop and stops cleanly", False),
                ],
                "why": "Python limits call depth (~1000). Without a base case it hits RecursionError.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "text": "Which exception is raised by int('abc')?",
                "choices": [
                    ("TypeError", False),
                    ("ValueError", True),
                    ("SyntaxError", False),
                    ("NameError", False),
                ],
                "why": "The type is correct (str), but the value cannot convert to int → ValueError.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "text": "Which exception is raised by 10 / 0?",
                "choices": [
                    ("ArithmeticError only", False),
                    ("ZeroDivisionError", True),
                    ("ValueError", False),
                    ("MathError", False),
                ],
                "why": "Division by zero raises ZeroDivisionError.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "try:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    print('caught')\nfinally:\n    print('done')",
                "choices": [
                    ("caught", False),
                    ("done", False),
                    ("caught\ndone", True),
                    ("Error", False),
                ],
                "why": "except catches the error; finally always runs.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "text": "Which exception is raised by my_list[100] when the list has 5 elements?",
                "choices": [
                    ("ValueError", False),
                    ("IndexError", True),
                    ("KeyError", False),
                    ("TypeError", False),
                ],
                "why": "Accessing an out-of-range index raises IndexError.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "text": "Which exception is raised by my_dict['missing_key']?",
                "choices": [
                    ("ValueError", False),
                    ("IndexError", False),
                    ("KeyError", True),
                    ("NameError", False),
                ],
                "why": "Accessing a missing dictionary key raises KeyError.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "easy",
                "text": "The finally block in a try/except/finally structure:",
                "choices": [
                    ("Only runs if an exception was raised", False),
                    ("Only runs if no exception was raised", False),
                    ("Always runs, whether or not an exception occurred", True),
                    ("Never runs if a break is inside the try", False),
                ],
                "why": "finally is guaranteed to execute for cleanup (close files, release resources).",
            },
            {   "domain": "functions-exceptions", "topic": "parameters-arguments",
                "diff": "medium",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "def f(a, b=10, c=20):\n    return a + b + c\n\nprint(f(1, c=5))",
                "choices": [
                    ("16", True),
                    ("31", False),
                    ("6", False),
                    ("Error", False),
                ],
                "why": "a=1, b defaults to 10, c is overridden to 5. 1+10+5=16.",
            },
            {   "domain": "functions-exceptions", "topic": "scope-global",
                "diff": "medium",
                "text": "What is the LEGB rule?",
                "choices": [
                    ("List, Error, Global, Boolean — Python data types", False),
                    ("The order Python searches for a variable name: Local → Enclosing → Global → Built-in", True),
                    ("Loop, Exception, Generator, Break — flow control keywords", False),
                    ("A PEP 8 style guide category", False),
                ],
                "why": "LEGB is the name resolution order Python uses when evaluating a variable name.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "hard",
                "qtype": "code_output",
                "text": "What is the output?",
                "code": "try:\n    pass\nexcept Exception:\n    print('error')\nelse:\n    print('ok')\nfinally:\n    print('done')",
                "choices": [
                    ("ok\ndone", True),
                    ("error\ndone", False),
                    ("ok", False),
                    ("done", False),
                ],
                "why": "No exception → except is skipped, else runs ('ok'), finally always runs ('done').",
            },
            {   "domain": "functions-exceptions", "topic": "functions-return",
                "diff": "easy",
                "qtype": "tf",
                "text": "True: Code written after a return statement in the same function body will never execute.",
                "choices": [("True", True), ("False", False)],
                "why": "return immediately exits the function; any code after it is unreachable.",
            },
            {   "domain": "functions-exceptions", "topic": "exceptions-try-except",
                "diff": "medium",
                "text": "What does 'except Exception as e' allow you to do?",
                "choices": [
                    ("Re-raise the exception automatically", False),
                    ("Access the exception object and its message", True),
                    ("Catch only ValueError", False),
                    ("Suppress all output from the error", False),
                ],
                "why": "'as e' binds the exception instance to e, so you can inspect it (e.g. str(e)).",
            },
        ]

    # ══════════════════════════════════════════════════════════════════
    # CODING CHALLENGES  (16 total — all 12 required types + 4 extras)
    # ══════════════════════════════════════════════════════════════════
    def _seed_challenges(self):
        challenges = [

            # ── Domain 1: Fundamentals ─────────────────────────────────

            {   "slug": "type-checker",
                "topic_slug": "type-casting", "domain_slug": "fundamentals",
                "title": "Type Checker",
                "diff": "easy", "order": 1,
                "description": (
                    "<p>Read a single value from input and print the name of its Python type.</p>"
                    "<p>Rules:</p>"
                    "<ul>"
                    "<li>If the value can be converted to <code>int</code>, print <code>int</code>.</li>"
                    "<li>Else if it can be converted to <code>float</code>, print <code>float</code>.</li>"
                    "<li>Otherwise print <code>str</code>.</li>"
                    "</ul>"
                    "<p>Example: input <code>42</code> → output <code>int</code></p>"
                ),
                "starter": (
                    "value = input()\n"
                    "# Determine whether value is int, float, or str\n"
                ),
                "expected": "int\n",
                "test_input": "42",
                "hint_1": "Try int(value) inside a try/except block first.",
                "hint_2": "If that fails, try float(value). If that also fails, it's a str.",
                "solution": (
                    "value = input()\n"
                    "try:\n"
                    "    int(value)\n"
                    "    print('int')\n"
                    "except ValueError:\n"
                    "    try:\n"
                    "        float(value)\n"
                    "        print('float')\n"
                    "    except ValueError:\n"
                    "        print('str')\n"
                ),
            },

            {   "slug": "numeral-conversion",
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "title": "Numeral Conversion",
                "diff": "easy", "order": 2,
                "description": (
                    "<p>Print the decimal values of these three literals, one per line:</p>"
                    "<ul>"
                    "<li><code>0o17</code> (octal)</li>"
                    "<li><code>0xFF</code> (hex)</li>"
                    "<li><code>0b1010</code> (binary)</li>"
                    "</ul>"
                    "<p>Expected output:</p><pre>15\n255\n10</pre>"
                ),
                "starter": "# Print decimal values of 0o17, 0xFF, and 0b1010\n",
                "expected": "15\n255\n10\n",
                "test_input": "",
                "hint_1": "Just print the literals — Python converts them automatically.",
                "hint_2": "print(0o17) outputs 15.",
                "solution": "print(0o17)\nprint(0xFF)\nprint(0b1010)\n",
            },

            {   "slug": "calculator",
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "title": "Four-Operation Calculator",
                "diff": "medium", "order": 3,
                "description": (
                    "<p>Read three lines from input:</p>"
                    "<ol>"
                    "<li>First number (float)</li>"
                    "<li>Operator: one of <code>+</code> <code>-</code> <code>*</code> <code>/</code></li>"
                    "<li>Second number (float)</li>"
                    "</ol>"
                    "<p>Print the result as a float with 2 decimal places.</p>"
                    "<p>If the operator is <code>/</code> and the second number is 0, print "
                    "<code>Error: division by zero</code> instead.</p>"
                    "<p>Example: <code>10 / + / 3</code> → <code>13.00</code></p>"
                ),
                "starter": (
                    "a = float(input())\n"
                    "op = input()\n"
                    "b = float(input())\n"
                    "# Compute and print the result\n"
                ),
                "expected": "13.00\n",
                "test_input": "10\n+\n3",
                "hint_1": "Use an if/elif chain to select the operation.",
                "hint_2": "Check for b == 0 before dividing.",
                "solution": (
                    "a = float(input())\n"
                    "op = input()\n"
                    "b = float(input())\n"
                    "if op == '+':\n"
                    "    print(f'{a + b:.2f}')\n"
                    "elif op == '-':\n"
                    "    print(f'{a - b:.2f}')\n"
                    "elif op == '*':\n"
                    "    print(f'{a * b:.2f}')\n"
                    "elif op == '/':\n"
                    "    if b == 0:\n"
                    "        print('Error: division by zero')\n"
                    "    else:\n"
                    "        print(f'{a / b:.2f}')\n"
                ),
            },

            {   "slug": "greeting-program",
                "topic_slug": "print-input", "domain_slug": "fundamentals",
                "title": "Greeting Program",
                "diff": "easy", "order": 4,
                "description": (
                    "<p>Read a name from input and print <code>Hello, NAME!</code></p>"
                ),
                "starter": "# Read a name and greet the user\n",
                "expected": "Hello, Alice!\n",
                "test_input": "Alice",
                "hint_1": "Use input() to read the name.",
                "hint_2": "Use an f-string: f'Hello, {name}!'",
                "solution": "name = input()\nprint(f'Hello, {name}!')\n",
            },

            # ── Domain 2: Control Flow ─────────────────────────────────

            {   "slug": "leap-year",
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "title": "Leap Year Checker",
                "diff": "medium", "order": 1,
                "description": (
                    "<p>Read a year from input. Print <code>Leap year</code> or "
                    "<code>Not a leap year</code>.</p>"
                    "<p>A leap year is divisible by 4, except century years (divisible by 100) "
                    "which must also be divisible by 400.</p>"
                ),
                "starter": "year = int(input())\n# Check if it's a leap year\n",
                "expected": "Leap year\n",
                "test_input": "2024",
                "hint_1": "Use the modulo operator % to check divisibility.",
                "hint_2": "Check: (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)",
                "solution": (
                    "year = int(input())\n"
                    "if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):\n"
                    "    print('Leap year')\n"
                    "else:\n"
                    "    print('Not a leap year')\n"
                ),
            },

            {   "slug": "even-odd-checker",
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "title": "Even / Odd Checker",
                "diff": "easy", "order": 2,
                "description": (
                    "<p>Read an integer from input. Print <code>even</code> if it is "
                    "even, or <code>odd</code> if it is odd.</p>"
                ),
                "starter": "n = int(input())\n# Print even or odd\n",
                "expected": "even\n",
                "test_input": "8",
                "hint_1": "Use the % (modulo) operator.",
                "hint_2": "n % 2 == 0 means even.",
                "solution": (
                    "n = int(input())\n"
                    "print('even' if n % 2 == 0 else 'odd')\n"
                ),
            },

            {   "slug": "fizzbuzz",
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "title": "FizzBuzz",
                "diff": "medium", "order": 3,
                "description": (
                    "<p>Print numbers 1 to 20. But:</p>"
                    "<ul>"
                    "<li>Print <code>Fizz</code> for multiples of 3</li>"
                    "<li>Print <code>Buzz</code> for multiples of 5</li>"
                    "<li>Print <code>FizzBuzz</code> for multiples of both</li>"
                    "</ul>"
                ),
                "starter": "for i in range(1, 21):\n    # Replace pass with your logic\n    pass\n",
                "expected": (
                    "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n"
                    "11\nFizz\n13\n14\nFizzBuzz\n16\n17\nFizz\n19\nBuzz\n"
                ),
                "test_input": "",
                "hint_1": "Check FizzBuzz first (divisible by both 3 and 5) before checking either alone.",
                "hint_2": "Use i % 3 == 0 and i % 5 == 0 for divisibility.",
                "solution": (
                    "for i in range(1, 21):\n"
                    "    if i % 15 == 0:\n"
                    "        print('FizzBuzz')\n"
                    "    elif i % 3 == 0:\n"
                    "        print('Fizz')\n"
                    "    elif i % 5 == 0:\n"
                    "        print('Buzz')\n"
                    "    else:\n"
                    "        print(i)\n"
                ),
            },

            {   "slug": "find-first-even",
                "topic_slug": "break-continue-pass", "domain_slug": "control-flow",
                "title": "Find First Even",
                "diff": "medium", "order": 4,
                "description": (
                    "<p>Read five space-separated integers from a single input line. "
                    "Print the first even number found. If none exist, print "
                    "<code>No even number</code>.</p>"
                    "<p>Example: <code>3 7 4 9 2</code> → <code>4</code></p>"
                ),
                "starter": (
                    "nums = list(map(int, input().split()))\n"
                    "# Find and print the first even number\n"
                ),
                "expected": "4\n",
                "test_input": "3 7 4 9 2",
                "hint_1": "Use a for loop and break when you find an even number.",
                "hint_2": "Use the for-else pattern: else runs only when no break occurred.",
                "solution": (
                    "nums = list(map(int, input().split()))\n"
                    "for n in nums:\n"
                    "    if n % 2 == 0:\n"
                    "        print(n)\n"
                    "        break\n"
                    "else:\n"
                    "    print('No even number')\n"
                ),
            },

            # ── Domain 3: Data Collections ─────────────────────────────

            {   "slug": "list-statistics",
                "topic_slug": "lists-methods", "domain_slug": "data-collections",
                "title": "List Statistics",
                "diff": "easy", "order": 1,
                "description": (
                    "<p>Read five space-separated integers from a single input line. "
                    "Print four lines:</p>"
                    "<ol>"
                    "<li>Min</li><li>Max</li><li>Sum</li>"
                    "<li>Average (as a float with 1 decimal place)</li>"
                    "</ol>"
                    "<p>Example: <code>3 1 4 1 5</code> → <code>1 / 5 / 14 / 2.8</code></p>"
                ),
                "starter": (
                    "nums = list(map(int, input().split()))\n"
                    "# Print min, max, sum, average\n"
                ),
                "expected": "1\n5\n14\n2.8\n",
                "test_input": "3 1 4 1 5",
                "hint_1": "Use the built-in functions min(), max(), sum().",
                "hint_2": "Average = sum(nums) / len(nums). Format with f'{avg:.1f}'.",
                "solution": (
                    "nums = list(map(int, input().split()))\n"
                    "print(min(nums))\n"
                    "print(max(nums))\n"
                    "print(sum(nums))\n"
                    "print(f'{sum(nums) / len(nums):.1f}')\n"
                ),
            },

            {   "slug": "dict-inventory",
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "title": "Dictionary Inventory Lookup",
                "diff": "easy", "order": 2,
                "description": (
                    "<p>A warehouse inventory is stored as a dictionary. "
                    "Read an item name from input. If it exists in the inventory, "
                    "print its quantity. If not, print <code>Not found</code>.</p>"
                    "<p>Inventory: <code>{'apple': 50, 'banana': 30, 'cherry': 10}</code></p>"
                ),
                "starter": (
                    "inventory = {'apple': 50, 'banana': 30, 'cherry': 10}\n"
                    "item = input()\n"
                    "# Look up item and print quantity or 'Not found'\n"
                ),
                "expected": "50\n",
                "test_input": "apple",
                "hint_1": "Use dict.get(key) — it returns None if the key is missing.",
                "hint_2": "Or check: if item in inventory: ...",
                "solution": (
                    "inventory = {'apple': 50, 'banana': 30, 'cherry': 10}\n"
                    "item = input()\n"
                    "result = inventory.get(item)\n"
                    "if result is None:\n"
                    "    print('Not found')\n"
                    "else:\n"
                    "    print(result)\n"
                ),
            },

            {   "slug": "string-cleaner",
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "title": "String Cleaner",
                "diff": "easy", "order": 3,
                "description": (
                    "<p>Read a string from input. Print it with:</p>"
                    "<ul>"
                    "<li>Leading and trailing whitespace removed</li>"
                    "<li>All letters converted to lowercase</li>"
                    "</ul>"
                    "<p>Example: <code>  Hello World  </code> → <code>hello world</code></p>"
                ),
                "starter": "raw = input()\n# Clean and print the string\n",
                "expected": "hello world\n",
                "test_input": "  Hello World  ",
                "hint_1": "str.strip() removes whitespace from both ends.",
                "hint_2": "str.lower() converts all letters to lowercase.",
                "solution": "raw = input()\nprint(raw.strip().lower())\n",
            },

            {   "slug": "word-frequency",
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "title": "Word Frequency Counter",
                "diff": "medium", "order": 4,
                "description": (
                    "<p>Read a sentence from input. Print each unique word and its "
                    "frequency, one per line in the format <code>word: count</code>, "
                    "in the order words first appear.</p>"
                    "<p>Example: <code>the cat sat on the mat</code></p>"
                    "<p>Output:</p><pre>the: 2\ncat: 1\nsat: 1\non: 1\nmat: 1</pre>"
                ),
                "starter": (
                    "sentence = input()\n"
                    "words = sentence.split()\n"
                    "# Count and print word frequencies\n"
                ),
                "expected": "the: 2\ncat: 1\nsat: 1\non: 1\nmat: 1\n",
                "test_input": "the cat sat on the mat",
                "hint_1": "Use a dict to count: freq[word] = freq.get(word, 0) + 1",
                "hint_2": "Iterate over freq.items() to print.",
                "solution": (
                    "sentence = input()\n"
                    "words = sentence.split()\n"
                    "freq = {}\n"
                    "for word in words:\n"
                    "    freq[word] = freq.get(word, 0) + 1\n"
                    "for word, count in freq.items():\n"
                    "    print(f'{word}: {count}')\n"
                ),
            },

            # ── Domain 4: Functions and Exceptions ─────────────────────

            {   "slug": "recursive-factorial",
                "topic_slug": "recursion", "domain_slug": "functions-exceptions",
                "title": "Factorial (Recursive)",
                "diff": "medium", "order": 1,
                "description": (
                    "<p>Write a recursive function <code>factorial(n)</code> that "
                    "returns n! (n factorial).</p>"
                    "<p>Read n from input and print the result.</p>"
                    "<p>Recall: 0! = 1, n! = n × (n-1)!</p>"
                ),
                "starter": (
                    "def factorial(n):\n"
                    "    # Base case\n"
                    "    # Recursive case\n"
                    "    pass\n\n"
                    "n = int(input())\n"
                    "print(factorial(n))\n"
                ),
                "expected": "120\n",
                "test_input": "5",
                "hint_1": "Base case: if n == 0 (or n == 1), return 1.",
                "hint_2": "Recursive case: return n * factorial(n - 1)",
                "solution": (
                    "def factorial(n):\n"
                    "    if n == 0:\n"
                    "        return 1\n"
                    "    return n * factorial(n - 1)\n\n"
                    "n = int(input())\n"
                    "print(factorial(n))\n"
                ),
            },

            {   "slug": "safe-division",
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "title": "Safe Division",
                "diff": "easy", "order": 2,
                "description": (
                    "<p>Read two integers from input (one per line). "
                    "Print the result of dividing the first by the second as a float "
                    "with 2 decimal places.</p>"
                    "<p>If the second number is 0, catch the exception and print "
                    "<code>Error: division by zero</code>.</p>"
                ),
                "starter": (
                    "a = int(input())\n"
                    "b = int(input())\n"
                    "# Divide safely with try/except\n"
                ),
                "expected": "3.33\n",
                "test_input": "10\n3",
                "hint_1": "Wrap the division in try/except ZeroDivisionError.",
                "hint_2": "print(f'{a / b:.2f}') for the result.",
                "solution": (
                    "a = int(input())\n"
                    "b = int(input())\n"
                    "try:\n"
                    "    print(f'{a / b:.2f}')\n"
                    "except ZeroDivisionError:\n"
                    "    print('Error: division by zero')\n"
                ),
            },

            {   "slug": "safe-index-lookup",
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "title": "Safe Index Lookup",
                "diff": "easy", "order": 3,
                "description": (
                    "<p>Given the list <code>[10, 20, 30, 40, 50]</code>, read an "
                    "index from input and print the element at that index.</p>"
                    "<p>If the index is out of range, print <code>Index out of range</code>.</p>"
                ),
                "starter": (
                    "items = [10, 20, 30, 40, 50]\n"
                    "index = int(input())\n"
                    "# Access safely with try/except\n"
                ),
                "expected": "30\n",
                "test_input": "2",
                "hint_1": "Wrap items[index] in try/except IndexError.",
                "hint_2": "The except block prints the error message.",
                "solution": (
                    "items = [10, 20, 30, 40, 50]\n"
                    "index = int(input())\n"
                    "try:\n"
                    "    print(items[index])\n"
                    "except IndexError:\n"
                    "    print('Index out of range')\n"
                ),
            },

            {   "slug": "default-params",
                "topic_slug": "parameters-arguments", "domain_slug": "functions-exceptions",
                "title": "Function with Default Parameters",
                "diff": "easy", "order": 4,
                "description": (
                    "<p>Write a function <code>describe(name, role='student', "
                    "score=0)</code> that prints:</p>"
                    "<pre>NAME is a ROLE with score SCORE</pre>"
                    "<p>Call it three ways:</p>"
                    "<ol>"
                    "<li><code>describe('Alice')</code></li>"
                    "<li><code>describe('Bob', 'instructor')</code></li>"
                    "<li><code>describe('Carol', score=95)</code></li>"
                    "</ol>"
                ),
                "starter": (
                    "def describe(name, role='student', score=0):\n"
                    "    pass  # Replace with the print statement\n\n"
                    "describe('Alice')\n"
                    "describe('Bob', 'instructor')\n"
                    "describe('Carol', score=95)\n"
                ),
                "expected": (
                    "Alice is a student with score 0\n"
                    "Bob is a instructor with score 0\n"
                    "Carol is a student with score 95\n"
                ),
                "test_input": "",
                "hint_1": "Use an f-string: f'{name} is a {role} with score {score}'",
                "hint_2": "Default parameters let you omit arguments when calling the function.",
                "solution": (
                    "def describe(name, role='student', score=0):\n"
                    "    print(f'{name} is a {role} with score {score}')\n\n"
                    "describe('Alice')\n"
                    "describe('Bob', 'instructor')\n"
                    "describe('Carol', score=95)\n"
                ),
            },
        ]

        for c in challenges:
            topic = Topic.objects.get(
                slug=c["topic_slug"], domain__slug=c["domain_slug"]
            )
            CodingChallenge.objects.update_or_create(
                slug=c["slug"],
                defaults={
                    "topic":           topic,
                    "title":           c["title"],
                    "description":     c["description"],
                    "starter_code":    c.get("starter", ""),
                    "expected_output": c["expected"],
                    "test_input":      c.get("test_input", ""),
                    "hint_1":          c.get("hint_1", ""),
                    "hint_2":          c.get("hint_2", ""),
                    "hint_3":          c.get("hint_3", ""),
                    "solution_code":   c.get("solution", ""),
                    "difficulty":      c.get("diff", "easy"),
                    "order":           c.get("order", 0),
                },
            )
