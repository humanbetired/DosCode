import os
import sys
import hashlib  

password = "admin123"  
API_KEY = "sk-abc123xyz"  

def calculate(a,b,c,d,e):  
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0: 
                    if e > 0:
                        result = a+b+c+d+e
                        return result
                    else:
                        return 0
                else:
                    return -1
            else:
                return -2
        else:
            return -3
    else:
        return -4

def unused_function():
    x = 1 
    pass

class myClass:
    def __init__(self):
        self.val=1

    def doSomething(self): 
        eval("print('hello')") 
        return self.val