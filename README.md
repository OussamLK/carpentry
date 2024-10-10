# Carpenter
Helps with wood cutting.

## Features
You input the dimensions of your pieces and the dimension of the board. The software says whether there is a solution. 

If no solution exists, it allows you to pick the subset of the pieces.

It a solution exists, it tries 3 different strategies to optimizing wood scraps.

### S1

create a rest that takes the entire width (smallest dimension) of the board and pushes down.

### S2

Same as S1 but taking the length as fixed

### S3

Optimizing from a corner starting from a minimal useful wood scrap dimension (ex 60x60)

# Observations
dimensions are in millimeter