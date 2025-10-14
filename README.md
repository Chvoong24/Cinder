# Cinder
Project for COMP333
Chvoong24: Chris Voong
duyhuynh-dev: Duy Huynh
bentaffet: Ben Taffet
Hawklight1: Ben Mckinney
https://github.com/Chvoong24/Cinder/blob/main/StyleGuide.md


# Table Of Contents
- [StyleGuide](#style-guide)
    - [Branching](#branching)
- [How To Use](#how-to-use)
## How To Use
1. Go to specfic model you want to download
2. Run file
3. Files appear in (modelName_download)

## Style Guide
### Tabs
Use tabs for indenting functions and to show which function a line of code belongs to
### Example   
 ```python
def Walking(stepsAmnt):
    for steps in range(10):
        leftFoot()
        rightFood()
```

### Indentation
Implied line continuation should align wrapped elements vertically, or use a hanging 4-space indent. Closing (round, square or curly) brackets can be placed at the end of the expression or on a separate line. They should be in line with the first non-whitespace character of the last line of list, or under the first character of the line that starts the multiline construct
*See https://google.github.io/styleguide/pyguide.html#s3.4-indentation*

### Example
```python
foo = make_a_long_lunction_name(varOne, varTwo,
                            varThree, varFour)
meal = (spam,
        beans)

foo = make_a_long_lunction_name(
          varOne, varTwo,
          varThree, varFour
          )

meal = (
    spam,
    beans
    )
```

### Whitespace
Follow standard typographic rules for the use of spaces around punctuation. 
*See https://google.github.io/styleguide/pyguide.html#s3.6-whitespace*


### Naming Variables & Functions
We are using nouns for variables and verbs for functions. We will make use of snake case for functions and variables. We will also use fully capitalized names for global variables (with snake case where appropriate).

### Example
```python
MAXPROB = 100
daysSinceLastRainFall = 4
def calculate_rain_probability_in_percent(daysSinceLastRain):
    # some fancy stastical analysis
    rainProbPercent = 15
    return rainProbPercent
```

###  Docstrings For Documentation
We are using Docstrings to "automatically" build our documentation for this codebase  
#### Example
```python
def Walking(stepsAmnt):
    """Moves the sprite's left and right feet 10 times."""
    for steps in range(10):
        leftFoot()
        rightFood()
```

### Comments
Have simple comments when explaining code or as a reminder
### Example
```python
# Does addition of two ints
def add(int1: int, int2: int) -> int:
    """Returns the sum of two ints as an int"""
    return int1 + int2
```

### Remove extraneous print statements when finished debugging

### Branching
When branching, use short but descriptive noming clature, use snake_case for naming files and branches.
Always branch when making new features, work on small features.

#### Example
You are adding a new feature that takes input from the front-end and fetches the data based on the input.
```
main
|
|----Dev
      |
      |---front_fetch
```

When you are done with your branch, make a pull a request to Dev to see if there are any conflicts. If not, merge fully into Dev and delete the working branch.

```
main
|
|----Dev------------------------
      |                  |
      |---front_fetch----|
```
