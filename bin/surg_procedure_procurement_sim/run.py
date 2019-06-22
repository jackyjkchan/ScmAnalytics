def lucas(start, stop, step):
    if start == 0 and stop == 1 and step == 1:
        return [2]
    elif start == 0 and stop == 2 and step == 1:
        return [2, 1]
    elif start == 1 and stop == 2 and step == 1:
        return [1]
    elif start == 1 and stop == 2 and step > 1:
        return []
    elif start == 0 and step == 1:
        return lucas(0, stop-1, 1) + [lucas(0, stop-1, 1)[-1]+lucas(0, stop-1, 1)[-2]]
    else:
        return lucas(0, stop, 1)[start:stop:step]


print(lucas(0, 2, 1))
print(lucas(1, 2, 1))
print(lucas(0, 6, 1))
print(lucas(0, 7, 1))
print(lucas(0, 7, 2))
print(lucas(2, 6, 2))
