#!/usr/bin/env python3
# NO ADDITIONAL IMPORTS!


#############################
# Scheme-related Exceptions #
#############################


class SchemeError(Exception):
    """
    A type of exception to be raised if there is an error with a Scheme
    program.  Should never be raised directly; rather, subclasses should be
    raised.
    """

    pass


class SchemeSyntaxError(SchemeError):
    """
    Exception to be raised when trying to evaluate a malformed expression.
    """

    pass


class SchemeNameError(SchemeError):
    """
    Exception to be raised when looking up a name that has not been defined.
    """

    pass


class SchemeEvaluationError(SchemeError):
    """
    Exception to be raised if there is an error during evaluation other than a
    SchemeNameError.
    """

    pass


############################
# Tokenization and Parsing #
############################


def number_or_symbol(x):
    """
    Helper function: given a string, convert it to an integer or a float if
    possible; otherwise, return the string itself

    >>> number_or_symbol('8')
    8
    >>> number_or_symbol('-5.32')
    -5.32
    >>> number_or_symbol('1.2.3.4')
    '1.2.3.4'
    >>> number_or_symbol('x')
    'x'
    """
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            if x == "#t":
                return True
            if x == "#f":
                return False
            if x == "nil":
                return Nil()
            return x


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a Scheme
                      expression
    """
    lines = []
    for line in source.splitlines():
        if ';' in line:
            end = line.find(';')
            lines.append(line[:end])
        else:
            lines.append(line)
    return ' '.join(lines).replace('(', ' ( ').replace(')', ' ) ').split()


def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    def parse_expression(index):

        token = tokens[index]
        if token == '(':
            next_index = index + 1
            expressions = []

            while next_index < len(tokens) and tokens[next_index] != ')':
                expression, next_index = parse_expression(next_index)
                expressions.append(expression)
            if next_index >= len(tokens):
                raise SchemeSyntaxError
            return expressions, next_index + 1
        elif token == ')':
            raise SchemeSyntaxError
        else:
            expression = number_or_symbol(token)
            return expression, index + 1
    parsed_expression, next_index = parse_expression(0)
    if next_index != len(tokens):
        raise SchemeSyntaxError
    return parsed_expression


######################
# Built-in Functions #
######################

class Pair:
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    # def __str__(self) -> str:
    #     return str(self.car) + str(self.cdr)

    # def __repr__(self) -> str:
    #     return str(self.car) + str(self.cdr)


class Nil:
    def __init__(self) -> None:
        pass

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Nil)

    def __str__(self) -> str:
        return ""


def mult(args):
    ans = 1
    for item in args:
        ans *= item
    return ans


def div(args):
    if len(args) == 0:
        raise SchemeEvaluationError
    if len(args) == 1:
        return 1 / args[0]
    return args[0] / mult(args[1:])


def op_helper(args, cmp):
    if len(args) <= 1:
        raise SchemeEvaluationError
    pre = args[0]
    for cur in args[1:]:
        if cmp(pre, cur):
            return False
        pre = cur
    return True


def gt(args):
    return op_helper(args, lambda a, b: a <= b)


def lt(args):
    return op_helper(args, lambda a, b: a >= b)


def ge(args):
    return op_helper(args, lambda a, b: a < b)


def le(args):
    return op_helper(args, lambda a, b: a > b)


def equal(args):
    return op_helper(args, lambda a, b: a != b)


def not_func(args):
    if len(args) != 1:
        raise SchemeEvaluationError
    if args[0]:
        return False
    return True


def cons_func(args):
    if len(args) != 2:
        raise SchemeEvaluationError
    return Pair(args[0], args[1])


def car_func(args):
    if len(args) != 1:
        raise SchemeEvaluationError
    cell = args[0]
    if isinstance(cell, Pair):
        return cell.car
    raise SchemeEvaluationError


def cdr_func(args):
    if len(args) != 1:
        raise SchemeEvaluationError
    cell = args[0]
    if isinstance(cell, Pair):
        return cell.cdr
    raise SchemeEvaluationError


def list_func(args):
    if len(args) == 0:
        return Nil()
    return cons_func([args[0], list_func(args[1:])])


def is_list_func(args):
    if len(args) != 1:
        raise SchemeEvaluationError
    obj = args[0]
    if isinstance(obj, Nil):
        return True
    if not isinstance(obj, Pair):
        return False
    return is_list_helper(obj.cdr)


def is_list_helper(list):
    if isinstance(list, Nil):
        return True
    if not isinstance(list, Pair):
        return False
    cdr = list.cdr
    while isinstance(cdr, Pair):
        cdr = cdr.cdr
    if isinstance(cdr, Nil):
        return True
    return False


def length_func(args):
    if len(args) != 1:
        raise SchemeEvaluationError
    obj = args[0]
    if not is_list_helper(obj):
        raise SchemeEvaluationError

    def inner(list):
        if isinstance(list, Nil):
            return 0
        return 1 + inner(list.cdr)
    return inner(obj)


def list_ref_func(args):
    if len(args) != 2:
        raise SchemeEvaluationError
    list, index = args[0], args[1]
    if not is_list_helper(list):
        if isinstance(list, Pair):
            if index == 0:
                return list.car
            raise SchemeEvaluationError
        raise SchemeEvaluationError
    if index < 0:
        raise SchemeEvaluationError

    def inner(list, index):
        if isinstance(list, Nil) and index >= 0:
            raise SchemeEvaluationError
        while index > 0:
            index -= 1
            list = list.cdr
            if isinstance(list, Nil) and index >= 0:
                raise SchemeEvaluationError
        if index == 0:
            return list.car
    return inner(list, index)


def append_func(args):
    if len(args) == 0:
        return Nil()
    items = []
    for list in args:
        if not is_list_helper(list):
            raise SchemeEvaluationError
        if isinstance(list, Pair):
            car, cdr = list.car, list.cdr
            items.append(car)
            while isinstance(cdr, Pair):
                car, cdr = cdr.car, cdr.cdr
                items.append(car)
    return list_func(items)


scheme_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": mult,
    "/": div,
    "equal?": equal,
    ">": gt,
    "<": lt,
    ">=": ge,
    "<=": le,
    "not": not_func,
    "cons": cons_func,
    "car": car_func,
    "cdr": cdr_func,
    "list": list_func,
    "list?": is_list_func,
    "length": length_func,
    "list-ref": list_ref_func,
    "append": append_func,
}


##############
# Evaluation #
##############

class Frame:
    def __init__(self,parms=(),args=(),parent=None) -> None:
        self.parent = parent
        if len(parms) != len(args):
            raise SchemeEvaluationError
        self.map = {}
        for key, value in zip(parms, args):
            self.map[key] = value

    def add(self, key, value):
        self.map[key] = value

    def get(self, key):
        if key in self.map:
            return self.map[key]
        if self.parent is None:
            return None
        return self.parent.get(key)

    def find(self, key):
        if key in self.map:
            return True
        return False

    def delete(self, key):
        value = self.map[key]
        self.map.pop(key)
        return value

    def update(self, key, value):
        if key in self.map:
            self.map[key] = value
            return
        if self.parent is not None:
            self.parent.update(key, value)


init_frame = Frame(scheme_builtins.keys(), scheme_builtins.values())

class Functions:
    def __init__(self, parameters, body, frame) -> None:
        self.body = body
        self.parameters = parameters
        self.frame = frame

    def __call__(self, args):
        function_frame = Frame(self.parameters, args, self.frame)
        return evaluate(self.body, function_frame)

    def __repr__(self) -> str:
        return "function object"


def evaluate_file(file, frame=None):
    with open(file) as f:
        source = ""
        for line in iter(f.readline, ""):
            source += line
        return evaluate(parse(tokenize(source)), frame)


def evaluate(tree, frame=None):
    """
    Evaluate the given syntax tree according to the rules of the Scheme
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if frame is None:
        frame = Frame(parent = init_frame)
    while True:
        if isinstance(tree, str):
            value = frame.get(tree)
            if value is None:
                raise SchemeNameError
            return value
        if not isinstance(tree, list):
            return tree
        if len(tree) < 1:
            raise SchemeEvaluationError
        op, rest = tree[0], tree[1:]
        if op == 'define':
            if len(rest) != 2:
                raise SchemeEvaluationError
            name = rest[0]
            if isinstance(name, list):
                key = name[0]
                parameters = name[1:]
                body = rest[1]
                expr = Functions(parameters, body, frame)
                frame.add(key, expr)
                return expr
            expr = evaluate(rest[1], frame)
            frame.add(name, expr)
            return expr
        if op == 'lambda':
            if len(rest) != 2:
                raise SchemeEvaluationError
            parameters = rest[0]
            body = rest[1]
            return Functions(parameters, body, frame)
        if op == "if":
            if len(rest) != 3:
                raise SchemeEvaluationError
            cond = rest[0]
            true_exp = rest[1]
            false_exp = rest[2]
            if evaluate(cond, frame):
                return evaluate(true_exp, frame)
            else:
                return evaluate(false_exp, frame)
        if op == "and":
            for cond in rest:
                if not evaluate(cond, frame):
                    return False
            return True
        if op == "or":
            for cond in rest:
                if evaluate(cond, frame):
                    return True
            return False
        if op == "begin":
            value = None
            for exp in rest:
                value = evaluate(exp, frame)
            return value
        if op == "del":
            if len(rest) != 1:
                raise SchemeEvaluationError
            key = rest[0]
            if frame.find(key):
                return frame.delete(key)
            raise SchemeNameError
        if op == "let":
            if len(rest) != 2:
                raise SchemeEvaluationError
            body = rest[1]
            inner_frame = Frame(parent=frame)
            for item in rest[0]:
                if len(item) != 2:
                    raise SchemeEvaluationError
                var = item[0]
                val = evaluate(item[1], frame)
                inner_frame.add(var, val)
            return evaluate(body, inner_frame)
        if op == "set!":
            if len(rest) != 2:
                raise SchemeEvaluationError
            var = rest[0]
            exp = rest[1]
            value = frame.get(var)
            if value is None:
                raise SchemeNameError
            value = evaluate(exp, frame)
            frame.update(var, value)
            return value

        exps = [evaluate(exp, frame) for exp in tree]
        func = exps.pop(0)
        if isinstance(func, Functions):
            tree = func.body
            frame = Frame(func.parameters, exps, func.frame)
        elif callable(func):
            return func(exps)
        else:
            raise SchemeEvaluationError


def result_and_frame(tree, frame=None):
    if frame is None:
        frame = Frame(parent=init_frame)
    value = evaluate(tree, frame)
    return value, frame

########
# REPL #
########


def repl(raise_all=False, global_frame=None):
    while True:
        # read the input.  pressing ctrl+d exits, as does typing "EXIT" at the
        # prompt.  pressing ctrl+c moves on to the next prompt, ignoring
        # current input
        try:
            inp = input("in> ")
            if inp.strip().lower() == "exit":
                print("  bye bye!")
                return
        except EOFError:
            print()
            print("  bye bye!")
            return
        except KeyboardInterrupt:
            print()
            continue

        try:
            # tokenize and parse the input
            tokens = tokenize(inp)
            ast = parse(tokens)
            # if global_frame has not been set, we want to call
            # result_and_frame without it (which will give us our new frame).
            # if it has been set, though, we want to provide that value
            # explicitly.
            args = [ast]
            if global_frame is not None:
                args.append(global_frame)
            result, global_frame = result_and_frame(*args)
            # finally, print the result
            print("  out> ", result)
        except SchemeError as e:
            # if raise_all was given as True, then we want to raise the
            # exception so we see a full traceback.  if not, just print some
            # information about it and move on to the next step.
            #
            # regardless, all Python exceptions will be raised.
            if raise_all:
                raise
            print(f"{e.__class__.__name__}:", *e.args)
        print()


if __name__ == "__main__":
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)

    # uncommenting the following line will run doctests from above
    # doctest.testmod()
    print(sys.argv)
    global_frame = Frame(parent=init_frame)
    if len(sys.argv) > 1:
        for file in sys.argv[1:]:
            evaluate_file(file, global_frame)
    repl(True, global_frame)
