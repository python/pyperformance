"""
Benchmark to measure performance of the python builtin method copy.deepcopy

Performance is tested on a nested dictionary and a dataclass

Author: Pieter Eendebak

"""
import copy
import pyperf
from dataclasses import dataclass

@dataclass
class A:
    string : str
    lst : list
    boolean : bool
    

def benchmark(n):
    a={'list': [1,2,3,43], 't': (1,2,3), 'str': 'hello', 'subdict': {'a': True}}
    dc=A('hello', [1,2,3], True)
    
    for ii in range(n):
        
        for jj in range(60):
            _ = copy.deepcopy(a)
            
        for s in ['red', 'blue', 'green']:
            dc.string = s
            for ii in range(10):
                dc.lst[0] = ii
                for b in [True, False]:
                    dc.boolean=b
                    _ = copy.deepcopy(dc)
                

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "deepcopy benchmark"

    runner.bench_func('deepcopy', benchmark, 200)
