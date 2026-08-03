---
title: Learning
date: 2026-08-03
emoji: 🐍
theme: Learning
tags: [Python]
excerpt: Learning Python for a university course this autumn. My summer project became a one-page Python cheat sheet I can use.
---

I'm starting a 10-credit programming course at university this autumn as part of my continuous learning. Although I've done some programming before, I wanted to be as prepared as possible before classes start.

During my summer vacation, I spent some time refreshing my Python skills. I worked through small projects and collected notes on Python syntax from different online resources. Having everything in one place made it much easier to look things up while coding.

As the notes grew, I challenged myself to fit everything onto a single double-sided A4 page. After reducing the font to size 8 and using four columns, I actually managed it! It's about the smallest text my 40+ year-old eyes can comfortably read, but it makes for a handy quick reference.

I've included the cheat sheet below. Hopefully, someone else will find it useful too. The cheat sheet is based on notes and examples from various online resources. One of the best references I found is the excellent **Python Cheat Sheets** from [Real Python](https://realpython.com/cheatsheets/python/).

# Python Cheat Sheet

> **Note**
> This is my personal Python cheat sheet, compiled from various online learning resources.
> I use it as a quick reference while working on small projects and learning Python. :contentReference[oaicite:0]{index=0}

---

## Data Types

### Type Investigation

```python
type(42)                 # <class 'int'>
type(3.14)               # <class 'float'>
type("Hello")            # <class 'str'>
type(True)               # <class 'bool'>
type(None)               # <class 'NoneType'>

isinstance(3.14, float)  # True
issubclass(int, object)  # True
```

### Type Conversion

```python
int("42")
float("3.14")
str(42)
bool(1)
list("abc")
```

---

## Variables & Assignment

### Basic Assignment

```python
name = "Leo"
age = 7
height = 5.6
is_cat = True
flaws = None
```

### Multiple Assignment

```python
x, y = 10, 20
a = b = c = 0
```

### Augmented Assignment

```python
counter += 1
numbers += [4, 5]
permissions |= write
```

---

## Strings

### Notes

- `\n` creates a new line.
- `\\` writes a backslash.

### Creating Strings

```python
single = 'Hello'
double = "World"

multi = """Multiple
line string"""
```

### Operations

```python
"me" + "ow!"
"Meow!" * 3

len("Python")
```

### Useful Methods

```python
"a".upper()
"A".lower()
" a ".strip()
"abc".replace("bc", "ha")
"a b".split()
"-".join(["a", "b"])
```

### Slicing

```python
text = "Python"

text[0]
text[-1]
text[1:4]
text[:3]
text[3:]
text[::2]
text[::-1]
```

### f-Strings

```python
name = "Aubrey"
age = 2

f"Hello, {name}!"
f"{name} is {age} years old"
f"Debug: {age=}"
```

---

## Numbers & Math

```python
10 + 3
10 - 3
10 * 3
10 / 3
10 // 3
10 % 3
2 ** 3
```

Useful functions:

```python
abs(-5)
round(3.14159, 2)
min(3, 1, 2)
max(3, 1, 2)
sum([1, 2, 3])
```

---

## Conditionals

```python
if age < 13:
    category = "child"
elif age < 20:
    category = "teenager"
else:
    category = "adult"
```

```python
x == y
x != y
x < y
x <= y
x > y
x >= y
```

```python
if age >= 18 and has_car:
    print("Roadtrip!")

if is_weekend or is_holiday:
    print("No work today.")

if not is_raining:
    print("You can go outside.")
```

---

## Loops

```python
for i in range(5):
    print(i)
```

```python
for fruit in fruits:
    print(fruit)
```

```python
for i, fruit in enumerate(fruits):
    print(i, fruit)
```

```python
while True:
    user_input = input()

    if user_input == "quit":
        break
```

---

## Functions

```python
def greet():
    return "Hello!"
```

```python
def greet_person(name):
    return f"Hello, {name}!"
```

```python
def add(x, y=10):
    return x + y
```

```python
square = lambda x: x**2
```

---

## Classes

```python
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name} says Woof!"
```

---

## Exceptions

```python
try:
    number = int(input())

except ValueError:
    print("Invalid number")

except ZeroDivisionError:
    print("Cannot divide by zero")

else:
    print(result)

finally:
    print("Finished")
```

---

## Collections

### Lists

```python
nums = [1, 2, 3]

nums.append(4)
nums.pop()
nums.remove(2)
```

### Tuples

```python
point = (3, 4)

x, y = point
```

### Sets

```python
a = {1, 2, 3}
b = {3, 4, 5}

a | b
a & b
a - b
a ^ b
```

### Dictionaries

```python
pet = {
    "name": "Leo",
    "age": 7
}

pet["sound"] = "Purr"

pet.keys()
pet.values()
pet.items()
```

---

## Comprehensions

```python
squares = [x**2 for x in range(10)]

evens = [x for x in range(20) if x % 2 == 0]

word_lengths = {
    word: len(word)
    for word in ["hello", "world"]
}
```

---

## Imports

```python
import math

from math import sqrt

import numpy as np
```

---

## File I/O

```python
with open("file.txt", "r", encoding="utf-8") as file:
    content = file.read()
```

```python
with open("output.txt", "w", encoding="utf-8") as file:
    file.write("Hello, World!\n")
```

```python
with open("log.txt", "a", encoding="utf-8") as file:
    file.write("New log entry\n")
```