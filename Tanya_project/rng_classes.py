from numpy import mean, random
import math


class NumberGenerator:

    def gen(self):
        return 1

    def mean(self):
        return 1


class GenerateFromSample(NumberGenerator):

    def __init__(self, samples):
        self.samples = samples
        self.average = mean(samples)

    def gen(self):
        return random.choice(self.samples)

    def mean(self):
        return self.average


class GenerateDeterministic(NumberGenerator):

    def __init__(self, value):
        self.value = value

    def gen(self):
        return self.value

    def mean(self):
        return self.value


class GenerateFromNormal(NumberGenerator):
    def __init__(self, mean1, std):
        self.mean = mean1
        self.std = std

    def gen(self):
        return random.normal(self.mean, self.std)

    def mean(self):
        return self.mean

    def sample(self, n):
        return [self.gen() for _ in range(n)]


class GenerateFromPositiveNormal(NumberGenerator):
    def __init__(self, mu, std):
        self.mu = mu
        self.std = std
        self.mean = mean(self.sample(10000))

    def gen(self):
        x = random.normal(self.mu, self.std)
        while x < 0:
            x = random.normal(self.mu, self.std)
        return x

    def mean(self):
        return self.mean

    def sample(self, n):
        return [self.gen() for _ in range(n)]


class GenerateFromLogNormal(NumberGenerator):
    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma

    def gen(self):
        return random.lognormal(self.mu, self.sigma)

    def mean(self):
        return math.exp(self.mu + self.sigma**2/2)

    def sample(self, n):
        return [self.gen() for _ in range(n)]


class GenerateFromScaledLogNormal(NumberGenerator):
    """ x ~ C * x1 where C is a constant and x1 is a LogNormal RV"""
    def __init__(self, mu, sigma, c):
        self.mu = mu
        self.sigma = sigma
        self.c = c

    def gen(self):
        return self.c * random.lognormal(self.mu, self.sigma)

    def mean(self):
        return self.c * math.exp(self.mu + self.sigma**2/2)

    def sample(self, n):
        return [self.gen() for _ in range(n)]
