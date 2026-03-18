

class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_name(self):
        return self.name

# 1. Create an instance (object) of the Dog class first
my_dog = Dog("Azor", 3) 

# 2. Now you can call the method on that specific dog
print(my_dog.get_name())


# The issue is that you are trying to call
# get_name directly on the class instead of creating an instance (an object) of the dog first.
# In Python, the __init__ method requires you to provide the name and age when you create the dog. Here is the corrected way to write it:

# Why your version failed:
#
#     Missing Instance: Dog.get_name("Azor") tells Python to look for a function inside the blueprint, but it doesn't know which dog's name to get.
#     The self argument: Methods inside a class automatically take self as the first argument, which represents the specific object you created.
#     Missing Arguments: Your __init__ method requires both a name and an age, so you must provide both when creating the dog.
#
# Would you like to see how to use a @classmethod or @staticmethod if you want to call functions without creating a dog instance first?


# To call functions without creating a specific dog instance, you use
# decorators like @classmethod and @staticmethod. These tell Python that the method doesn't need the standard self argument.

# 1. @classmethod (Accesses Class Data)
# Use this when you need to access something that belongs to the entire "Dog" category, like a shared species name. It takes cls as its first argument instead of self.

class Dog:
    species = "Canis familiaris"  # Shared by all dogs

    @classmethod
    def get_species(cls):
        return cls.species

# Call directly on the class
print(Dog.get_species())


# 2. @staticmethod (Utility Functions)
# Use this for functions that belong logically in the Dog class but don't need any data from the class or an instance. It doesn't take self or cls

class Dog:
    @staticmethod
    def bark_sound():
        return "Woof!"

# Call directly on the class
print(Dog.bark_sound())

# 3. "Factory" Methods (Advanced Use)
# A very common use for @classmethod is creating a "factory" to make a dog in a special way (e.g., from a birth year).
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def from_birth_year(cls, name, birth_year):
        import datetime
        age = datetime.date.today().year - birth_year
        return cls(name, age) # This creates and returns a new Dog

# Create a dog without calling __init__ directly
new_dog = Dog.from_birth_year("Azor", 2020)
print(f"{new_dog.name} is {new_dog.age} years old.")

# Do you want to see how to use inheritance so you can make specific types of dogs like a Labrador?

# Inheritance allows you to create a new class that "takes" all the attributes and methods from an existing one
# . This is perfect for creating specialized versions of a general class, like a Labrador that is still a Dog.

# How to Implement Inheritance
# To make a class inherit from another, you pass the parent class name in parentheses during the child class definition.
#
#     super().__init__(): This special function calls the parent class's constructor, ensuring the child class properly sets up inherited attributes like name and age.
#     Unique Methods: You can add new methods to the child class that only that specific breed can do.

# The Parent Class
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def speak(self):
        return f"{self.name} says Woof!"

# The Child Class (Inherits from Dog)
class Labrador(Dog):
    def __init__(self, name, age, color):
        # 1. Use super() to handle name and age from the Dog class
        super().__init__(name, age)
        # 2. Add a new attribute unique to Labradors
        self.color = color

    # 3. Add a new method unique to Labradors
    def swim(self):
        return f"{self.name} is swimming in the lake!"

# Usage
my_lab = Labrador("Buddy", 5, "Golden")

print(my_lab.speak()) # Works! (Inherited from Dog)
print(my_lab.swim())  # Works! (Unique to Labrador)
print(f"{my_lab.name} is {my_lab.color}.")

# Key Concepts
#
#     Is-A Relationship: Use inheritance when you can say "A Labrador is a Dog".
#     Method Overriding: If you want the Labrador to speak differently, you can redefine def speak(self): inside the Labrador class to replace the version from the Dog class.
#     Code Reuse: You don't have to rewrite the name or age logic; the Labrador automatically gets it from Dog

# Would you like to see how to override a method so a Husky howls instead of barks?

# To override a method, you simply define a method in the child class with the exact same name as the one in the parent class. Python will prioritize the child's version.
# Here is how you make a Husky howl while a regular Dog barks:

class Dog:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} says: Woof!"

class Husky(Dog):
    # This overrides the speak method from the Dog class
    def speak(self):
        return f"{self.name} says: Awoooooo!"

# Let's see them in action
generic_dog = Dog("Rex")
snow_dog = Husky("Ghost")

print(generic_dog.speak()) # Output: Rex says: Woof!
print(snow_dog.speak())    # Output: Ghost says: Awoooooo!

# Why use Overriding?
#
#     Specialization: You keep the general structure (all dogs speak), but change the specific behavior for different types.
#     Polymorphism: You can have a list of different dogs and call .speak() on all of them; each will automatically use its own version of the sound.




