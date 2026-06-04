"""The underlying data structure used in gplearn.

The :mod:`gplearn._program` module contains the underlying representation of a
computer program. It is used for creating and evolving programs used in the
:mod:`gplearn.genetic` module.
"""

# Author: Trevor Stephens <trevorstephens.com>
#
# License: BSD 3 clause

from copy import copy

import numpy as np
from sklearn.utils.random import sample_without_replacement

from .functions import _Function
from .utils import check_random_state

# from scipy import stats
# import pandas as pd

# import pickle
# import cloudpickle as pickle

def make_ts_function(function, d_ls, random_state):
    """
    Parameters
    ----------
    function: _Function
        时间序列函数.

    d_ls: list
        参数 'd' 可选范围.

    random_state: RandomState instance
        随机数生成器.

    """
    d = random_state.randint(len(d_ls))
    d = d_ls[d]
    function_ = copy(function)
    function_.set_d(d)
    return function_



class _Program(object):

    """A program-like representation of the evolved program.

    This is the underlying data-structure used by the public classes in the
    :mod:`gplearn.genetic` module. It should not be used directly by the user.

    Parameters
    ----------
    function_set : list
        A list of valid functions to use in the program.

    arities : dict
        A dictionary of the form `{arity: [functions]}`. The arity is the
        number of arguments that the function takes, the functions must match
        those in the `function_set` parameter.

    init_depth : tuple of two ints
        The range of tree depths for the initial population of naive formulas.
        Individual trees will randomly choose a maximum depth from this range.
        When combined with `init_method='half and half'` this yields the well-
        known 'ramped half and half' initialization method.

    init_method : str
        - 'grow' : Nodes are chosen at random from both functions and
          terminals, allowing for smaller trees than `init_depth` allows. Tends
          to grow asymmetrical trees.
        - 'full' : Functions are chosen until the `init_depth` is reached, and
          then terminals are selected. Tends to grow 'bushy' trees.
        - 'half and half' : Trees are grown through a 50/50 mix of 'full' and
          'grow', making for a mix of tree shapes in the initial population.

    n_features : int
        The number of features in `X`.

    const_range : tuple of two floats
        The range of constants to include in the formulas.

    metric : _Fitness object
        The raw fitness metric.

    p_point_replace : float
        The probability that any given node will be mutated during point
        mutation.

    parsimony_coefficient : float
        This constant penalizes large programs by adjusting their fitness to
        be less favorable for selection. Larger values penalize the program
        more which can control the phenomenon known as 'bloat'. Bloat is when
        evolution is increasing the size of programs without a significant
        increase in fitness, which is costly for computation time and makes for
        a less understandable final result. This parameter may need to be tuned
        over successive runs.

    random_state : RandomState instance
        The random number generator. Note that ints, or None are not allowed.
        The reason for this being passed is that during parallel evolution the
        same program object may be accessed by multiple parallel processes.

    transformer : _Function object, optional (default=None)
        The function to transform the output of the program to probabilities,
        only used for the SymbolicClassifier.

    feature_names : list, optional (default=None)
        Optional list of feature names, used purely for representations in
        the `print` operation or `export_graphviz`. If None, then X0, X1, etc
        will be used for representations.

    program : list, optional (default=None)
        The flattened tree representation of the program. If None, a new naive
        random tree will be grown. If provided, it will be validated.

    Attributes
    ----------
    program : list
        The flattened tree representation of the program.

    raw_fitness_ : float
        The raw fitness of the individual program.

    fitness_ : float
        The penalized fitness of the individual program.

    oob_fitness_ : float
        The out-of-bag raw fitness of the individual program for the held-out
        samples. Only present when sub-sampling was used in the estimator by
        specifying `max_samples` < 1.0.

    parents : dict, or None
        If None, this is a naive random program from the initial population.
        Otherwise it includes meta-data about the program's parent(s) as well
        as the genetic operations performed to yield the current program. This
        is set outside this class by the controlling evolution loops.

    depth_ : int
        The maximum depth of the program tree.

    length_ : int
        The number of functions and terminals in the program.

    """

    def __init__(self,
                 function_set,
                 ts_function_set,
                 fixed_function_set,                 
                 arities,
                 init_depth,
                 init_method,
                 n_features,
                 const_range,
                 metric,
                 p_point_replace,
                 parsimony_coefficient,
                 random_state,
                 transformer=None,
                 feature_names=None,
                 program=None):

        self.d_ls = [1,2,3,6,9,12]  # 时间序列偏移量列表
        # self.d_ls = [5,10,15,20]#时间序列偏移量列表
        self.ts_function_set = ts_function_set
        self.fixed_function_set = fixed_function_set
        
        self.function_set = function_set
        self.arities = arities
        self.init_depth = (init_depth[0], init_depth[1] + 1)
        self.init_method = init_method
        self.n_features = n_features
        self.const_range = const_range
        self.metric = metric
        self.p_point_replace = p_point_replace
        self.parsimony_coefficient = parsimony_coefficient
        self.transformer = transformer
        self.feature_names = feature_names
        self.program = program
        
        
        # print(12345667)
        if self.program is not None:
            if not self.validate_program():
                raise ValueError('The supplied program is incomplete.')
        else:
            # Create a naive random program
            self.program = self.build_program(random_state)

        self.raw_fitness_ = None
        self.fitness_ = None
        self.parents = None
        self._n_samples = None
        self._max_samples = None
        self._indices_state = None
        


    # def build_program(self, random_state):
    #     """Build a naive random program.

    #     Parameters
    #     ----------
    #     random_state : RandomState instance
    #         The random number generator.

    #     Returns
    #     -------
    #     program : list
    #         The flattened tree representation of the program.

    #     """
    #     if self.init_method == 'half and half':
    #         method = ('full' if random_state.randint(2) else 'grow')
    #     else:
    #         method = self.init_method
    #     max_depth = random_state.randint(*self.init_depth)

    #     # Start a program with a function to avoid degenerative programs
    #     function = random_state.randint(len(self.function_set))
    #     function = self.function_set[function]
    #     program = [function]
    #     terminal_stack = [function.arity]

    #     while terminal_stack:
    #         depth = len(terminal_stack)
    #         choice = self.n_features + len(self.function_set)
    #         choice = random_state.randint(choice)
    #         # Determine if we are adding a function or terminal
    #         if (depth < max_depth) and (method == 'full' or
    #                                     choice <= len(self.function_set)):
    #             function = random_state.randint(len(self.function_set))
    #             function = self.function_set[function]
    #             program.append(function)
    #             terminal_stack.append(function.arity)
    #         else:
    #             # We need a terminal, add a variable or constant
    #             if self.const_range is not None:
    #                 terminal = random_state.randint(self.n_features + 1)
    #             else:
    #                 terminal = random_state.randint(self.n_features)
    #             if terminal == self.n_features:
    #                 terminal = random_state.uniform(*self.const_range)
    #                 if self.const_range is None:
    #                     # We should never get here
    #                     raise ValueError('A constant was produced with '
    #                                      'const_range=None.')
    #             program.append(terminal)
    #             terminal_stack[-1] -= 1
    #             while terminal_stack[-1] == 0:
    #                 terminal_stack.pop()
    #                 if not terminal_stack:
    #                     return program
    #                 terminal_stack[-1] -= 1

    #     # We should never get here
    #     return None

    def build_program(self, random_state):
        """Build a naive random program.
    
        Parameters
        ----------
        random_state : RandomState instance
            The random number generator.
    
        Returns
        -------
        program : list
            The flattened tree representation of the program.
    
        """
        if self.init_method == 'half and half':
            method = ('full' if random_state.randint(2) else 'grow')
        else:
            method = self.init_method
        max_depth = random_state.randint(*self.init_depth)
    
        # Start a program with a function to avoid degenerative programs
    
        # function = random_state.randint(len(self.function_set))
        function = random_state.randint(len(self.function_set) + len(self.ts_function_set))
        # function = self.function_set[function]
        if function < len(self.function_set):
            function = self.function_set[function]
        else:
            function = make_ts_function(self.ts_function_set[function - len(self.function_set)],
                                        self.d_ls, random_state)
    
        program = [function]
        terminal_stack = [function.arity]
    
        while terminal_stack:
            depth = len(terminal_stack)
    
            # choice = self.n_features + len(self.function_set)
            choice = self.n_features + len(self.function_set) + len(self.ts_function_set) +             len(self.fixed_function_set)
    
            choice = random_state.randint(choice)
    
            # Determine if we are adding a function or terminal
            # if (depth < max_depth) and (method == 'full' or
            #                             choice <= len(self.function_set)):
            if (depth < max_depth) and (method == 'full' or
                                        choice < len(self.function_set) + len(self.ts_function_set)):
                # function = random_state.randint(len(self.function_set))
                function = random_state.randint(len(self.function_set) + len(self.ts_function_set))
                # function = self.function_set[function]
                # if choice < len(self.function_set):
                if function < len(self.function_set):
                    function = self.function_set[function]
                else:
                    # print(2222222222222222)
                    # print(1,function,len(self.function_set))
                    # with open(r'D:/Work/遗传算法测试/debug/test.pkl','wb') as file:
                        # pickle.dump([choice,self.function_set,choice - len(self.function_set)],file)
                        # pickle.dump([self.ts_function_set[choice - len(self.function_set)],self.function_set[0]],file)
                    # function = random_state.randint(len(self.ts_function_set))    
                    function = make_ts_function(self.ts_function_set[function - len(self.function_set)],self.d_ls, random_state)
                    # function = make_ts_function(self.ts_function_set[choice - len(self.function_set)],
                                                # self.d_ls, random_state)
                program.append(function)
                terminal_stack.append(function.arity)
            else:
                # We need a terminal, add a variable or a fixed function or constant
                if self.const_range is not None:
                    # terminal = random_state.randint(self.n_features + 1)
                    terminal = random_state.randint(self.n_features + len(self.fixed_function_set) + 1)
                else:
                    # terminal = random_state.randint(self.n_features)
                    terminal = random_state.randint(self.n_features + len(self.fixed_function_set))
                # if terminal == self.n_features:
                if terminal == self.n_features + len(self.fixed_function_set):
                    terminal = random_state.uniform(*self.const_range)
                    # print('const:', terminal, self.const_range)
                    if self.const_range is None:
                        # We should never get here
                        raise ValueError('A constant was produced with '
                                         'const_range=None.')
                # 新增
                elif terminal >= self.n_features:
                    terminal = make_ts_function(self.fixed_function_set[terminal - self.n_features],
                                                self.d_ls, random_state)
                program.append(terminal)
                terminal_stack[-1] -= 1
                while terminal_stack[-1] == 0:
                    terminal_stack.pop()
                    if not terminal_stack:
                        return program
                    terminal_stack[-1] -= 1
    
        # We should never get here
        return None

    def validate_program(self):
        """Rough check that the embedded program in the object is valid."""
        terminals = [0]
        for node in self.program:
            if isinstance(node, _Function):
                # 新增条件
                if node.arity != 0:
                    terminals.append(node.arity)
                # 新增
                else:
                    terminals[-1] -= 1
                    while terminals[-1] == 0:
                        terminals.pop()
                        terminals[-1] -= 1
            else:
                terminals[-1] -= 1
                while terminals[-1] == 0:
                    terminals.pop()
                    terminals[-1] -= 1
        return terminals == [-1]

    def __str__(self):
        """Overloads `print` output of the object to resemble a LISP tree."""
        terminals = [0]
        output = ''
        for i, node in enumerate(self.program):
            if isinstance(node, _Function):
                # 新增条件
                if node.arity != 0:
                    terminals.append(node.arity)
                    output += node.name + '('
                # 新增
                else:
                    output += node.name + '(%s)' % ', '.join(node.params_need)
                    terminals[-1] -= 1
                    while terminals[-1] == 0:
                        terminals.pop()
                        terminals[-1] -= 1
                        output += ')'
                    if i != len(self.program) - 1:
                        output += ', '
            else:
                if isinstance(node, int):
                    if self.feature_names is None:
                        output += 'X%s' % node
                    else:
                        output += self.feature_names[node]
                else:
                    output += '%.3f' % node
                terminals[-1] -= 1
                while terminals[-1] == 0:
                    terminals.pop()
                    terminals[-1] -= 1
                    output += ')'
                if i != len(self.program) - 1:
                    output += ', '
        return output
    
    def _depth(self):
        """Calculates the maximum depth of the program tree."""
        terminals = [0]
        depth = 1
        for node in self.program:
            if isinstance(node, _Function):
                # 新增条件
                if node.arity != 0:
                    terminals.append(node.arity)
                    depth = max(len(terminals), depth)
                # 新增
                else:
                    terminals[-1] -= 1
                    while terminals[-1] == 0:
                        terminals.pop()
                        terminals[-1] -= 1
            else:
                terminals[-1] -= 1
                while terminals[-1] == 0:
                    terminals.pop()
                    terminals[-1] -= 1
        return depth - 1
    

    # def validate_program(self):
    #     """Rough check that the embedded program in the object is valid."""
    #     terminals = [0]
    #     for node in self.program:
    #         if isinstance(node, _Function):
    #             terminals.append(node.arity)
    #         else:
    #             terminals[-1] -= 1
    #             while terminals[-1] == 0:
    #                 terminals.pop()
    #                 terminals[-1] -= 1
    #     return terminals == [-1]

    # def __str__(self):
    #     """Overloads `print` output of the object to resemble a LISP tree."""
    #     terminals = [0]
    #     output = ''
    #     for i, node in enumerate(self.program):
    #         if isinstance(node, _Function):
    #             terminals.append(node.arity)
    #             output += node.name + '('
    #         else:
    #             if isinstance(node, int):
    #                 if self.feature_names is None:
    #                     output += 'X%s' % node
    #                 else:
    #                     output += self.feature_names[node]
    #             else:
    #                 output += '%.3f' % node
    #             terminals[-1] -= 1
    #             while terminals[-1] == 0:
    #                 terminals.pop()
    #                 terminals[-1] -= 1
    #                 output += ')'
    #             if i != len(self.program) - 1:
    #                 output += ', '
    #     return output

    def export_graphviz(self, fade_nodes=None):
        """Returns a string, Graphviz script for visualizing the program.

        Parameters
        ----------
        fade_nodes : list, optional
            A list of node indices to fade out for showing which were removed
            during evolution.

        Returns
        -------
        output : string
            The Graphviz script to plot the tree representation of the program.

        """
        terminals = []
        if fade_nodes is None:
            fade_nodes = []
        output = 'digraph program {\nnode [style=filled]\n'
        for i, node in enumerate(self.program):
            fill = '#cecece'
            if isinstance(node, _Function):
                if i not in fade_nodes:
                    fill = '#136ed4'
                terminals.append([node.arity, i])
                output += ('%d [label="%s", fillcolor="%s"] ;\n'
                           % (i, node.name, fill))
            else:
                if i not in fade_nodes:
                    fill = '#60a6f6'
                if isinstance(node, int):
                    if self.feature_names is None:
                        feature_name = 'X%s' % node
                    else:
                        feature_name = self.feature_names[node]
                    output += ('%d [label="%s", fillcolor="%s"] ;\n'
                               % (i, feature_name, fill))
                else:
                    output += ('%d [label="%.3f", fillcolor="%s"] ;\n'
                               % (i, node, fill))
                if i == 0:
                    # A degenerative program of only one node
                    return output + '}'
                terminals[-1][0] -= 1
                terminals[-1].append(i)
                while terminals[-1][0] == 0:
                    output += '%d -> %d ;\n' % (terminals[-1][1],
                                                terminals[-1][-1])
                    terminals[-1].pop()
                    if len(terminals[-1]) == 2:
                        parent = terminals[-1][-1]
                        terminals.pop()
                        if not terminals:
                            return output + '}'
                        terminals[-1].append(parent)
                        terminals[-1][0] -= 1

        # We should never get here
        return None

    # def _depth(self):
    #     """Calculates the maximum depth of the program tree."""
    #     terminals = [0]
    #     depth = 1
    #     for node in self.program:
    #         if isinstance(node, _Function):
    #             terminals.append(node.arity)
    #             depth = max(len(terminals), depth)
    #         else:
    #             terminals[-1] -= 1
    #             while terminals[-1] == 0:
    #                 terminals.pop()
    #                 terminals[-1] -= 1
    #     return depth - 1

    def _length(self):
        """Calculates the number of functions and terminals in the program."""
        return len(self.program)

    # def execute(self, X):
    #     """Execute the program according to X.

    #     Parameters
    #     ----------
    #     X : {array-like}, shape = [n_samples, n_features]
    #         Training vectors, where n_samples is the number of samples and
    #         n_features is the number of features.

    #     Returns
    #     -------
    #     y_hats : array-like, shape = [n_samples]
    #         The result of executing the program on X.

    #     """
    #     # Check for single-node programs
    #     node = self.program[0]
    #     if isinstance(node, float):
    #         return np.repeat(node, X.shape[0])
    #     if isinstance(node, int):
    #         return X[:, node]

    #     apply_stack = []

    #     for node in self.program:

    #         if isinstance(node, _Function):
    #             apply_stack.append([node])
    #         else:
    #             # Lazily evaluate later
    #             apply_stack[-1].append(node)

    #         while len(apply_stack[-1]) == apply_stack[-1][0].arity + 1:
    #             # Apply functions that have sufficient arguments
    #             function = apply_stack[-1][0]
    #             terminals = [np.repeat(t, X.shape[0]) if isinstance(t, float)
    #                          else X[:, t] if isinstance(t, int)
    #                          else t for t in apply_stack[-1][1:]]
    #             intermediate_result = function(*terminals)
    #             if len(apply_stack) != 1:
    #                 apply_stack.pop()
    #                 apply_stack[-1].append(intermediate_result)
    #             else:
    #                 return intermediate_result

    #     # We should never get here
    #     return None
    
    def execute(self, X):
        """Execute the program according to X.
    
        Parameters
        ----------
        X : {array-like}, shape = [n_samples, n_features]
            Training vectors, where n_samples is the number of samples and
            n_features is the number of features.
    
        Returns
        -------
        y_hats : array-like, shape = [n_samples]
            The result of executing the program on X.
    
        """
        # Check for single-node programs
        node = self.program[0]
        if isinstance(node, float):
            return np.repeat(node, X.shape[0])
        if isinstance(node, int):
            return X[:, node]
    
        apply_stack = []
    
        for node in self.program:
    
            if isinstance(node, _Function):
                # 新增
                if node.arity != 0:
                    apply_stack.append([node])
                else:
                    args_ = [X[:, self.feature_names.index(name)] for name in node.params_need]
                    t = node(*args_)
                    if apply_stack:
                        apply_stack[-1].append(t)
                    else:
                        return t
            else:
                # Lazily evaluate later
                if apply_stack:
                    apply_stack[-1].append(node)
                else:
                    return np.repeat(node, X.shape[0]) if isinstance(node, float) \
                        else X[:, node]
    
            while len(apply_stack[-1]) == apply_stack[-1][0].arity + 1:
                # Apply functions that have sufficient arguments
                function = apply_stack[-1][0]               

                
                terminals = [np.repeat(t, X.shape[0]) if isinstance(t, float)
                             else X[:, t] if isinstance(t, int)
                else t for t in apply_stack[-1][1:]]
                # with open(r'D:/Work/遗传算法测试/debug/test2.pkl','wb') as file:
                    # pickle.dump([self.program,X,terminals,function],file)
                
                intermediate_result = function(*terminals)
                if len(apply_stack) != 1:
                    apply_stack.pop()
                    apply_stack[-1].append(intermediate_result)
                else:
                    return intermediate_result
    
        # We should never get here
        return None

    
    def get_all_indices(self, n_samples=None, max_samples=None,
                        random_state=None):
        """Get the indices on which to evaluate the fitness of a program.

        Parameters
        ----------
        n_samples : int
            The number of samples.

        max_samples : int
            The maximum number of samples to use.

        random_state : RandomState instance
            The random number generator.

        Returns
        -------
        indices : array-like, shape = [n_samples]
            The in-sample indices.

        not_indices : array-like, shape = [n_samples]
            The out-of-sample indices.

        """
        if self._indices_state is None and random_state is None:
            raise ValueError('The program has not been evaluated for fitness '
                             'yet, indices not available.')

        if n_samples is not None and self._n_samples is None:
            self._n_samples = n_samples
        if max_samples is not None and self._max_samples is None:
            self._max_samples = max_samples
        if random_state is not None and self._indices_state is None:
            self._indices_state = random_state.get_state()

        indices_state = check_random_state(None)
        indices_state.set_state(self._indices_state)

        not_indices = sample_without_replacement(
            self._n_samples,
            self._n_samples - self._max_samples,
            random_state=indices_state)
        sample_counts = np.bincount(not_indices, minlength=self._n_samples)
        indices = np.where(sample_counts == 0)[0]

        return indices, not_indices

    def _indices(self):
        """Get the indices used to measure the program's fitness."""
        return self.get_all_indices()[0]

    def raw_fitness(self, X, y, score_data,sample_weight,seed = -777,circle = 3):


    #     """Evaluate the raw fitness of the program according to X, y.

    #     Parameters
    #     ----------
    #     X : {array-like}, shape = [n_samples, n_features]
    #         Training vectors, where n_samples is the number of samples and
    #         n_features is the number of features.

    #     y : array-like, shape = [n_samples]
    #         Target values.

    #     sample_weight : array-like, shape = [n_samples]
    #         Weights applied to individual samples.

    #     Returns
    #     -------
    #     raw_fitness : float
    #         The raw fitness of the program.

    #     """

        y_pred = self.execute(X)
        raw_fitness = self.metric(y, y_pred, sample_weight)

        if len(score_data) != 0:
            raw_fitness_list = [raw_fitness]
            for temp_list in score_data:
                X, y = temp_list
                y_pred = self.execute(X)
                raw_fitness = self.metric(y, y_pred, sample_weight)
                raw_fitness_list.append(raw_fitness)
            raw_fitness = np.mean(raw_fitness_list)
            # raw_fitness = np.min(raw_fitness_list)
        # y_pred = self.execute(X)
    #     if self.transformer:
    #         y_pred = self.transformer(y_pred)
        # raw_fitness = self.metric(y, y_pred, sample_weight)
        # seed = -777
        # if seed == -777:
        #     y_pred = self.execute(X)
        #     raw_fitness = self.metric(y, y_pred, sample_weight)
        #
        #     if len(score_data) != 0:
        #         raw_fitness_list = [raw_fitness]
        #         for temp_list in score_data:
        #             X, y = temp_list
        #             y_pred = self.execute(X)
        #             raw_fitness = self.metric(y, y_pred, sample_weight)
        #             raw_fitness_list.append(raw_fitness)
        #         # raw_fitness = np.mean(raw_fitness_list)
        #         raw_fitness = np.min(raw_fitness_list)
        # else:
        #     random_state = check_random_state(seed)
        #     raw_fitness_list = []
        #     X0 = X.copy()
        #     a,b = X0.shape
        #     for i in range(circle):
        #         circle_raw_fitness_list = []
        #         X_add = random_state.normal(0,0.001,(a,b))
        #         X_add[np.where(X_add > 0.003)] = 0.003
        #         X_add[np.where(X_add < -0.003)] = -0.003
        #         X_temp = (1 + X0) * np.exp(X_add) - 1
        #         y_pred = self.execute(X_temp)
        #
        #         raw_fitness = self.metric(y, y_pred, sample_weight)
        #         circle_raw_fitness_list.append(raw_fitness)
        #
        #         if len(score_data) != 0:
        #             for temp_list in score_data:
        #                 X, y = temp_list
        #                 y_pred = self.execute(X_temp)
        #                 raw_fitness = self.metric(y, y_pred, sample_weight)
        #                 # raw_fitness_list.append(raw_fitness)
        #                 circle_raw_fitness_list.append(raw_fitness)
        #         raw_fitness_list.append(np.min(circle_raw_fitness_list))
        #     # raw_fitness = np.mean(raw_fitness_list)
        #     raw_fitness = np.mean(raw_fitness_list)





        return raw_fitness
    
    
    # def raw_fitness(self, X, y,score_data,sample_weight):
        
        
    #     """ 
    #     根据分位数生成买卖信号
    #     x: np.array,shapes:[n] 
    #     up:分位数阈值上限,0-100
    #     down:分位数阈值下限,0-100
    #     period:分位数计算周期，不包括当前值
    #     """
    #     # with open(r'D:/Work/遗传算法测试/debug/test.pkl','wb') as file:
    #     #     pickle.dump([self.program,X],file)
    #     y_pred = self.execute(X)
    #     y_pred = y_pred.reshape(-1,)
    #     up,down,period = 80,20,60
    #     signal = np.ones_like(y_pred) * 0
    #     for i in range(period,len(y_pred)):
    #         p = stats.percentileofscore(y_pred[i - period : i],y_pred[i])
    #         if p > up:
    #             signal[i] = 1
    #         elif p < down:
    #             signal[i] = -1
    #         else:
    #             signal[i] = 0
            
    
    #     close = y
    #     fee,trade_delay = 0.003,1
        
    #     """ 
    #     策略回测打分
    #     signal: 每日信号,np.array,shapes:[n] 
    #     close:每日收盘价,np.array,shapes:[n] 
    #     fee:手续费，双边
    #     trade_delay:交易延迟天数，默认为1，当天计算信号，第二天以收盘价成交
    #     """
        
    #     n = len(signal)
    #     pos_array = np.ones_like(signal) * 0
    #     r_array = np.ones_like(signal)
    #     trade_array = np.ones_like(signal) * 0  
        
    #     last_high = -np.inf
    #     max_lose = 0
    #     lose_index = [0,0]
        
    #     trade_record = [[],[]]
    #     hold_record = [[],[]]
    #     for i in range(trade_delay,n):
    #         pos_array[i] = signal[i - trade_delay]
    #         trade = abs(pos_array[i] - pos_array[i - 1])
    #         r_array[i] = (close[i] / close[i - 1] - 1) * pos_array[i - 1]
    #         r_array[i] = (1 + r_array[i] - (trade * fee * 0.5)) * r_array[i - 1]
            
    #         trade_array[i] = trade
    #         if i < n - trade_delay:
                
    #             if pos_array[i] != 0 and pos_array[i - 1] == 0:#新开仓
    #                 last_open_index = i
    #                 last_direction = pos_array[i]
    #             elif pos_array[i] != pos_array[i - 1]:#平仓或反手
    #                 if last_direction == 1:
    #                     trade_record[0].append(close[i] / close[last_open_index] - 1 - fee)
    #                     hold_record[0].append(i - last_open_index)
    #                 else:
    #                     trade_record[1].append(-(close[i] / close[last_open_index] - 1) - fee)
    #                     hold_record[1].append(i - last_open_index)
    #                 if pos_array[i] != 0:
    #                     last_open_index = i
    #                     last_direction = pos_array[i]
                    
                        
                
    #         if r_array[i] > last_high:
    #             last_high = r_array[i]
    #             lose_index[0] = i
    #         temp_r = r_array[i] / last_high - 1
    #         if temp_r < max_lose:
    #             max_lose = temp_r
    #             lose_index[1] = i
        
    #     if abs(max_lose) < 0.001:
    #         r_l = 100
    #     else:
    #         r_l = -((r_array[-1] / r_array[0]) ** (252 / n) - 1) / max_lose
    #     score_list = [r_l]
        
    #     trade_n = np.sum(trade_array) / (n / 252)
    #     score_list.append(trade_n)
    #     win_n = len(trade_record[0])
    #     lose_n = len(trade_record[1])
    #     if win_n + lose_n == 0:
    #         win_ratio = 0
    #     else:
    #         win_ratio = win_n / (win_n + lose_n)
        
    #     score_list.append(win_ratio)
        
    #     if len(hold_record[0]) == 0:
    #         hold_avg = 0
    #     else:
    #         hold_avg = np.mean(hold_record[0])
    #     score_list.append(hold_avg)
        
    #     final_score = score_list[0] * (score_list[1] ** 0.5) * score_list[2] * (score_list[3] ** 0.5)
    #     final_score = max(0,final_score)
        
    #     # if final_score >= 5.8:
    #     #     with open(r'D:/Work/遗传算法测试/debug/test3.pkl','wb') as file:
    #     #         pickle.dump([X,y_pred,close,fee,final_score],file)
    #     return final_score   

    
    
    
    
    
    # def fitness(self, parsimony_coefficient=None):
    #     """Evaluate the penalized fitness of the program according to X, y.

    #     Parameters
    #     ----------
    #     parsimony_coefficient : float, optional
    #         If automatic parsimony is being used, the computed value according
    #         to the population. Otherwise the initialized value is used.

    #     Returns
    #     -------
    #     fitness : float
    #         The penalized fitness of the program.

    #     """
    #     if parsimony_coefficient is None:
    #         parsimony_coefficient = self.parsimony_coefficient
    #     penalty = parsimony_coefficient * len(self.program) * self.metric.sign
    #     return self.raw_fitness_ - penalty
    
    def fitness(self, parsimony_coefficient=None):
        """Evaluate the penalized fitness of the program according to X, y.

        Parameters
        ----------
        parsimony_coefficient : float, optional
            If automatic parsimony is being used, the computed value according
            to the population. Otherwise the initialized value is used.

        Returns
        -------
        fitness : float
            The penalized fitness of the program.

        """
        if isinstance(parsimony_coefficient,str):#自定义惩罚系数
            mode = parsimony_coefficient.split('_')
            # print(mode)
            if mode[0] == 'fixed':
                up = float(mode[2])
                low = float(mode[1])
                mul = float(mode[3])
                p = float(mode[4])
                # penalty = max(0,max(len(self.program) * p,np.exp(len(self.program) - low)/ (up - low) * mul) - 1)
                penalty = max(np.exp((len(self.program) - low) / (up - low) * low) - 1, 0) * mul
                penalty = min(penalty,len(self.program) * p)
                # penalty = max(len(self.program) * p, np.exp(len(self.program) - low) / (up - low) * mul) - 1
                return self.raw_fitness_ - penalty 
        
            
        else:
            # if parsimony_coefficient is None or isinstance(parsimony_coefficient,float):
            if parsimony_coefficient is None:
                parsimony_coefficient = self.parsimony_coefficient
            penalty = parsimony_coefficient * len(self.program) * self.metric.sign
        # print(self.raw_fitness_,penalty)
        return self.raw_fitness_ - penalty
    
    
    

    def get_subtree(self, random_state, program=None):
        """Get a random subtree from the program.

        Parameters
        ----------
        random_state : RandomState instance
            The random number generator.

        program : list, optional (default=None)
            The flattened tree representation of the program. If None, the
            embedded tree in the object will be used.

        Returns
        -------
        start, end : tuple of two ints
            The indices of the start and end of the random subtree.

        """
        if program is None:
            program = self.program
        # Choice of crossover points follows Koza's (1992) widely used approach
        # of choosing functions 90% of the time and leaves 10% of the time.
        probs = np.array([0.9 if isinstance(node, _Function) else 0.1
                          for node in program])
        probs = np.cumsum(probs / probs.sum())
        start = np.searchsorted(probs, random_state.uniform())

        stack = 1
        end = start
        while stack > end - start:
            node = program[end]
            if isinstance(node, _Function):
                stack += node.arity
            end += 1

        return start, end

    def reproduce(self):
        """Return a copy of the embedded program."""
        return copy(self.program)

    def crossover(self, donor, random_state):
        """Perform the crossover genetic operation on the program.

        Crossover selects a random subtree from the embedded program to be
        replaced. A donor also has a subtree selected at random and this is
        inserted into the original parent to form an offspring.

        Parameters
        ----------
        donor : list
            The flattened tree representation of the donor program.

        random_state : RandomState instance
            The random number generator.

        Returns
        -------
        program : list
            The flattened tree representation of the program.

        """
        # Get a subtree to replace
        start, end = self.get_subtree(random_state)
        removed = range(start, end)
        # Get a subtree to donate
        donor_start, donor_end = self.get_subtree(random_state, donor)
        donor_removed = list(set(range(len(donor))) -
                             set(range(donor_start, donor_end)))
        # Insert genetic material from donor
        return (self.program[:start] +
                donor[donor_start:donor_end] +
                self.program[end:]), removed, donor_removed

    def subtree_mutation(self, random_state):
        """Perform the subtree mutation operation on the program.

        Subtree mutation selects a random subtree from the embedded program to
        be replaced. A donor subtree is generated at random and this is
        inserted into the original parent to form an offspring. This
        implementation uses the "headless chicken" method where the donor
        subtree is grown using the initialization methods and a subtree of it
        is selected to be donated to the parent.

        Parameters
        ----------
        random_state : RandomState instance
            The random number generator.

        Returns
        -------
        program : list
            The flattened tree representation of the program.

        """
        # Build a new naive program
        chicken = self.build_program(random_state)
        # Do subtree mutation via the headless chicken method!
        return self.crossover(chicken, random_state)

    def hoist_mutation(self, random_state):
        """Perform the hoist mutation operation on the program.

        Hoist mutation selects a random subtree from the embedded program to
        be replaced. A random subtree of that subtree is then selected and this
        is 'hoisted' into the original subtrees location to form an offspring.
        This method helps to control bloat.

        Parameters
        ----------
        random_state : RandomState instance
            The random number generator.

        Returns
        -------
        program : list
            The flattened tree representation of the program.

        """
        # Get a subtree to replace
        start, end = self.get_subtree(random_state)
        subtree = self.program[start:end]
        # Get a subtree of the subtree to hoist
        sub_start, sub_end = self.get_subtree(random_state, subtree)
        hoist = subtree[sub_start:sub_end]
        # Determine which nodes were removed for plotting
        removed = list(set(range(start, end)) -
                       set(range(start + sub_start, start + sub_end)))
        return self.program[:start] + hoist + self.program[end:], removed

    # def point_mutation(self, random_state):
    #     """Perform the point mutation operation on the program.

    #     Point mutation selects random nodes from the embedded program to be
    #     replaced. Terminals are replaced by other terminals and functions are
    #     replaced by other functions that require the same number of arguments
    #     as the original node. The resulting tree forms an offspring.

    #     Parameters
    #     ----------
    #     random_state : RandomState instance
    #         The random number generator.

    #     Returns
    #     -------
    #     program : list
    #         The flattened tree representation of the program.

    #     """
    #     program = copy(self.program)

    #     # Get the nodes to modify
    #     mutate = np.where(random_state.uniform(size=len(program)) <
    #                       self.p_point_replace)[0]

    #     for node in mutate:
    #         if isinstance(program[node], _Function):
    #             arity = program[node].arity
    #             # Find a valid replacement with same arity
    #             replacement = len(self.arities[arity])
    #             replacement = random_state.randint(replacement)
    #             replacement = self.arities[arity][replacement]
    #             program[node] = replacement
    #         else:
    #             # We've got a terminal, add a const or variable
    #             if self.const_range is not None:
    #                 terminal = random_state.randint(self.n_features + 1)
    #             else:
    #                 terminal = random_state.randint(self.n_features)
    #             if terminal == self.n_features:
    #                 terminal = random_state.uniform(*self.const_range)
    #                 if self.const_range is None:
    #                     # We should never get here
    #                     raise ValueError('A constant was produced with '
    #                                       'const_range=None.')
    #             program[node] = terminal

    #     return program, list(mutate)

    depth_ = property(_depth)
    length_ = property(_length)
    indices_ = property(_indices)
    
    def point_mutation(self, random_state):
        """Perform the point mutation operation on the program.
    
        Point mutation selects random nodes from the embedded program to be
        replaced. Terminals are replaced by other terminals and functions are
        replaced by other functions that require the same number of arguments
        as the original node. The resulting tree forms an offspring.
    
        Parameters
        ----------
        random_state : RandomState instance
            The random number generator.
    
        Returns
        -------
        program : list
            The flattened tree representation of the program.
    
        """
        program = copy(self.program)
    
        # Get the nodes to modify
        mutate = np.where(random_state.uniform(size=len(program)) <
                          self.p_point_replace)[0]
    
        for node in mutate:
            mutated = False
            if isinstance(program[node], _Function):
                arity = program[node].arity
                # 新增条件
                if arity != 0:
                    # Find a valid replacement with same arity
                    replacement = len(self.arities[arity])
                    replacement = random_state.randint(replacement)
                    replacement = self.arities[arity][replacement]
                    if replacement.is_ts:
                        replacement = make_ts_function(replacement, self.d_ls, random_state)
                    program[node] = replacement
                    # 新增
                    mutated = True
            if not mutated:
                # We've got a terminal, add a const or variable
                if self.const_range is not None:
                    # terminal = random_state.randint(self.n_features + 1)
                    terminal = random_state.randint(self.n_features + len(self.fixed_function_set) + 1)
                else:
                    # terminal = random_state.randint(self.n_features)
                    terminal = random_state.randint(self.n_features + len(self.fixed_function_set))
                # if terminal == self.n_features:
                if terminal == self.n_features + len(self.fixed_function_set):
                    terminal = random_state.uniform(*self.const_range)
                    # print('const:',terminal,self.const_range)
                    if self.const_range is None:
                        # We should never get here
                        raise ValueError('A constant was produced with '
                                         'const_range=None.')
                    # 新增
                    program[node] = terminal
                # 新增
                elif terminal >= self.n_features:
                    replacement = self.fixed_function_set[terminal - self.n_features]
                    replacement = make_ts_function(replacement, self.d_ls, random_state)
                    program[node] = replacement
                else:
                    program[node] = terminal
    
        return program, list(mutate)
    
    
