from numpy import random
import time



s = 0
trials = 100000000
c = list(range(1000))

# start = time.time()
# for i in range(trials):
#     random.choice(c, replace=True)
# print(time.time() - start)

start = time.time()
r = random.choice(c, trials)
for i in range(trials):
    r[i]
print(time.time()-start)

start = time.time()
l = len(c)
indices = list(int(i*l) for i in random.rand(trials))
for i in indices:
    c[i]

print(time.time()-start)
