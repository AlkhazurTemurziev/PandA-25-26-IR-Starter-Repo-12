# Part 12 - Starter

This last part builds on your Part 11 solution. There will be almost no instructions this time. You do not need
them anymore ☺️.

Your task is to add **normalization** and **stemming**, e.g., the Porter stemmer to the system. See the ToDos for a bit more detail.

## Run the app

``` bash
python -m part12.app
```

## What to implement (ToDos)
ToDo 0 is in `part12/models.py`. Normalization and stemming will most likely be implemented there as well.  
You may create new modules, classes, and functions and restructure the code as you see fit.

0. First, **copy/redo** your implementation from Part 11. Move your solution for the **four ToDos** to the `models.py` module.

1. **Add stemming** and **normalization**. Our overall goal is to search for normalized, stemmed tokens instead of using tokens obtained by splitting on whitespace (as we do now).

   Make sure that although we normalize and stem tokens, the **original token is highlighted**. For example, if due to normalization and stemming `summer` and `summer's` have the same stem, then when searching for `summer`, all occurrences of both tokens should be highlighted.

   Implement the normalization and stemming logic once and use it (1) during index creation and (2) during querying.

   1. For the **normalization** part, at least the following three characters should be removed: `',.` (apostrophe, comma, and dot).  
      Converting tokens to lowercase is also important.
   2. For **stemming**, either include the Porter stemmer linked in the slides or add a package containing a stemmer that you can use.
