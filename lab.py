#!/usr/bin/env python3

import doctest

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

def mult(args):
    ans = 1
    for item in args:
        ans *= item
    return ans
def div(args):
    if len(args) == 0:
        raise SchemeEvaluationError
    if len(args) == 1:
        return 1/ args[0]
    return args[0]/ mult(args[1:])

scheme_builtins = {
    "+": sum,
    "-": lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    "*": mult,
    "/": div
}


##############
# Evaluation #
##############


def evaluate(tree):
    """
    Evaluate the given syntax tree according to the rules of the Scheme
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    if isinstance(tree, str):
        if tree in scheme_builtins.keys():
            return scheme_builtins[tree]
    if not isinstance(tree, list):
        return tree
    op, rest = tree[0], tree[1:]
    func = evaluate(op)
    if not hasattr(func, '__call__'):
        raise SchemeEvaluationError
    args = [evaluate(arg) for arg in rest]
    return func(args)


########
# REPL #
########


def repl(raise_all=False):
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
            # tokenize and parse the input, then evaluate and print the result
            tokens = tokenize(inp)
            ast = parse(tokens)
            print("  out> ", evaluate(ast))
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

    repl()
