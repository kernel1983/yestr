
import inspect

def log(*t):
    print()
    print(inspect.stack()[1].function, inspect.stack()[1].filename+':', inspect.stack()[1].lineno)
    print(*t)

