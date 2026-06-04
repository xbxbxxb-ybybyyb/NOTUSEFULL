import pandas as pd
import line_profiler
import memory_profiler

# pd.set_option('display.max_columns', None)

import functools
import gc
import itertools
import sys
from timeit import default_timer as _timer


def timeit(_func=None, repeat=1, number=1, file=sys.stdout):
    _repeat = functools.partial(itertools.repeat, None)

    def wrap(func):
        @functools.wraps(func)
        def _timeit(*args, **kwargs):
            # Temporarily turn off garbage collection during the timing.
            # Makes independent timings more comparable.
            # If it was originally enabled, switch it back on afterwards.
            gcold = gc.isenabled()
            gc.disable()
            try:
                # Outer loop - the number of repeats.
                trials = []
                for _ in _repeat(repeat):
                    # Inner loop - the number of calls within each repeat.
                    total = 0
                    for _ in _repeat(number):
                        start = _timer()
                        result = func(*args, **kwargs)
                        end = _timer()
                        total += end - start
                    trials.append(total)

                best = min(trials) / number
                print(
                    "Best of {} trials with {} function"
                    " calls per trial:".format(repeat, number)
                )
                print(
                    "Function `{}` ran in average"
                    " of {:0.3f} seconds.".format(func.__name__, best),
                    end="\n\n",
                    file=file,
                )
            finally:
                if gcold:
                    gc.enable()
            # Result is returned *only once*
            return result

        return _timeit

    # Syntax trick from Python @dataclass
    if _func is None:
        return wrap
    else:
        return wrap(_func)


def profile(_func=None, target='time', file=sys.stdout):
    # target 'time'监测运行时间，'memery'监测运行占用内存
    if target not in ['time', 'memery']:
        raise Exception("【target参数】'time'监测运行时间，'memery'监测运行占用内存！")

    def wrap(func):
        @functools.wraps(func)
        def _profile(*args, **kwargs):
            # Temporarily turn off garbage collection during the timing.
            # Makes independent timings more comparable.
            # If it was originally enabled, switch it back on afterwards.
            gcold = gc.isenabled()
            gc.disable()
            try:
                if target == 'time':
                    profile = line_profiler.LineProfiler(func)
                    profile.enable()
                    result = func(*args, **kwargs)
                    profile.disable()
                    profile.print_stats(file)
                else:
                    profile = memory_profiler.LineProfiler()
                    profile.add_function(func)
                    profile.enable()
                    result = func(*args, **kwargs)
                    profile.disable()
                    memory_profiler.show_results(profile, stream=file)
            finally:
                if gcold:
                    gc.enable()
            # Result is returned *only once*
            return result

        return _profile

    # Syntax trick from Python @dataclass
    if _func is None:
        return wrap
    else:
        return wrap(_func)
