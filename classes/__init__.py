import re
from random import randint

def roll_dice(nd,manual):
    result = 0
    if nd.startswith("d"):
        nd = "1" + nd
    if bool(re.search("^[0-9]*d[0-9]*$", nd)):
        split_nd = nd.split("d")
        n = int(split_nd[0])
        d = int(split_nd[1])
    else:
        raise ValueError("Invalid roll description")
    if manual:
        result = int(input(f"Roll {nd} and type in the result. Press 0 to let the computer do it: "))
        if result > n * d:
            result = int(input(f"That result {result} is more than is possible with {nd}. If you're doing this on purpose as a test, enter the same thing now: "))

    if result == 0: # If manual dice rolls is false or the input from the user was 0
        nd = nd.lower()
        for _ in range(0,n):
            roll = randint(1,d)
            result += roll
    return result