import itertools
import copy
from .perms import AllPerms, SomePerms
from hypothesis import given, settings


class Generate(object):
    def __init__(self, db, model, create_func=None):
        if create_func:
            self.create = create_func
        else:
            self.create = lambda MC, **kwargs: MC.query.create(**kwargs)
            
        self.db = db
        self.parents = None
        self.model = model
        self.n = 200
        self.dist = None
        self.strategy = {}
        self.fixtures = {}
        self.relative_values = []
        self.extras = {}
        
    def with_extras(self, **kwargs):
        ret = copy.copy(self)
        ret.extras = kwargs
        return ret
        
    def by_method(self, create_func):
        ret = copy.copy(self)
        ret.create = create_func
        return ret
            
    def execute(self):
        if self.parents is None:
            return self._do()
        else:
            return list(itertools.chain(*(self._do(**p) for p in self.parents)))
                
    def _do(self, **parents):
        if self.dist is not None:
            k = self.dist(1)[0]
            if k == 0:
                k = 1
        else:
            k = self.n
            
        recs = []
            
        @settings(max_examples=k)
        def gen(**kwargs):
            rels = {}
            for rv in self.relative_values:
                rels.update({name: xform(**kwargs, **parents, **self.fixtures, **rels, **self.extras) for name, xform in rv.items()})
            recs.append(self.create(self.model, **kwargs, **parents, **self.fixtures, **rels))
        
        if self.strategy:    
            given(**self.strategy)(gen)()
        else:
            gen()
            
        self.db.session.commit()
        return recs
    
    def num(self, n=None, dist=None):
        ret = copy.copy(self)
        
        ret.n = n
        ret.dist = dist
        
        return ret
    
    def for_every(self, *args):
        ret = copy.copy(self)
        ret.parents = AllPerms(*args)
        return ret
    
    def for_some(self, *args, from_n=None, to_n=None, dist=None):
        ret = copy.copy(self)
        ret.parents = SomePerms(*args, from_n=from_n, to_n=to_n, dist=dist)
        return ret
        
    def using(self, **strategy):
        ret = copy.copy(self)
        ret.strategy = copy.copy(self.strategy)
        ret.strategy.update(strategy)
        return ret
    
    def with_fixed_values_for(self, **fixtures):
        ret = copy.copy(self)
        ret.fixtures = copy.copy(self.fixtures)
        ret.fixtures.update(fixtures)
        return ret

    def with_relative_values_for(self, **kwargs):
        ret = copy.copy(self)
        ret.relative_values = copy.copy(ret.relative_values)
        ret.relative_values.append(kwargs)
        return ret
    
