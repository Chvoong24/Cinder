# Style Guide 
## Tabs
Use tabs for indenting functions and to show which function a line of code belongs to
### Example   
 ```python
def Walking(stepsAmnt):
    for steps in range(10):
        leftFoot()
        rightFood()
```

## Indentation
Implied line continuation should align wrapped elements vertically, or use a hanging 4-space indent. Closing (round, square or curly) brackets can be placed at the end of the expression or on a separate line. They should be in line with the first non-whitespace character of the last line of list, or under the first character of the line that starts the multiline construct
*See https://google.github.io/styleguide/pyguide.html#s3.4-indentation*

### Example
```python
foo = makeALongFunctionName(varOne, varTwo,
                            varThree, varFour)
meal = (spam,
        beans)

foo = makeALongFunctionName(
          varOne, varTwo,
          varThree, varFour
          )

meal = (
    spam,
    beans
    )
```

## Whitespace
Follow standard typographic rules for the use of spaces around punctuation. 
*See https://google.github.io/styleguide/pyguide.html#s3.6-whitespace*


## Naming Variables & Functions
We are using nouns for variables and verbs for functions as well as camelCase. We will also use fully capitalized names for global variables.

### Example
```python
MAXPROB = 100
daysSinceLastRainFall = 4
def calculateRainProbabilityInPercent(daysSinceLastRain):
    # some fancy stastical analysis
    rainProbPercent = 15
    return rainProbPercent
```

##  Docstrings For Documentation
We are using Docstrings to "automatically" build our documentation for this codebase  
### Example
```python
def Walking(stepsAmnt):
    """Moves the sprite's left and right feet 10 times."""
    for steps in range(10):
        leftFoot()
        rightFood()
```

## Comments
Have simple comments when explaining code or as a reminder
### Example
```python
# Does addition of two ints
def add(int1: int, int2: int) -> int:
    """Returns the sum of two ints as an int"""
    return int1 + int2
```

### Remove extraneous print statements when finished debugging



