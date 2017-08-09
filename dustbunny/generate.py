import itertools
import copy
from .perms import AllPerms, SomePerms
from hypothesis import given, settings
from io import StringIO


class Generate(object):
    """
    This is the main class for generating records via Hypothesis. Every call returns a new Generator object instead of
    modifying the current object. Therefore the general procedure is to use this in "combinator"
    style, similar to the way you add filters to SQLAlchemy queries.  In other words::
    
        g = Generate(db, model).by_method(create_func)
        g = g.with_fixed_values_for(...)
        g = g.with_random_values_for(...)
        g.execute()
        
    """
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
        self.generated_instances = []

    def with_extras(self, **kwargs):
        """
        These are available to the relative_values combinator.
        """
        ret = copy.copy(self)
        ret.extras = kwargs
        return ret
        
    def by_method(self, create_func):
        """
        Determine what function to use to commit and create records to the database.
        
        :param create_func: 
        :return: Generate
        """
        ret = copy.copy(self)
        ret.create = create_func
        return ret
            
    def execute(self):
        """
        Actually run the generation script.
        
        :return: a list of generated instances.
        """
        if self.parents is None:
            self.generated_instances.extend(self._do())
        else:
            self.generated_instances.extend(list(itertools.chain(*(self._do(**p) for p in self.parents))))
        return self.generated_instances
        
    def remove(self):
        """
        Removes all the generated instances from the database.
        
        :return: None 
        """
        for inst in reversed(self.generated_instances):
            self.db.session.delete(inst)
        self.db.session.commit()
                
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
        """
        Set the number of instances to generate for each parent object. 
        
        :param n (int): A fixed number of instances to generate 
        :param dist (function): A varaible number of instances to generate. Dist should be a function of zero parameters
            that returns a random number between 0 and the max number of instances you want to generate.
        :return: Generate
        """
        ret = copy.copy(self)
        
        ret.n = n
        ret.dist = dist
        
        return ret
    
    def for_every(self, *args):
        """
        Generates child instances, one for every permutation of args.
        
        :param args (tuples): each tuple should be a `(key, value)` pair of (`attribute_name`, `possible_values` (some iterable))  
        :return: Generate
        """
        ret = copy.copy(self)
        ret.parents = AllPerms(*args)
        return ret
    
    def for_some(self, *args, from_n=None, to_n=None, dist=None):
        """
        Generates child instances for some random permutations of args. 
        
        :param args: Same as in the `for_every` call 
        :param from_n: The minimum number of permutations to generate new instances for
        :param to_n: The maximum number of permutations to generate new instances for
        :param dist: The distribution to use (by default a simple binomial distribution, but otherwise use the same as the `dist` param of `num`
        :return: Generate
        """
        ret = copy.copy(self)
        ret.parents = SomePerms(*args, from_n=from_n, to_n=to_n, dist=dist)
        return ret
        
    def using(self, **strategy):
        """
        Use random values selected from hypothesis strategies for a set of attribute values.
        
        :param strategy (attr_name -> hypothesis strategy): A mapping of attribute names to hypothesis strategies
        :return: Generate
        """
        ret = copy.copy(self)
        ret.strategy = copy.copy(self.strategy)
        ret.strategy.update(strategy)
        return ret

    def with_random_values_for(self, **strategy):
        """
        More descriptively named alias for `using`
        
        :param strategy (attr_name -> hypothesis strategy): A mapping of attribute names to hypothesis strategies
        :return: Generate
        """
        return self.using(**strategy)
    
    def with_fixed_values_for(self, **fixtures):
        """
        Use fixed values for the given set of attributes.
        
        :param fixtures (attr_name -> attr_value): A mapping of attribute names to static values. These will be used 
            directly to assign to attribute values on the database record.
            
        :return: Generate 
        """
        ret = copy.copy(self)
        ret.fixtures = copy.copy(self.fixtures)
        ret.fixtures.update(fixtures)
        return ret

    def with_relative_values_for(self, **kwargs):
        """
        Use relative values for the given set of attributes.
        
        :param kwargs (attr_name -> function): A mapping of attibute names to functions of a single dictionary argument
            containing all values already set for any given record so far.  Fixed, random, and "extra" values. The 
            function should return the value you wnat to use for the attribute for that record.
            
        :return: Generate
        """
        ret = copy.copy(self)
        ret.relative_values = copy.copy(ret.relative_values)
        ret.relative_values.append(kwargs)
        return ret
    
