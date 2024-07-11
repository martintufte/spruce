from typing import Final

import typer
from pathlib import Path
import xml.etree.ElementTree as ET

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.graphics import get_cube_string
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.configuration import COLOR_SCHEME


app: Final = typer.Typer()


@app.command()
def create_svg_icon(
    sequence: str = typer.Option(" "),
    file_name: str = typer.Option("icon.svg"),
    output_path: str = typer.Option("rubiks_cube/data/icons"),
) -> None:
    """Create an SVG icon of the Rubiks Cube State."""

    state = get_rubiks_cube_state(MoveSequence(sequence))
    cube_string = get_cube_string(state)

    # Colors of the up, front and right faces and their cubies
    cube_colors: list[str] = [
        *["#000000"] * 3,
        *[COLOR_SCHEME[face] for face in cube_string[:27]],
    ]

    template = "rubiks_cube/data/resources/icon_template.svg"
    tree = ET.parse(template)
    root = tree.getroot()
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    # Find all polygon elements in the template SVG
    polygons = root.findall('.//svg:polygon', namespaces)

    for polygon, new_color in zip(polygons, cube_colors):
        polygon.set('fill', new_color)

    # Save the SVG file
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    tree.write(output_dir / file_name)


if __name__ == "__main__":
    app()
