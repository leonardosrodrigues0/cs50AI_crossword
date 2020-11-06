import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
        constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            words_rem = list()

            for word in self.domains[var]:
                if len(word) != var.length:
                    words_rem.append(word)

            for word in words_rem:
                self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        pos = self.crossword.overlaps[x, y]

        if pos is None:
            return False

        # List of words to be removed from self.domains[x]
        words_rem = list()

        for x_word in self.domains[x]:
            rem = True

            for y_word in self.domains[y]:
                if x_word[pos[0]] == y_word[pos[1]]:
                    rem = False
                    break

            if rem:
                words_rem.append(x_word)

        revision = bool(words_rem)
            
        for word in words_rem:
            self.domains[x].remove(word)

        return revision

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            arcs = list()

            for x in self.crossword.variables:
                for y in self.crossword.neighbors(x):
                    if (x, y) not in arcs and (y, x) not in arcs:
                        arcs.append((x, y))

        while arcs:
            arc = arcs.pop(0)

            # For both arc orders.
            for x, y in [arc, arc[::-1]]:
                revised = self.revise(x, y)

                # If domain is empty (impossible):
                if not self.domains[x]:
                    return False

                # Add arcs between x and its neighbors if x revised.
                elif revised:
                    for neighbor in self.crossword.neighbors(x):
                        if (x, neighbor) not in arcs and (neighbor, x) not in arcs:
                            arcs.append((x, neighbor))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for v in self.crossword.variables:
            if v not in assignment:
                return False

        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for v in assignment:
            # Check for length consistency.
            if v.length != len(assignment[v]):
                return False

            # Check if common cells have the same letter.
            for neighbor in self.crossword.neighbors(v):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[v, neighbor]

                    if assignment[v][i] != assignment[neighbor][j]:
                        return False

            # Check for duplicates.
            if list(assignment.values()).count(assignment[v]) > 1:
                return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # For implemenation by now, this function only returns any list:
        # This function only speeds up the algorithm.
        
        return list(self.domains[var]).copy()

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        minimum = 10**6

        for var in self.crossword.variables:
            if var not in assignment:
                L = len(self.domains[var])

                if L < minimum:
                    minimum = L
                    variables = [var]

                elif L == minimum:
                    variables.append(var)

        if len(variables) == 1:
            return variables[0]

        else:
            maximum = 0

            for var in variables:
                N = len(self.crossword.neighbors(var))

                if N > maximum:
                    maximum = N
                    chosen = var

            return chosen

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if assignment is None:
            return None

        if self.assignment_complete(assignment):
            return assignment

        # Select a var to be assigned.
        var = self.select_unassigned_variable(assignment)

        # Creates a copy of the dict assignment:
        new_assignment = assignment.copy()

        for value in self.order_domain_values(var, assignment):

            # Assign a value to var and recursevely calls self.backtrack.
            new_assignment[var] = value

            if self.consistent(new_assignment):
                new_assignment = self.backtrack(new_assignment)

                if new_assignment is not None:
                    return new_assignment
                
                else:
                    new_assignment = assignment.copy()

        # Returns None if no value was valid.
        return None



def main():

    # # Check usage
    # if len(sys.argv) not in [3, 4]:
    #     sys.exit("Usage: python generate.py structure words [output]")

    # # Parse command-line arguments
    # structure = sys.argv[1]
    # words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    for i in range(3):
        for j in range(3):
            words =  'data/words' + str(i) + '.txt'
            structure = 'data/structure' + str(j) + '.txt'

            print(words, structure)

            # Generate crossword
            crossword = Crossword(structure, words)
            creator = CrosswordCreator(crossword)
            assignment = creator.solve()

            # Print result
            if assignment is None:
                print("No solution.")
            else:
                creator.print(assignment)
                if output:
                    creator.save(assignment, output)


if __name__ == "__main__":
    main()
