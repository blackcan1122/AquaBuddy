from dataclasses import dataclass
from typing import Optional

@dataclass
class Vector2():
    X: Optional[float] = None
    Y: Optional[float] = None

class MyBaseClass():
    
    def __init__(self):
        print("Base Class is initialized")
        self._velocity = Vector2()
        pass


class MyDerivedClass(MyBaseClass):
    def __init__(self):
        super().__init__()
        print(self._velocity.X)
        
if __name__ == "__main__":
    myobj = MyDerivedClass()
    