from crossword import Crossword

cross = Crossword("data/structure0.txt", "data/words0.txt")

x = cross.variables.pop()
y = cross.variables.pop()

print(x, y)

i, j = cross.overlaps[x, y]

print(i, j)