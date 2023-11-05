import sys
from OLLs import OLLs
from utilities import permutations, invert_seq, get_cube_state, sequence_to_latex

def table_to_latex(title, state, dic, idx_start, idx_end):
  latex_str = """\\bigskip
\\begin{tabular}{|p{0.968\\linewidth}|}
\\hline
\\textbf{""" + title + """}\\\\"""
  for name, oll in list(dic.items())[idx_start:idx_end]:
    name = name.strip()
    if '//' in oll:
      breakdown = oll.split('//')
      oll, comment = breakdown[0], breakdown[1].strip()
      comment = '\\color{gray}{' + comment + '}'
    else:
        comment = ''
    cube_state = get_cube_state(state)
    for move in invert_seq(oll).split():
      cube_state = [cube_state[i] for i in permutations[move]]
    latex_str += """
\\hline\\vspace{0.2mm}
\\begin{minipage}[l]{0.08\\linewidth}
\\quad """ + name + """
\\end{minipage}
\\begin{minipage}[l]{0.24\\linewidth}
""" + '\\xdef\\myarray{{"' + '","'.join(cube_state) + '"}}' + """\\DrawUpFace{3}{1}\DrawCubeIcon{3}{0.86}
\\end{minipage}
\\begin{minipage}[l]{0.48\\linewidth}""" + sequence_to_latex(oll) + """
\\end{minipage}
\\begin{minipage}[l]{0.15\\linewidth}
""" + comment + """
\\end{minipage}\\vspace{2.5mm}\\\\"""
  latex_str += """
\\hline
\\end{tabular}
\\bigskip"""
  return latex_str

idx_start, idx_end = int(sys.argv[1]), int(sys.argv[2])


# create table of OLLs
print(table_to_latex("OLL table", "OLL", OLLs, idx_start, idx_end))
