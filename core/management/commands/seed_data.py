"""
Management command to seed the database with comprehensive PCEP-30-02 content.

Creates 4 domains, 22 topics, 44+ flashcards, 65+ quiz questions,
and 15 coding challenges — enough to demonstrate the full system.

Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from learning.models import Domain, Topic, Lesson, Flashcard
from quizzes.models import Question, AnswerChoice
from labs.models import CodingChallenge

_WHAT_IS_OUTPUT = "What is the output?"


class Command(BaseCommand):
    help = "Seed database with PCEP-30-02 exam content"

    def handle(self, *args, **options):
        self.stdout.write("Seeding PCEP domains...")
        self._create_domains()
        self.stdout.write("Seeding topics...")
        self._create_topics()
        self.stdout.write("Seeding lessons...")
        self._create_lessons()
        self.stdout.write("Seeding flashcards...")
        self._create_flashcards()
        self.stdout.write("Seeding quiz questions...")
        self._create_questions()
        self.stdout.write("Seeding coding challenges...")
        self._create_coding_challenges()
        self.stdout.write(self.style.SUCCESS("✅ Seed data loaded successfully!"))

    # ── Domains ───────────────────────────────────────────────────────
    def _create_domains(self):
        domains = [
            {
                "title": "Computer Programming and Python Fundamentals",
                "slug": "fundamentals",
                "order": 1,
                "weight_percent": 18,
                "description": "Core concepts: how computers run programs, Python basics, data types, variables, operators, and I/O.",
                "icon": "bi-cpu",
            },
            {
                "title": "Control Flow: Conditional Blocks and Loops",
                "slug": "control-flow",
                "order": 2,
                "weight_percent": 29,
                "description": "Decision-making with if/elif/else, iteration with while and for, and flow control with break, continue, and pass.",
                "icon": "bi-arrow-repeat",
            },
            {
                "title": "Data Collections: Tuples, Dictionaries, Lists, and Strings",
                "slug": "data-collections",
                "order": 3,
                "weight_percent": 25,
                "description": "Working with Python's built-in data structures: lists, tuples, dictionaries, and strings.",
                "icon": "bi-collection",
            },
            {
                "title": "Functions and Exceptions",
                "slug": "functions-exceptions",
                "order": 4,
                "weight_percent": 28,
                "description": "Defining functions, parameter passing, scope, recursion, and handling errors with try/except.",
                "icon": "bi-gear",
            },
        ]
        for d in domains:
            Domain.objects.update_or_create(slug=d["slug"], defaults=d)

    # ── Topics ────────────────────────────────────────────────────────
    def _create_topics(self):
        topics_data = {
            "fundamentals": [
                ("Interpreter vs Compiler", "interpreter-vs-compiler", "easy", "1.1.1"),
                ("Lexis, Syntax, and Semantics", "lexis-syntax-semantics", "easy", "1.1.2"),
                ("Keywords, Indentation, Comments", "keywords-indentation-comments", "easy", "1.1.3"),
                ("Literals and Variables", "literals-variables", "easy", "1.2.1"),
                ("Naming Conventions and PEP 8", "naming-conventions-pep8", "easy", "1.2.2"),
                ("Numeric and String Operators", "numeric-string-operators", "medium", "1.3.1"),
                ("Boolean, Relational, and Bitwise Operators", "boolean-relational-bitwise", "medium", "1.3.2"),
                ("Type Casting", "type-casting", "easy", "1.4.1"),
                ("print() and input()", "print-input", "easy", "1.4.2"),
            ],
            "control-flow": [
                ("if / if-else / if-elif-else", "conditionals", "easy", "2.1.1"),
                ("while Loops", "while-loops", "medium", "2.2.1"),
                ("for Loops and range()", "for-loops-range", "medium", "2.2.2"),
                ("break, continue, pass", "break-continue-pass", "medium", "2.2.3"),
                ("Nested Loops and Logic", "nested-loops", "hard", "2.3.1"),
            ],
            "data-collections": [
                ("Lists and List Methods", "lists-methods", "medium", "3.1.1"),
                ("List Slicing and Comprehensions", "list-slicing-comprehensions", "medium", "3.1.2"),
                ("Nested Lists", "nested-lists", "hard", "3.1.3"),
                ("Tuples and Immutability", "tuples-immutability", "easy", "3.2.1"),
                ("Dictionaries", "dictionaries", "medium", "3.3.1"),
                ("Strings, Escaping, and String Methods", "strings-methods", "medium", "3.4.1"),
            ],
            "functions-exceptions": [
                ("Defining Functions and return", "functions-return", "medium", "4.1.1"),
                ("Parameters, Arguments, Defaults", "parameters-arguments", "medium", "4.1.2"),
                ("Scope, Shadowing, and global", "scope-global", "hard", "4.2.1"),
                ("Recursion", "recursion", "hard", "4.2.2"),
                ("Exceptions and try/except", "exceptions-try-except", "medium", "4.3.1"),
            ],
        }
        for domain_slug, topics in topics_data.items():
            domain = Domain.objects.get(slug=domain_slug)
            for i, (name, slug, diff, obj) in enumerate(topics):
                Topic.objects.update_or_create(
                    domain=domain, slug=slug,
                    defaults={
                        "name": name,
                        "order": i + 1,
                        "difficulty": diff,
                        "pcep_objective": obj,
                        "description": f"Learn about {name.lower()} in Python.",
                    },
                )

    # ── Lessons ───────────────────────────────────────────────────────
    def _create_lessons(self):
        lessons = [
            ("interpreter-vs-compiler", "fundamentals", "How Python Runs Your Code", """
<h3>Interpreter vs Compiler</h3>
<p>A <strong>compiler</strong> translates the entire source code into machine code before execution. Languages like C and C++ use compilers.</p>
<p>An <strong>interpreter</strong> reads and executes code <em>line by line</em>. Python uses an interpreter — specifically CPython, which compiles to bytecode internally, then interprets it.</p>
<h4>Key differences</h4>
<table class="table table-bordered">
<tr><th></th><th>Compiler</th><th>Interpreter</th></tr>
<tr><td>Translation</td><td>All at once</td><td>Line by line</td></tr>
<tr><td>Speed</td><td>Faster execution</td><td>Slower execution</td></tr>
<tr><td>Errors</td><td>Shown after compilation</td><td>Shown immediately at the failing line</td></tr>
</table>
<h4>Example</h4>
<pre><code># Python is interpreted — try this:
print("Hello, PCEP!")  # Executes immediately
print(1 / 0)           # Error appears here, line 2
</code></pre>
"""),
            ("lexis-syntax-semantics", "fundamentals", "Lexis, Syntax, and Semantics", """
<h3>The Three Layers of a Programming Language</h3>
<p><strong>Lexis</strong> (vocabulary): The set of valid words/tokens. In Python: keywords like <code>if</code>, <code>for</code>, <code>def</code>, operators like <code>+</code>, <code>=</code>.</p>
<p><strong>Syntax</strong> (grammar): The rules for combining tokens. <code>if x > 0:</code> is valid syntax; <code>if > x 0:</code> is not.</p>
<p><strong>Semantics</strong> (meaning): What the code actually <em>does</em>. <code>x = 1 + 2</code> means "compute 3 and store it in x".</p>
<h4>Common exam question</h4>
<pre><code># Which layer catches this error?
print("Hello"  # Missing closing parenthesis → Syntax error
</code></pre>
"""),
            ("keywords-indentation-comments", "fundamentals", "Keywords, Indentation, and Comments", """
<h3>Python Fundamentals</h3>
<h4>Keywords</h4>
<p>Reserved words that have special meaning: <code>if</code>, <code>else</code>, <code>for</code>, <code>while</code>, <code>def</code>, <code>return</code>, <code>True</code>, <code>False</code>, <code>None</code>, <code>and</code>, <code>or</code>, <code>not</code>, <code>in</code>, <code>is</code>, <code>class</code>, <code>try</code>, <code>except</code>, <code>import</code>, <code>from</code>, <code>global</code>, <code>pass</code>, <code>break</code>, <code>continue</code>.</p>
<h4>Indentation</h4>
<p>Python uses indentation (spaces/tabs) to define code blocks — not braces <code>{}</code>.</p>
<pre><code>if True:
    print("indented = inside the if block")
print("not indented = outside")</code></pre>
<h4>Comments</h4>
<pre><code># This is a single-line comment
x = 42  # Inline comment</code></pre>
"""),
            ("literals-variables", "fundamentals", "Literals and Variables", """
<h3>Literals</h3>
<p>Fixed values written directly in code:</p>
<pre><code>42          # int literal
3.14        # float literal
"hello"     # string literal
True        # boolean literal
None        # NoneType literal
0o17        # octal (15 in decimal)
0xFF        # hex (255 in decimal)
</code></pre>
<h3>Variables</h3>
<p>Names that refer to values. Created by assignment:</p>
<pre><code>name = "Alice"
age = 25
pi = 3.14159</code></pre>
<p>Variables don't need type declarations — Python figures out the type automatically (dynamic typing).</p>
"""),
            ("conditionals", "control-flow", "Conditional Statements in Python", """
<h3>if / if-else / if-elif-else</h3>
<p>Conditional statements let your program make decisions.</p>
<pre><code># Simple if
x = 10
if x > 0:
    print("positive")

# if-else
if x % 2 == 0:
    print("even")
else:
    print("odd")

# if-elif-else
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"
print(grade)  # B
</code></pre>
<h4>Key points</h4>
<ul>
<li>Conditions evaluate to <code>True</code> or <code>False</code></li>
<li>Only the first matching branch executes</li>
<li>The <code>else</code> block is optional</li>
<li>Indentation defines the block</li>
</ul>
"""),
            ("while-loops", "control-flow", "while Loops", """
<h3>while Loops</h3>
<p>Repeat a block as long as a condition is True.</p>
<pre><code>count = 0
while count < 5:
    print(count)
    count += 1
# Output: 0 1 2 3 4</code></pre>
<h4>while-else</h4>
<p>The <code>else</code> block runs if the loop finishes normally (no <code>break</code>).</p>
<pre><code>n = 5
while n > 0:
    n -= 1
else:
    print("Loop finished!")  # This runs
</code></pre>
<h4>Infinite loops</h4>
<pre><code># Be careful!
while True:
    response = input("Type 'quit': ")
    if response == "quit":
        break  # Exits the loop
</code></pre>
"""),
            ("for-loops-range", "control-flow", "for Loops and range()", """
<h3>for Loops</h3>
<p>Iterate over sequences (lists, strings, ranges).</p>
<pre><code>for fruit in ["apple", "banana", "cherry"]:
    print(fruit)

for char in "Python":
    print(char)
</code></pre>
<h3>range() function</h3>
<pre><code>range(5)        # 0, 1, 2, 3, 4
range(2, 6)     # 2, 3, 4, 5
range(0, 10, 2) # 0, 2, 4, 6, 8
range(5, 0, -1) # 5, 4, 3, 2, 1</code></pre>
<h4>for-else</h4>
<pre><code>for i in range(5):
    if i == 10:
        break
else:
    print("No break occurred")  # This runs
</code></pre>
"""),
            ("lists-methods", "data-collections", "Lists and List Methods", """
<h3>Python Lists</h3>
<p>Ordered, mutable collections.</p>
<pre><code>fruits = ["apple", "banana", "cherry"]
print(fruits[0])   # apple
print(fruits[-1])  # cherry
fruits[1] = "blueberry"  # mutable!
</code></pre>
<h3>Common methods</h3>
<pre><code>nums = [3, 1, 4, 1, 5]
nums.append(9)      # [3, 1, 4, 1, 5, 9]
nums.insert(0, 0)   # [0, 3, 1, 4, 1, 5, 9]
nums.remove(1)      # removes first 1
nums.pop()          # removes and returns last
nums.sort()         # sorts in place
nums.reverse()      # reverses in place
len(nums)           # length
</code></pre>
"""),
            ("tuples-immutability", "data-collections", "Tuples and Immutability", """
<h3>Tuples</h3>
<p>Ordered, <strong>immutable</strong> sequences. Once created, you cannot change them.</p>
<pre><code>point = (3, 4)
colors = ("red", "green", "blue")
single = (42,)  # Note the comma for single-element tuple

print(point[0])    # 3
print(len(colors)) # 3
</code></pre>
<h4>Why use tuples?</h4>
<ul>
<li>Faster than lists</li>
<li>Can be dictionary keys (lists cannot)</li>
<li>Signal that data shouldn't change</li>
</ul>
<pre><code># This raises TypeError:
point[0] = 10  # TypeError: 'tuple' object does not support item assignment</code></pre>
"""),
            ("dictionaries", "data-collections", "Dictionaries", """
<h3>Python Dictionaries</h3>
<p>Key-value pairs. Keys must be immutable (strings, numbers, tuples).</p>
<pre><code>student = {"name": "Alice", "age": 20, "grade": "A"}
print(student["name"])      # Alice
student["age"] = 21         # update
student["email"] = "a@b.c"  # add new key
del student["grade"]        # delete
</code></pre>
<h3>Useful methods</h3>
<pre><code>student.keys()    # dict_keys(['name', 'age', 'email'])
student.values()  # dict_values(['Alice', 21, 'a@b.c'])
student.items()   # dict_items([('name','Alice'), ...])
student.get("gpa", 0.0)  # returns 0.0 if key missing
</code></pre>
"""),
            ("functions-return", "functions-exceptions", "Defining Functions and return", """
<h3>Functions</h3>
<p>Reusable blocks of code defined with <code>def</code>.</p>
<pre><code>def greet(name):
    return f"Hello, {name}!"

message = greet("Alice")
print(message)  # Hello, Alice!
</code></pre>
<h4>return statement</h4>
<ul>
<li><code>return</code> sends a value back to the caller</li>
<li>A function without <code>return</code> returns <code>None</code></li>
<li>Code after <code>return</code> doesn't execute</li>
</ul>
<pre><code>def add(a, b):
    return a + b

def say_hi():
    print("Hi!")
    # implicitly returns None

result = say_hi()
print(result)  # None
</code></pre>
"""),
            ("parameters-arguments", "functions-exceptions", "Parameters, Arguments, and Defaults", """
<h3>Parameters vs Arguments</h3>
<p><strong>Parameters</strong> are in the function definition. <strong>Arguments</strong> are the values you pass when calling.</p>
<pre><code>def power(base, exponent=2):  # base, exponent are parameters
    return base ** exponent

power(3)       # 9  — exponent defaults to 2
power(3, 3)    # 27 — positional argument
power(base=2, exponent=10)  # keyword arguments
</code></pre>
<h4>Key rules</h4>
<ul>
<li>Default parameters must come after non-default ones</li>
<li>Positional arguments must come before keyword arguments</li>
</ul>
"""),
            ("scope-global", "functions-exceptions", "Scope, Shadowing, and global", """
<h3>Variable Scope</h3>
<p>Variables have scope — where they're accessible.</p>
<pre><code>x = "global"

def my_func():
    x = "local"  # This shadows the global x
    print(x)     # local

my_func()
print(x)  # global — unchanged
</code></pre>
<h4>The global keyword</h4>
<pre><code>counter = 0

def increment():
    global counter
    counter += 1

increment()
increment()
print(counter)  # 2
</code></pre>
"""),
            ("exceptions-try-except", "functions-exceptions", "Exceptions and try/except", """
<h3>Exception Handling</h3>
<p>Errors that occur during execution can be caught and handled.</p>
<pre><code>try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")
</code></pre>
<h4>Multiple except blocks</h4>
<pre><code>try:
    nums = [1, 2, 3]
    print(nums[10])
except IndexError:
    print("Index out of range!")
except TypeError:
    print("Type error!")
except Exception as e:
    print(f"Unexpected error: {e}")
</code></pre>
<h4>Common PCEP exceptions</h4>
<ul>
<li><code>ZeroDivisionError</code> — dividing by zero</li>
<li><code>IndexError</code> — list/tuple index out of range</li>
<li><code>KeyError</code> — dictionary key not found</li>
<li><code>TypeError</code> — wrong type operation</li>
<li><code>ValueError</code> — right type, wrong value</li>
</ul>
"""),
        ]
        for topic_slug, domain_slug, title, content in lessons:
            topic = Topic.objects.get(slug=topic_slug, domain__slug=domain_slug)
            Lesson.objects.update_or_create(
                topic=topic, slug=title.lower().replace(" ", "-")[:48],
                defaults={"title": title, "content": content, "order": 1},
            )

    # ── Flashcards ────────────────────────────────────────────────────
    def _create_flashcards(self):
        cards = [
            # Domain 1: Fundamentals
            ("interpreter-vs-compiler", "fundamentals", "What is the difference between a compiler and an interpreter?", "A compiler translates the entire program at once; an interpreter executes code line by line."),
            ("interpreter-vs-compiler", "fundamentals", "Is Python compiled or interpreted?", "Python is interpreted (CPython compiles to bytecode internally, then interprets it)."),
            ("lexis-syntax-semantics", "fundamentals", "What is 'lexis' in programming?", "The vocabulary/set of valid tokens (keywords, operators, identifiers)."),
            ("lexis-syntax-semantics", "fundamentals", "What is a syntax error?", "A violation of the grammar rules — the code structure is invalid."),
            ("lexis-syntax-semantics", "fundamentals", "What is semantics?", "The meaning of syntactically correct code — what it actually does."),
            ("keywords-indentation-comments", "fundamentals", "How do you write a comment in Python?", "Use the # symbol. Everything after # on that line is ignored."),
            ("keywords-indentation-comments", "fundamentals", "Why is indentation important in Python?", "Python uses indentation to define code blocks (instead of braces {})."),
            ("literals-variables", "fundamentals", "What is a literal?", "A fixed value written directly in source code, like 42, 3.14 or 'hello'."),
            ("literals-variables", "fundamentals", "What is 0xFF in Python?", "A hexadecimal literal equal to 255 in decimal."),
            ("naming-conventions-pep8", "fundamentals", "What does PEP 8 recommend for variable names?", "Use snake_case: lowercase words separated by underscores."),
            ("numeric-string-operators", "fundamentals", "What does the ** operator do?", "Exponentiation. 2 ** 3 = 8"),
            ("numeric-string-operators", "fundamentals", "What does the // operator do?", "Floor (integer) division. 7 // 2 = 3"),
            ("numeric-string-operators", "fundamentals", "What does % do?", "Modulo — returns the remainder. 7 % 3 = 1"),
            ("boolean-relational-bitwise", "fundamentals", "What is the result of not True?", "False"),
            ("type-casting", "fundamentals", "How do you convert a string '42' to an integer?", "int('42') returns 42"),
            ("print-input", "fundamentals", "What does sep do in print()?", "It sets the separator between arguments. print(1, 2, sep='-') outputs '1-2'."),
            ("print-input", "fundamentals", "What does input() always return?", "A string. You must cast it to int/float if you need a number."),

            # Domain 2: Control Flow
            ("conditionals", "control-flow", "What happens if no condition is True and there's no else?", "Nothing — the program skips the entire if block."),
            ("conditionals", "control-flow", "Can you have elif without else?", "Yes. else is optional."),
            ("while-loops", "control-flow", "When does a while loop's else block execute?", "When the condition becomes False normally (not via break)."),
            ("for-loops-range", "control-flow", "What does range(2, 10, 3) produce?", "2, 5, 8"),
            ("for-loops-range", "control-flow", "What does range(5, 0, -1) produce?", "5, 4, 3, 2, 1"),
            ("break-continue-pass", "control-flow", "What does break do?", "Immediately exits the nearest enclosing loop."),
            ("break-continue-pass", "control-flow", "What does continue do?", "Skips the rest of the current iteration and goes to the next."),
            ("break-continue-pass", "control-flow", "What does pass do?", "Does nothing — it's a placeholder for empty blocks."),
            ("nested-loops", "control-flow", "If you have a for loop inside a for loop, how many times does the inner loop run?", "outer_iterations × inner_iterations times total."),

            # Domain 3: Data Collections
            ("lists-methods", "data-collections", "Are lists mutable or immutable?", "Mutable — you can change their elements."),
            ("lists-methods", "data-collections", "What does .append() do?", "Adds an element to the end of the list."),
            ("lists-methods", "data-collections", "What does .pop() do?", "Removes and returns the last item (or the item at a given index)."),
            ("list-slicing-comprehensions", "data-collections", "What does my_list[1:4] return?", "Elements at indices 1, 2, 3 (not including 4)."),
            ("list-slicing-comprehensions", "data-collections", "What is a list comprehension?", "[expr for item in iterable if condition] — a compact way to build lists."),
            ("tuples-immutability", "data-collections", "Can you change an element of a tuple?", "No — tuples are immutable. You'll get a TypeError."),
            ("tuples-immutability", "data-collections", "How do you create a single-element tuple?", "Add a trailing comma: (42,) — not (42)."),
            ("dictionaries", "data-collections", "What does .get(key, default) do?", "Returns the value for key if it exists, otherwise returns default."),
            ("dictionaries", "data-collections", "Can a list be a dictionary key?", "No — dictionary keys must be immutable (strings, numbers, tuples)."),
            ("strings-methods", "data-collections", "Are Python strings mutable?", "No — strings are immutable."),
            ("strings-methods", "data-collections", "What does .split() do?", "Splits a string into a list of substrings using whitespace (or a given delimiter)."),

            # Domain 4: Functions & Exceptions
            ("functions-return", "functions-exceptions", "What does a function return if there is no return statement?", "None"),
            ("functions-return", "functions-exceptions", "Can a function return multiple values?", "Yes — return a, b returns a tuple (a, b)."),
            ("parameters-arguments", "functions-exceptions", "What is a default parameter?", "A parameter with a default value: def f(x=10). If no argument is passed, x is 10."),
            ("parameters-arguments", "functions-exceptions", "What is the difference between a parameter and an argument?", "A parameter is in the function definition; an argument is the value passed when calling."),
            ("scope-global", "functions-exceptions", "What does the global keyword do?", "Allows a function to modify a variable from the global scope."),
            ("scope-global", "functions-exceptions", "What is variable shadowing?", "When a local variable has the same name as a global one, the local hides the global."),
            ("recursion", "functions-exceptions", "What is recursion?", "A function that calls itself. Must have a base case to stop."),
            ("exceptions-try-except", "functions-exceptions", "Name 5 common Python exceptions.", "ZeroDivisionError, IndexError, KeyError, TypeError, ValueError."),
            ("exceptions-try-except", "functions-exceptions", "What happens if an exception is not caught?", "The program crashes and shows a traceback."),
        ]
        for topic_slug, domain_slug, front, back in cards:
            topic = Topic.objects.get(slug=topic_slug, domain__slug=domain_slug)
            Flashcard.objects.update_or_create(
                topic=topic, front=front,
                defaults={"back": back, "order": 0},
            )

    # ── Quiz Questions ────────────────────────────────────────────────
    def _create_questions(self):
        questions = self._get_all_questions()
        for q_data in questions:
            topic = Topic.objects.get(
                slug=q_data["topic_slug"],
                domain__slug=q_data["domain_slug"],
            )
            q, _ = Question.objects.update_or_create(
                topic=topic,
                text=q_data["text"],
                code_snippet=q_data.get("code", ""),
                defaults={
                    "question_type": q_data["qtype"],
                    "explanation": q_data.get("explanation", ""),
                    "hint": q_data.get("hint", ""),
                    "difficulty": q_data.get("difficulty", "medium"),
                },
            )
            # Create choices
            q.choices.all().delete()
            for i, (text, correct) in enumerate(q_data["choices"]):
                AnswerChoice.objects.create(
                    question=q, text=text, is_correct=correct, order=i,
                )

    def _get_all_questions(self):
        """Return all 65+ quiz questions as a list of dicts."""
        return [
            # ── DOMAIN 1: Fundamentals (12 questions) ────────────────
            {
                "topic_slug": "interpreter-vs-compiler", "domain_slug": "fundamentals",
                "qtype": "mc", "difficulty": "easy",
                "text": "Which statement best describes an interpreter?",
                "explanation": "An interpreter executes code line by line, reporting errors as it encounters them.",
                "choices": [
                    ("Translates the entire program before running it", False),
                    ("Executes code line by line", True),
                    ("Only works with compiled languages", False),
                    ("Converts code to HTML", False),
                ],
            },
            {
                "topic_slug": "interpreter-vs-compiler", "domain_slug": "fundamentals",
                "qtype": "tf", "difficulty": "easy",
                "text": "Python is primarily an interpreted language.",
                "explanation": "CPython interprets Python bytecode.",
                "choices": [("True", True), ("False", False)],
            },
            {
                "topic_slug": "lexis-syntax-semantics", "domain_slug": "fundamentals",
                "qtype": "mc", "difficulty": "easy",
                "text": "A missing colon after an if statement is an example of what type of error?",
                "explanation": "Missing a colon violates Python's grammar rules — that's a syntax error.",
                "choices": [
                    ("Runtime error", False),
                    ("Semantic error", False),
                    ("Syntax error", True),
                    ("Logical error", False),
                ],
            },
            {
                "topic_slug": "keywords-indentation-comments", "domain_slug": "fundamentals",
                "qtype": "mc", "difficulty": "easy",
                "text": "Which of these is NOT a Python keyword?",
                "choices": [
                    ("for", False),
                    ("while", False),
                    ("function", True),
                    ("class", False),
                ],
                "explanation": "Python uses 'def' to define functions, not 'function'.",
            },
            {
                "topic_slug": "literals-variables", "domain_slug": "fundamentals",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 0o11\nprint(x)",
                "explanation": "0o11 is octal for 9 (1×8 + 1×1).",
                "choices": [("9", True)],
            },
            {
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": 'print(2 ** 3 ** 2)',
                "explanation": "** is right-associative: 3**2=9, then 2**9=512.",
                "choices": [("512", True)],
            },
            {
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "qtype": "mc", "difficulty": "medium",
                "text": "What does 17 // 3 evaluate to?",
                "choices": [("5", True), ("5.67", False), ("6", False), ("5.0", False)],
                "explanation": "// is floor division: 17/3 = 5.67, floor = 5.",
            },
            {
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "print('Ha' * 3)",
                "explanation": "String repetition: 'Ha' * 3 = 'HaHaHa'.",
                "choices": [("HaHaHa", True)],
            },
            {
                "topic_slug": "boolean-relational-bitwise", "domain_slug": "fundamentals",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "print(True + True + False)",
                "explanation": "True=1, False=0. 1+1+0=2.",
                "choices": [("2", True)],
            },
            {
                "topic_slug": "type-casting", "domain_slug": "fundamentals",
                "qtype": "mc", "difficulty": "easy",
                "text": "What does int('3.14') produce?",
                "choices": [
                    ("3", False),
                    ("3.14", False),
                    ("ValueError", True),
                    ("0", False),
                ],
                "explanation": "int() cannot directly convert a string with a decimal point. Use int(float('3.14')).",
            },
            {
                "topic_slug": "print-input", "domain_slug": "fundamentals",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "print(1, 2, 3, sep='-', end='!')",
                "explanation": "sep='-' puts dashes between args; end='!' replaces newline.",
                "choices": [("1-2-3!", True)],
            },
            {
                "topic_slug": "print-input", "domain_slug": "fundamentals",
                "qtype": "tf", "difficulty": "easy",
                "text": "The input() function always returns a string.",
                "choices": [("True", True), ("False", False)],
            },

            # ── DOMAIN 2: Control Flow (18 questions) ────────────────
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 15\nif x > 20:\n    print('A')\nelif x > 10:\n    print('B')\nelse:\n    print('C')",
                "choices": [("B", True)],
            },
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 5\nif x > 3:\n    if x > 10:\n        print('big')\n    else:\n        print('medium')\nelse:\n    print('small')",
                "choices": [("medium", True)],
            },
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "qtype": "mc", "difficulty": "easy",
                "text": "In an if-elif-else chain, how many blocks can execute?",
                "choices": [("All of them", False), ("Exactly one", True), ("At least one", False), ("Zero or more", False)],
                "explanation": "Only the first matching branch executes.",
            },
            {
                "topic_slug": "while-loops", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "i = 0\nwhile i < 3:\n    print(i, end=' ')\n    i += 1",
                "choices": [("0 1 2 ", True)],
            },
            {
                "topic_slug": "while-loops", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "i = 5\nwhile i > 0:\n    i -= 2\nelse:\n    print(i)",
                "choices": [("-1", True)],
                "explanation": "Loop: 5→3→1→-1 (condition False). else runs, prints -1.",
            },
            {
                "topic_slug": "while-loops", "domain_slug": "control-flow",
                "qtype": "tf", "difficulty": "medium",
                "text": "The else block of a while loop runs even if the loop was exited with break.",
                "choices": [("True", False), ("False", True)],
                "explanation": "The else block does NOT run if break was used.",
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(3):\n    print(i, end=' ')",
                "choices": [("0 1 2 ", True)],
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "qtype": "mc", "difficulty": "medium",
                "text": "What does list(range(10, 0, -3)) produce?",
                "choices": [
                    ("[10, 7, 4, 1]", True),
                    ("[10, 7, 4]", False),
                    ("[10, 7, 4, 1, 0]", False),
                    ("[10, 8, 6, 4, 2]", False),
                ],
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "total = 0\nfor i in range(1, 6):\n    total += i\nprint(total)",
                "choices": [("15", True)],
            },
            {
                "topic_slug": "break-continue-pass", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(5):\n    if i == 3:\n        break\n    print(i, end=' ')",
                "choices": [("0 1 2 ", True)],
            },
            {
                "topic_slug": "break-continue-pass", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(5):\n    if i == 2:\n        continue\n    print(i, end=' ')",
                "choices": [("0 1 3 4 ", True)],
            },
            {
                "topic_slug": "break-continue-pass", "domain_slug": "control-flow",
                "qtype": "mc", "difficulty": "easy",
                "text": "What does the 'pass' statement do?",
                "choices": [
                    ("Exits the loop", False),
                    ("Skips the current iteration", False),
                    ("Does nothing — it's a placeholder", True),
                    ("Raises an error", False),
                ],
            },
            {
                "topic_slug": "nested-loops", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(3):\n    for j in range(2):\n        print(i * j, end=' ')",
                "choices": [("0 0 0 1 0 2 ", True)],
                "explanation": "i=0: 0*0=0, 0*1=0. i=1: 1*0=0, 1*1=1. i=2: 2*0=0, 2*1=2.",
            },
            {
                "topic_slug": "nested-loops", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": "How many times does 'X' print?",
                "code": "for i in range(4):\n    for j in range(3):\n        print('X', end='')",
                "explanation": "4 × 3 = 12 times.",
                "choices": [("12", True)],
                "hint": "Multiply the outer iterations by the inner iterations.",
            },
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 0\nif x:\n    print('yes')\nelse:\n    print('no')",
                "choices": [("no", True)],
                "explanation": "0 is falsy in Python.",
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(5):\n    pass\nprint(i)",
                "choices": [("4", True)],
                "explanation": "The loop variable persists after the loop ends.",
            },
            {
                "topic_slug": "while-loops", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "n = 1\nwhile n < 100:\n    n *= 2\nprint(n)",
                "choices": [("128", True)],
            },
            {
                "topic_slug": "break-continue-pass", "domain_slug": "control-flow",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "for i in range(5):\n    if i % 2 == 0:\n        continue\n    if i > 3:\n        break\n    print(i, end=' ')",
                "choices": [("1 3 ", True)],
            },

            # ── DOMAIN 3: Data Collections (18 questions) ────────────
            {
                "topic_slug": "lists-methods", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "a = [1, 2, 3]\na.append(4)\nprint(len(a))",
                "choices": [("4", True)],
            },
            {
                "topic_slug": "lists-methods", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "a = [3, 1, 4, 1, 5]\na.sort()\nprint(a)",
                "choices": [("[1, 1, 3, 4, 5]", True)],
            },
            {
                "topic_slug": "lists-methods", "domain_slug": "data-collections",
                "qtype": "mc", "difficulty": "medium",
                "text": "What does [1, 2, 3].insert(1, 'a') produce?",
                "choices": [
                    ("[1, 'a', 2, 3]", True),
                    ("['a', 1, 2, 3]", False),
                    ("[1, 2, 'a', 3]", False),
                    ("Error", False),
                ],
            },
            {
                "topic_slug": "list-slicing-comprehensions", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "a = [0, 1, 2, 3, 4, 5]\nprint(a[1:4])",
                "choices": [("[1, 2, 3]", True)],
            },
            {
                "topic_slug": "list-slicing-comprehensions", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "a = [0, 1, 2, 3, 4, 5]\nprint(a[::2])",
                "choices": [("[0, 2, 4]", True)],
            },
            {
                "topic_slug": "list-slicing-comprehensions", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "print([x ** 2 for x in range(5)])",
                "choices": [("[0, 1, 4, 9, 16]", True)],
            },
            {
                "topic_slug": "list-slicing-comprehensions", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "a = [1, 2, 3, 4, 5]\nprint(a[::-1])",
                "choices": [("[5, 4, 3, 2, 1]", True)],
            },
            {
                "topic_slug": "nested-lists", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "m = [[1, 2], [3, 4], [5, 6]]\nprint(m[1][0])",
                "choices": [("3", True)],
            },
            {
                "topic_slug": "tuples-immutability", "domain_slug": "data-collections",
                "qtype": "mc", "difficulty": "easy",
                "text": "What happens when you try t[0] = 10 on a tuple t = (1, 2, 3)?",
                "choices": [
                    ("It changes the first element to 10", False),
                    ("TypeError: 'tuple' object does not support item assignment", True),
                    ("It creates a new tuple", False),
                    ("IndexError", False),
                ],
            },
            {
                "topic_slug": "tuples-immutability", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "t = (1,)\nprint(type(t).__name__)",
                "choices": [("tuple", True)],
            },
            {
                "topic_slug": "tuples-immutability", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "t = (1)\nprint(type(t).__name__)",
                "choices": [("int", True)],
                "explanation": "(1) is just grouping parentheses, not a tuple. Use (1,) for a single-element tuple.",
            },
            {
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "d = {'a': 1, 'b': 2}\nprint(d['b'])",
                "choices": [("2", True)],
            },
            {
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "qtype": "mc", "difficulty": "medium",
                "text": "What does d.get('z', 0) return if 'z' is not in dictionary d?",
                "choices": [("0", True), ("None", False), ("KeyError", False), ("''", False)],
            },
            {
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "d = {'x': 1, 'y': 2, 'z': 3}\nprint(len(d))",
                "choices": [("3", True)],
            },
            {
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "print('hello'.upper())",
                "choices": [("HELLO", True)],
            },
            {
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "print('hello world'.split())",
                "choices": [("['hello', 'world']", True)],
            },
            {
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "s = 'Python'\nprint(s[1:4])",
                "choices": [("yth", True)],
            },
            {
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "qtype": "tf", "difficulty": "easy",
                "text": "Strings in Python are immutable.",
                "choices": [("True", True), ("False", False)],
            },

            # ── DOMAIN 4: Functions & Exceptions (17 questions) ──────
            {
                "topic_slug": "functions-return", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "easy",
                "text": _WHAT_IS_OUTPUT,
                "code": "def greet():\n    return 'Hi'\n\nprint(greet())",
                "choices": [("Hi", True)],
            },
            {
                "topic_slug": "functions-return", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "def foo():\n    print('A')\n\nresult = foo()\nprint(result)",
                "choices": [("A\nNone", True)],
                "explanation": "foo() prints 'A' and implicitly returns None.",
            },
            {
                "topic_slug": "functions-return", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "def f(x):\n    return x * 2\n    return x * 3\n\nprint(f(5))",
                "choices": [("10", True)],
                "explanation": "Only the first return executes. Code after return is unreachable.",
            },
            {
                "topic_slug": "parameters-arguments", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "def power(base, exp=2):\n    return base ** exp\n\nprint(power(3))\nprint(power(2, 10))",
                "choices": [("9\n1024", True)],
            },
            {
                "topic_slug": "parameters-arguments", "domain_slug": "functions-exceptions",
                "qtype": "mc", "difficulty": "medium",
                "text": "Which function definition is valid?",
                "choices": [
                    ("def f(a=1, b): pass", False),
                    ("def f(a, b=1): pass", True),
                    ("def f(a=1, b=2, c): pass", False),
                    ("def f(,a): pass", False),
                ],
                "explanation": "Default parameters must come after non-default ones.",
            },
            {
                "topic_slug": "parameters-arguments", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "def f(a, b, c):\n    print(a, b, c)\n\nf(c=3, a=1, b=2)",
                "choices": [("1 2 3", True)],
            },
            {
                "topic_slug": "scope-global", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 10\ndef f():\n    x = 20\n    print(x)\nf()\nprint(x)",
                "choices": [("20\n10", True)],
                "explanation": "The local x=20 shadows the global x=10. Global x is unchanged.",
            },
            {
                "topic_slug": "scope-global", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "x = 1\ndef f():\n    global x\n    x = 2\nf()\nprint(x)",
                "choices": [("2", True)],
            },
            {
                "topic_slug": "scope-global", "domain_slug": "functions-exceptions",
                "qtype": "mc", "difficulty": "hard",
                "text": "What happens if you try to read a global variable inside a function without the global keyword?",
                "choices": [
                    ("It works fine — you can read globals", True),
                    ("UnboundLocalError", False),
                    ("NameError", False),
                    ("SyntaxError", False),
                ],
                "explanation": "You only need 'global' to MODIFY a global variable. Reading is fine.",
            },
            {
                "topic_slug": "recursion", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))",
                "choices": [("120", True)],
            },
            {
                "topic_slug": "recursion", "domain_slug": "functions-exceptions",
                "qtype": "mc", "difficulty": "hard",
                "text": "What must every recursive function have?",
                "choices": [
                    ("A loop", False),
                    ("A base case", True),
                    ("A global variable", False),
                    ("Multiple parameters", False),
                ],
            },
            {
                "topic_slug": "recursion", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "def countdown(n):\n    if n <= 0:\n        return\n    print(n, end=' ')\n    countdown(n - 1)\n\ncountdown(3)",
                "choices": [("3 2 1 ", True)],
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "try:\n    print(1/0)\nexcept ZeroDivisionError:\n    print('oops')",
                "choices": [("oops", True)],
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "medium",
                "text": _WHAT_IS_OUTPUT,
                "code": "try:\n    x = int('abc')\nexcept ValueError:\n    print('bad value')\nexcept TypeError:\n    print('bad type')",
                "choices": [("bad value", True)],
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "qtype": "mc", "difficulty": "medium",
                "text": "Which exception is raised by accessing my_list[100] on a 3-element list?",
                "choices": [
                    ("KeyError", False),
                    ("IndexError", True),
                    ("ValueError", False),
                    ("TypeError", False),
                ],
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "qtype": "code_output", "difficulty": "hard",
                "text": _WHAT_IS_OUTPUT,
                "code": "try:\n    print('A')\n    x = 1/0\n    print('B')\nexcept ZeroDivisionError:\n    print('C')\nprint('D')",
                "choices": [("A\nC\nD", True)],
                "explanation": "'A' prints, then exception occurs so 'B' is skipped, except catches it printing 'C', then 'D' runs.",
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "qtype": "mc", "difficulty": "medium",
                "text": "Which exception does int('hello') raise?",
                "choices": [
                    ("TypeError", False),
                    ("ValueError", True),
                    ("NameError", False),
                    ("SyntaxError", False),
                ],
            },
        ]

    # ── Coding Challenges ─────────────────────────────────────────────
    def _create_coding_challenges(self):
        challenges = [
            {
                "topic_slug": "print-input", "domain_slug": "fundamentals",
                "title": "Hello, World!",
                "slug": "hello-world",
                "description": "<p>Write a program that prints <code>Hello, World!</code></p>",
                "starter_code": "# Print Hello, World!\n",
                "expected_output": "Hello, World!\n",
                "test_input": "",
                "hint_1": "Use the print() function.",
                "hint_2": "print('Hello, World!')",
                "solution_code": "print('Hello, World!')",
                "difficulty": "easy",
            },
            {
                "topic_slug": "type-casting", "domain_slug": "fundamentals",
                "title": "Data Types Explorer",
                "slug": "data-types",
                "description": "<p>Given the variable <code>x = 42</code>, print its type using <code>type()</code>.</p><p>Expected output: <code>&lt;class 'int'&gt;</code></p>",
                "starter_code": "x = 42\n# Print the type of x\n",
                "expected_output": "<class 'int'>\n",
                "test_input": "",
                "hint_1": "Use print(type(x))",
                "hint_2": "type() returns the type of any value.",
                "solution_code": "x = 42\nprint(type(x))",
                "difficulty": "easy",
            },
            {
                "topic_slug": "numeric-string-operators", "domain_slug": "fundamentals",
                "title": "Number System Converter",
                "slug": "number-systems",
                "description": "<p>Print the decimal value of the octal number <code>0o17</code> and the hex number <code>0xFF</code>, each on a new line.</p>",
                "starter_code": "# Print the decimal value of 0o17 and 0xFF\n",
                "expected_output": "15\n255\n",
                "test_input": "",
                "hint_1": "Just print the literals directly — Python converts them.",
                "hint_2": "print(0o17) prints 15",
                "solution_code": "print(0o17)\nprint(0xFF)",
                "difficulty": "easy",
            },
            {
                "topic_slug": "print-input", "domain_slug": "fundamentals",
                "title": "Greeting Program",
                "slug": "greeting-program",
                "description": "<p>Read a name from input and print <code>Hello, NAME!</code></p>",
                "starter_code": "# Read name and greet\n",
                "expected_output": "Hello, Alice!\n",
                "test_input": "Alice",
                "hint_1": "Use input() to read the name.",
                "hint_2": "name = input()\nprint('Hello, ' + name + '!')",
                "solution_code": "name = input()\nprint('Hello, ' + name + '!')",
                "difficulty": "easy",
            },
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "title": "Number Classifier",
                "slug": "number-classifier",
                "description": "<p>Read a number from input. Print <code>positive</code>, <code>negative</code>, or <code>zero</code>.</p>",
                "starter_code": "# Read number and classify\n",
                "expected_output": "positive\n",
                "test_input": "5",
                "hint_1": "Use if/elif/else to check the number's sign.",
                "hint_2": "Don't forget to convert input() to int.",
                "solution_code": "n = int(input())\nif n > 0:\n    print('positive')\nelif n < 0:\n    print('negative')\nelse:\n    print('zero')",
                "difficulty": "easy",
            },
            {
                "topic_slug": "conditionals", "domain_slug": "control-flow",
                "title": "Leap Year Checker",
                "slug": "leap-year",
                "description": "<p>Read a year from input. Print <code>Leap year</code> or <code>Not a leap year</code>.</p><p>Rules: divisible by 4, but not 100, unless also by 400.</p>",
                "starter_code": "# Check if year is a leap year\n",
                "expected_output": "Leap year\n",
                "test_input": "2024",
                "hint_1": "A year is a leap year if divisible by 4.",
                "hint_2": "But not if divisible by 100, UNLESS also by 400.",
                "hint_3": "(year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)",
                "solution_code": "year = int(input())\nif (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):\n    print('Leap year')\nelse:\n    print('Not a leap year')",
                "difficulty": "medium",
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "title": "Sum of 1 to N",
                "slug": "sum-1-to-n",
                "description": "<p>Read N from input. Print the sum of integers from 1 to N (inclusive).</p>",
                "starter_code": "# Calculate sum from 1 to N\n",
                "expected_output": "55\n",
                "test_input": "10",
                "hint_1": "Use a for loop with range(1, n+1).",
                "hint_2": "Keep a running total variable.",
                "solution_code": "n = int(input())\ntotal = 0\nfor i in range(1, n + 1):\n    total += i\nprint(total)",
                "difficulty": "easy",
            },
            {
                "topic_slug": "for-loops-range", "domain_slug": "control-flow",
                "title": "Multiplication Table",
                "slug": "multiplication-table",
                "description": "<p>Read N from input. Print the multiplication table for N from 1 to 5, each on a new line like: <code>N x 1 = result</code></p>",
                "starter_code": "# Print multiplication table\n",
                "expected_output": "3 x 1 = 3\n3 x 2 = 6\n3 x 3 = 9\n3 x 4 = 12\n3 x 5 = 15\n",
                "test_input": "3",
                "hint_1": "Use a for loop from 1 to 5.",
                "hint_2": "Use f-strings or string concatenation for formatting.",
                "solution_code": "n = int(input())\nfor i in range(1, 6):\n    print(f'{n} x {i} = {n * i}')",
                "difficulty": "easy",
            },
            {
                "topic_slug": "lists-methods", "domain_slug": "data-collections",
                "title": "List Operations",
                "slug": "list-operations",
                "description": "<p>Create a list <code>[5, 3, 8, 1, 9]</code>, sort it, then print the sorted list.</p>",
                "starter_code": "# Create list, sort, and print\n",
                "expected_output": "[1, 3, 5, 8, 9]\n",
                "test_input": "",
                "hint_1": "Use .sort() to sort in place, then print the list.",
                "hint_2": "Or use sorted() to create a new sorted list.",
                "solution_code": "nums = [5, 3, 8, 1, 9]\nnums.sort()\nprint(nums)",
                "difficulty": "easy",
            },
            {
                "topic_slug": "dictionaries", "domain_slug": "data-collections",
                "title": "Dictionary Key/Value Iteration",
                "slug": "dict-iteration",
                "description": "<p>Given the dictionary <code>{'a': 1, 'b': 2, 'c': 3}</code>, print each key-value pair on a separate line as <code>key: value</code>.</p>",
                "starter_code": "d = {'a': 1, 'b': 2, 'c': 3}\n# Print each key: value\n",
                "expected_output": "a: 1\nb: 2\nc: 3\n",
                "test_input": "",
                "hint_1": "Use a for loop with .items().",
                "hint_2": "for k, v in d.items(): print(f'{k}: {v}')",
                "solution_code": "d = {'a': 1, 'b': 2, 'c': 3}\nfor k, v in d.items():\n    print(f'{k}: {v}')",
                "difficulty": "easy",
            },
            {
                "topic_slug": "strings-methods", "domain_slug": "data-collections",
                "title": "String Methods Practice",
                "slug": "string-methods",
                "description": "<p>Read a string from input. Print it in uppercase, then in lowercase, then its length — each on a new line.</p>",
                "starter_code": "# String methods practice\n",
                "expected_output": "HELLO\nhello\n5\n",
                "test_input": "Hello",
                "hint_1": "Use .upper(), .lower(), and len().",
                "solution_code": "s = input()\nprint(s.upper())\nprint(s.lower())\nprint(len(s))",
                "difficulty": "easy",
            },
            {
                "topic_slug": "functions-return", "domain_slug": "functions-exceptions",
                "title": "Define and Call a Function",
                "slug": "define-function",
                "description": "<p>Define a function <code>double(n)</code> that returns n * 2. Read a number from input, call the function, and print the result.</p>",
                "starter_code": "# Define double() and use it\n",
                "expected_output": "10\n",
                "test_input": "5",
                "hint_1": "def double(n): return n * 2",
                "solution_code": "def double(n):\n    return n * 2\n\nprint(double(int(input())))",
                "difficulty": "easy",
            },
            {
                "topic_slug": "recursion", "domain_slug": "functions-exceptions",
                "title": "Recursive Factorial",
                "slug": "recursive-factorial",
                "description": "<p>Write a recursive function <code>factorial(n)</code> and use it to print <code>factorial(5)</code>.</p>",
                "starter_code": "# Write a recursive factorial function\n",
                "expected_output": "120\n",
                "test_input": "",
                "hint_1": "Base case: if n <= 1, return 1.",
                "hint_2": "Recursive case: return n * factorial(n - 1).",
                "solution_code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))",
                "difficulty": "medium",
            },
            {
                "topic_slug": "scope-global", "domain_slug": "functions-exceptions",
                "title": "Global Keyword Practice",
                "slug": "global-keyword",
                "description": "<p>There is a global variable <code>count = 0</code>. Write a function <code>increment()</code> that adds 1 to count using the global keyword. Call it 3 times and print count.</p>",
                "starter_code": "count = 0\n# Define increment() using global\n",
                "expected_output": "3\n",
                "test_input": "",
                "hint_1": "Use 'global count' inside the function.",
                "solution_code": "count = 0\n\ndef increment():\n    global count\n    count += 1\n\nincrement()\nincrement()\nincrement()\nprint(count)",
                "difficulty": "medium",
            },
            {
                "topic_slug": "exceptions-try-except", "domain_slug": "functions-exceptions",
                "title": "Safe Division",
                "slug": "safe-division",
                "description": "<p>Read two numbers from input. Print the result of dividing the first by the second. If division by zero occurs, print <code>Cannot divide by zero</code>.</p>",
                "starter_code": "# Safe division with try/except\n",
                "expected_output": "Cannot divide by zero\n",
                "test_input": "10\n0",
                "hint_1": "Wrap the division in try/except ZeroDivisionError.",
                "hint_2": "Read both numbers with input(), convert to int.",
                "solution_code": "a = int(input())\nb = int(input())\ntry:\n    print(a / b)\nexcept ZeroDivisionError:\n    print('Cannot divide by zero')",
                "difficulty": "easy",
            },
        ]
        for c in challenges:
            topic = Topic.objects.get(
                slug=c["topic_slug"], domain__slug=c["domain_slug"]
            )
            CodingChallenge.objects.update_or_create(
                slug=c["slug"],
                defaults={
                    "topic": topic,
                    "title": c["title"],
                    "description": c["description"],
                    "starter_code": c.get("starter_code", ""),
                    "expected_output": c["expected_output"],
                    "test_input": c.get("test_input", ""),
                    "hint_1": c.get("hint_1", ""),
                    "hint_2": c.get("hint_2", ""),
                    "hint_3": c.get("hint_3", ""),
                    "solution_code": c.get("solution_code", ""),
                    "difficulty": c.get("difficulty", "easy"),
                    "order": 0,
                },
            )
