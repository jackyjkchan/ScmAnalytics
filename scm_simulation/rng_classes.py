import random
from numpy import mean


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
