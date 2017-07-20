import copy
from collections import OrderedDict
import itertools
import numpy as np
from functools import partial

class AllPerms(object):
    def __init__(self, *args):
        self.of = args
            
    def __iter__(self):
        tally = []
        values = (pair[1] for pair in self.of)
        keys = [pair[0] for pair in self.of]
        
        # evaluate any transformers in order
        for i, v in enumerate(values):
            if callable(v):  # then create a permutation for everything 
                for p in [x for x in AllPerms(*tally)]:
                    tally.append((keys[i], v(**p)))
            else:
                tally.append((keys[i], v))
                
        values = (pair[1] for pair in tally)
        
        for tup in itertools.product(*values):
            yield dict(zip(keys, tup))
            

class SomePerms(AllPerms):
    def __init__(self, *args, dist=None, from_n=None, to_n=None):
        super(SomePerms, self).__init__(*args)
        self.dist = dist or partial(np.random.binomial, 1, 0.5)
        self.from_n = from_n
        self.to_n = to_n
        self.n = 0
        
    def __iter__(self):
        i = 0
        n = []
        for x in super(SomePerms, self).__iter__():
            a = self.dist(1)[0]
            if a > 0.5:
                yield x
                n.append(i)
            i += 1
            if self.to_n is not None and len(n) >= to_n:
                break
                
        if self.from_n and len(n) < self.from_n:
            i = 0
            for x in super(SomePerms, self).__iter__():
                if i not in n:
                    yield x
                    n.append(i)
                    i += 1
                    
                    if len(n) >= self.from_n:
                        break
