import sys
from scrambles import scrambles
from permutations import permutations

if len(sys.argv) == 2:
  scr  = scrambles[int(sys.argv[1])]
  permutations = permutations[1]
  size2 = 9
elif len(sys.argv) == 3:
  size = int(sys.argv[1])
  scr  = scrambles[int(sys.argv[2])]
  permutations = permutations[size-2]
  size2 = size**2

sides = ["U","F","R","B","L","D","-"]
cube_state = [sides[i//size2] for i in range(6*size2)]

for move in scr.split():
  cube_state = [cube_state[i] for i in permutations[move]]

print('\\xdef\\myarray{{"' + '","'.join([colors[int(s//size2)] for s in cube_state]) + '"}}')
