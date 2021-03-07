class Parent():
    def __init__(self):
        pass

    def set_address(self, address):
        self.address = address


class Child(Parent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


child = Child()
child.set_address('Iowa')

print(child.address)
