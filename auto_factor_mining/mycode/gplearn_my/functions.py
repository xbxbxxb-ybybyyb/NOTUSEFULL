
import numpy as np
from joblib import wrap_non_picklable_objects

__all__ = ['make_function']

from xquant.factordata import FactorData
s = FactorData()
stock_list = list(s.hset('MARKET','20220725','ALLA')['stock'])

class _Function(object):

    """A representation of a mathematical relationship, a node in a program.

    This object is able to be called with NumPy vectorized arguments and return
    a resulting vector based on a mathematical relationship.

    Parametersok
    ----------
    function : callable
        A function with signature function(x1, *args) that returns a Numpy
        array of the same shape as its arguments.

    name : str
        The name for the function as it should be represented in the program
        and its visualizations.

    arity : int
        The number of arguments that the ``function`` takes.

    """

    def __init__(self, function, name, arity, parameter_pair_list=[]):
        self.function = function
        self.name = name
        self.arity = arity  # 个数
        self.parameter_pair_list = parameter_pair_list

        for para_pair in parameter_pair_list:
            # if para_pair[0] == "ALL":
            #     assert len(para_pair) == 1
            # else:
            assert len(para_pair) == arity + 1

            for element in para_pair:
                assert element in set(["PCT", "VALUE", "VOLUME", "PRICE"])



    # TODO 这里可以直接加入？？？
    def __call__(self, *args):
        return self.function(*args)


def make_function(function, name, arity, wrap=True, parameter_pair_list=[]):

# arr3=2.5 * np.random.randn(2,4)+3 
    """Make a function node, a representation of a mathematical relationship.

    This factory function creates a function node, one of the core nodes in any
    program. The resulting object is able to be called with NumPy vectorized
    arguments and return a resulting vector based on a mathematical
    relationship.

    Parameters
    ----------
    function : callable
        A function with signature `function(x1, *args)` that returns a Numpy
        array of the same shape as its arguments.

    name : str
        The name for the function as it should be represented in the program
        and its visualizations.

    arity : int
        The number of arguments that the `function` takes.

    wrap : bool, optional (default=True)
        When running in parallel, pickling of custom functions is not supported
        by Python's default pickler. This option will wrap the function using
        cloudpickle allowing you to pickle your solution, but the evolution may
        run slightly more slowly. If you are running single-threaded in an
        interactive Python session or have no need to save the model, set to
        `False` for faster runs.

    """



    if not isinstance(arity, int):
        raise ValueError('arity must be an int, got %s' % type(arity))
    if not isinstance(function, np.ufunc):
        if function.__code__.co_argcount != arity:
            raise ValueError('arity %d does not match required number of '
                             'function arguments of %d.'
                             % (arity, function.__code__.co_argcount))
    if not isinstance(name, str):
        raise ValueError('name must be a string, got %s' % type(name))
    if not isinstance(wrap, bool):
        raise ValueError('wrap must be an bool, got %s' % type(wrap))

    # Check output shape -> 如果有mode的话，加不进去？
    # TODO 这里的10改成stock list ALL_HIST
    smaple_number = len(stock_list) * 2 # 2天 * # stock
    # args = [np.ones(10) for _ in range(arity)]

    # if "ts_corr" in name:
    #     pass
    if True:
        pass
    else:
        args = [np.ones(smaple_number) for _ in range(arity)]
        try:
            function(*args)
        except ValueError:
            raise ValueError('supplied function %s does not support arity of %d.'
                            % (name, arity))
        if not hasattr(function(*args), 'shape'):
            raise ValueError('supplied function %s does not return a numpy array.'
                            % name)
        if function(*args).shape != (smaple_number,):
            raise ValueError('supplied function %s does not return same shape as '
                            'input vectors.' % name)

        # Check closure for zero & negative input arguments
        args = [np.zeros(smaple_number) for _ in range(arity)]
        if not np.all(np.isfinite(function(*args))):
            raise ValueError('supplied function %s does not have closure against '
                            'zeros in argument vectors.' % name)
        args = [-1 * np.ones(smaple_number) for _ in range(arity)]
        if not np.all(np.isfinite(function(*args))):
            raise ValueError('supplied function %s does not have closure against '
                            'negatives in argument vectors.' % name)



    if wrap:
        return _Function(function=wrap_non_picklable_objects(function),
                         name=name,
                         arity=arity,
                        parameter_pair_list=parameter_pair_list)
    return _Function(function=function,
                     name=name,
                     arity=arity,
                     parameter_pair_list=parameter_pair_list)


# def _protected_division(x1, x2):
#     """Closure of division (x1/x2) for zero denominator."""
#     with np.errstate(divide='ignore', invalid='ignore'):
#         return np.where(np.abs(x2) > 0.00001, np.divide(x1, x2), 1.)


# def _protected_sqrt(x1):
#     """Closure of square root for negative arguments."""
#     return np.sqrt(np.abs(x1))


# def _protected_log(x1):
#     """Closure of log for zero arguments."""
#     with np.errstate(divide='ignore', invalid='ignore'):
#         return np.where(np.abs(x1) > 0.001, np.log(np.abs(x1)), 0.)


# def _protected_inverse(x1):
#     """Closure of log for zero arguments."""
#     with np.errstate(divide='ignore', invalid='ignore'):
#         return np.where(np.abs(x1) > 0.001, 1. / x1, 0.)
def _sign(x):
    return np.where(x>0, np.sign(1+x), np.sign(x))


def _trans_x(x):
    # sign(x) * 1.5^abs(x) - 0.5*sign(x)
    return np.where(x == 0, 0.5, _sign(x)*np.power(1.5,np.abs(x))-0.5*_sign(x))

def _protected_division(x1, x2):
    """Closure of division (x1/x2) for zero denominator."""
    x1 = np.nan_to_num(x1)
    x2 = np.nan_to_num(x2)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.abs(x2) > 1.0, np.divide(x1, x2), np.divide(x1, _trans_x(x2)))

def _protected_division3(x1, x2):
    """用序列最小值的非0值来代替空值和0"""
    threshold1 = min(abs(x1[np.nonzero(x1)]))
    x1 = np.nan_to_num(x1)
    x1 = np.where(np.abs(x1) > threshold1, x1, _sign(x1) * threshold1)

    threshold2 = min(abs(x2[np.nonzero(x2)]))
    x2 = np.nan_to_num(x2)
    x2 = np.where(np.abs(x2) > threshold1, x2, _sign(x2) * threshold2)   
    return np.divide(x1, x2)

def _protected_sqrt(x1):
    """Closure of square root for negative arguments."""
    return _sign(x1)*np.sqrt(np.abs(x1))

def _protected_log(x1):
    """Closure of log for zero arguments."""
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.abs(x1) > 1.0, 
                        _sign(x1)*np.log(np.abs(x1))+_sign(x1)*np.abs(np.log(0.5)), 
                        _sign(x1)*np.log(_trans_x(np.abs(x1)))+_sign(x1)*np.abs(np.log(0.5)))

def _protected_inverse(x1):
    """Closure of log for zero arguments."""
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.abs(x1) > 1.0, 1. / x1, 1./_trans_x(x1))

def _sigmoid(x1):
    """Special case of logistic function to transform to probabilities."""
    with np.errstate(over='ignore', under='ignore'):
        return 1 / (1 + np.exp(-x1))


add2 = _Function(function=np.add, name='add', arity=2, parameter_pair_list=[("PRICE","PRICE","PRICE"),
                                                     ("VOLUME","VOLUME","VOLUME"),
                                                     ("VALUE","VALUE","VALUE"),
                                                     ("PCT", "PCT", "PCT")])

sub2 = _Function(function=np.subtract, name='sub', arity=2,parameter_pair_list=[("PRICE","PRICE","PRICE"),
                                                     ("VOLUME","VOLUME","VOLUME"),
                                                     ("VALUE","VALUE","VALUE"),
                                                      ("PCT", "PCT", "PCT")])

mul2 = _Function(function=np.multiply, name='mul', arity=2,parameter_pair_list=[("PRICE","VOLUME","VALUE"),
                                                     ("PRICE","PRICE","PRICE"),
                                                     ("VOLUME","VOLUME","VOLUME"),
                                                     ("VALUE","VALUE","VALUE"),
                                                     ("PCT", "PCT", "PCT"),
                                                     ("PRICE", "PCT", "PRICE"),
                                                     ("VOLUME", "PCT", "VOLUME"),
                                                     ("VALUE", "PCT", "VALUE")])

div2 = _Function(function=_protected_division, name='div', arity=2,parameter_pair_list=[
                                                              ("PRICE","PRICE","PCT"),
                                                              ("VOLUME","VOLUME","PCT"),
                                                              ("VALUE","VALUE","PCT"),
                                                              ("VALUE","PRICE","VOLUME"),
                                                              ("VALUE","VOLUME","PRICE"),
                                                              ("PCT", "PCT", "PCT"),
                                                              ("PRICE", "PCT", "PRICE"),
                                                              ("VOLUME", "PCT", "VOLUME"),
                                                              ("VALUE", "PCT", "VALUE")])

div3 = _Function(function=_protected_division3, name='div3', arity=2,parameter_pair_list=[
                                                              ("PRICE","PRICE","PCT"),
                                                              ("VOLUME","VOLUME","PCT"),
                                                              ("VALUE","VALUE","PCT"),
                                                              ("VALUE","PRICE","VOLUME"),
                                                              ("VALUE","VOLUME","PRICE"),
                                                               ("PCT", "PCT", "PCT"),
                                                            ("PRICE", "PCT", "PRICE"),
                                                            ("VOLUME", "PCT", "VOLUME"),
                                                            ("VALUE", "PCT", "VALUE")])


all_list = [("PRICE", "PRICE"),
                    ("VOLUME", "VOLUME"),
                    ("PCT", "PCT"),
                    ("VALUE", "VALUE")]


sqrt1 = _Function(function=_protected_sqrt, name='sqrt', arity=1,parameter_pair_list=all_list)
log1 = _Function(function=_protected_log, name='log', arity=1,parameter_pair_list=all_list)
neg1 = _Function(function=np.negative, name='neg', arity=1,parameter_pair_list=all_list)
inv1 = _Function(function=_protected_inverse, name='inv', arity=1,parameter_pair_list=all_list)
abs1 = _Function(function=np.abs, name='abs', arity=1,parameter_pair_list=all_list)


max2 = _Function(function=np.maximum, name='max', arity=2,parameter_pair_list=[("PRICE","PRICE","PRICE"),
                                                     ("VOLUME","VOLUME","VOLUME"),
                                                     ("VALUE","VALUE","VALUE"),
                                                     ("PCT", "PCT", "PCT")])

min2 = _Function(function=np.minimum, name='min', arity=2,parameter_pair_list=[("PRICE","PRICE","PRICE"),
                                                     ("VOLUME","VOLUME","VOLUME"),
                                                     ("VALUE","VALUE","VALUE"),
                                                      ("PCT", "PCT", "PCT")])


sin1 = _Function(function=np.sin, name='sin', arity=1,parameter_pair_list=all_list)
cos1 = _Function(function=np.cos, name='cos', arity=1,parameter_pair_list=all_list)
tan1 = _Function(function=np.tan, name='tan', arity=1,parameter_pair_list=all_list)
sig1 = _Function(function=_sigmoid, name='sig', arity=1,parameter_pair_list=all_list)

_function_map = {'add': add2,
                 'sub': sub2,
                 'mul': mul2,
                 'div': div2,
                 'div3':div3,
                 'sqrt': sqrt1,
                 'log': log1,
                 'abs': abs1,
                 'neg': neg1,
                 'inv': inv1,
                 'max': max2,
                 'min': min2,
                 'sin': sin1,
                 'cos': cos1,
                 'tan': tan1,
                 "sig": sig1}
