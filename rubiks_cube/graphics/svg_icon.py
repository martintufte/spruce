import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Final

import typer

from rubiks_cube.configuration.paths import DATA_DIR
from rubiks_cube.graphics import get_colored_rubiks_cube
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state

app: Final = typer.Typer()


@app.command()  # type: ignore[misc, unused-ignore]
def create_svg_icon(
    sequence: str = typer.Option(" "),
    file_name: str = typer.Option("icon.svg"),
    output_path: str = typer.Option(os.path.join(DATA_DIR, "icons")),
) -> None:
    """
    Create an SVG icon of the Rubiks Cube State.

    Args:
        sequence (str, optional): Move sequence. Defaults to " ".
        file_name (str, optional): File name. Defaults to "icon.svg".
        output_path (str, optional): _description_. Defaults to DATA_DIR / "icons".

    """
    state = get_rubiks_cube_state(MoveSequence(sequence))
    colored_cube = get_colored_rubiks_cube(tag="solved", permutation=state)

    # Colors of the up, front and right faces and their cubies
    cube_colors: list[str] = [*["#000000"] * 3, *colored_cube[:27]]

    template = "rubiks_cube/data/resources/icon_template.svg"
    tree = ET.parse(template)
    root = tree.getroot()
    namespaces = {"svg": "http://www.w3.org/2000/svg"}

    # Find all polygon elements in the template SVG
    polygons = root.findall(".//svg:polygon", namespaces)

    for polygon, new_color in zip(polygons, cube_colors):
        polygon.set("fill", new_color)

    # Save the SVG file
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    tree.write(output_dir / file_name)


if __name__ == "__main__":
    app()
