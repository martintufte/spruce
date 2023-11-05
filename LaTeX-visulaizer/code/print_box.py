import sys
from utilities import sequence_to_latex, steps_to_latex, get_cube_state, permutations

def split_reconstruction(recon):
  recon = recon.strip()
  lines = [line.strip() for line in recon.split('\n')]
  # lines = ['title', 'scramble', '', 'step 1 // comment 1', 'step 2 // comment 2', '', 'solution']
  title, scramble = lines[0], lines[1]

  if len(lines)>2 and lines[2]=='':
    lines = lines[3:]
    if '' in lines:
      steps = lines[:lines.index('')]
      solution = lines[-1]
      return title, scramble, steps, solution
    return title, scramble, lines, None
  return title, scramble, None, None

def box_to_latex(title, scramble, steps=None, solution=None, draw_func="DrawCube"):
  latex_str = "\\bigskip\n\\begin{tabular}{|p{0.968\\linewidth}|}\n\\hline\n\\textbf{" + title + """}\\\\\n\\hline
Scramble: """ + sequence_to_latex(scramble) + "\\\\\n\\hline"
  if steps is not None:
    latex_str += "\\\\\n\\begin{minipage}[l]{0.75\\linewidth}\n" + steps_to_latex(steps) + "\\end{minipage}"
  latex_str += "\n\\begin{minipage}[c]{0.20\\linewidth}\n\\"+ draw_func + "{3}{2}\n\\end{minipage}\\\\"
  if solution is not None:
    latex_str += """\n\\hline\nSolution: """ + sequence_to_latex(solution) + "\\\\"
  latex_str += "\n\\hline\n\\end{tabular}\n\\bigskip\\\\"

  return latex_str

# import reconstructions
if int(sys.argv[3])==0:
    from reconstructions_3x3 import reconstructions
elif int(sys.argv[3])==1:
    from reconstructions_FMC import reconstructions
else:
    from reconstructions_3x3 import reconstructions
    
recon = reconstructions[int(sys.argv[1])]
draw_func = "DrawCube" if int(sys.argv[2]) else "DrawSimpleCube"
title, scr, steps, sol = split_reconstruction(recon)

cube_state = get_cube_state('solved')

# apply the moves in the scramble
for move in scr.split():
  if move == '':
    pass
  cube_state = [cube_state[i] for i in permutations[move]]

# set the cube state
print('\\xdef\\myarray{{"' + '","'.join(cube_state) + '"}}')

# do the reconstruction
print(box_to_latex(title, scr, steps, sol, draw_func))
