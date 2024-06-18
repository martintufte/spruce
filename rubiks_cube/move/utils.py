

def combine_rotations(rotation_list: list[str]) -> list[str]:
    """
    Collapse rotations in a sequence to a standard rotation.
    It rotates the cube to correct up-face and the correct front-face.
    """
    standard_rotations = {
        "UF": "",
        "UL": "y'",
        "UB": "y2",
        "UR": "y",
        "FU": "x y2",
        "FL": "x y'",
        "FD": "x",
        "FR": "x y",
        "RU": "z' y'",
        "RF": "z'",
        "RD": "z' y",
        "RB": "z' y2",
        "BU": "x'",
        "BL": "x' y'",
        "BD": "x' y2",
        "BR": "x' y",
        "LU": "z y",
        "LF": "z",
        "LD": "z y'",
        "LB": "z y2",
        "DF": "z2",
        "DL": "x2 y'",
        "DB": "x2",
        "DR": "x2 y",
    }
    transition_dict = {
        'x': {
            'UF': 'FD',
            'UL': 'LD',
            'UB': 'BD',
            'UR': 'RD',
            'FU': 'UB',
            'FL': 'LB',
            'FD': 'DB',
            'FR': 'RB',
            'RU': 'UL',
            'RF': 'FL',
            'RD': 'DL',
            'RB': 'BL',
            'BU': 'UF',
            'BL': 'LF',
            'BD': 'DF',
            'BR': 'RF',
            'LU': 'UR',
            'LF': 'FR',
            'LD': 'DR',
            'LB': 'BR',
            'DF': 'FU',
            'DL': 'LU',
            'DB': 'BU',
            'DR': 'RU',
        },
        "x'": {
            'UF': 'BU',
            'UL': 'RU',
            'UB': 'FU',
            'UR': 'LU',
            'FU': 'DF',
            'FL': 'RF',
            'FD': 'UF',
            'FR': 'LF',
            'RU': 'DR',
            'RF': 'BR',
            'RD': 'UR',
            'RB': 'FR',
            'BU': 'DB',
            'BL': 'RB',
            'BD': 'UB',
            'BR': 'LB',
            'LU': 'DL',
            'LF': 'BL',
            'LD': 'UL',
            'LB': 'FL',
            'DF': 'BD',
            'DL': 'RD',
            'DB': 'FD',
            'DR': 'LD',
        },
        'x2': {
            'UF': 'DB',
            'UL': 'DR',
            'UB': 'DF',
            'UR': 'DL',
            'FU': 'BD',
            'FL': 'BR',
            'FD': 'BU',
            'FR': 'BL',
            'RU': 'LD',
            'RF': 'LB',
            'RD': 'LU',
            'RB': 'LF',
            'BU': 'FD',
            'BL': 'FR',
            'BD': 'FU',
            'BR': 'FL',
            'LU': 'RD',
            'LF': 'RB',
            'LD': 'RU',
            'LB': 'RF',
            'DF': 'UB',
            'DL': 'UR',
            'DB': 'UF',
            'DR': 'UL',
        },
        'y': {
            'UF': 'UR',
            'UL': 'UF',
            'UB': 'UL',
            'UR': 'UB',
            'FU': 'FL',
            'FL': 'FD',
            'FD': 'FR',
            'FR': 'FU',
            'RU': 'RF',
            'RF': 'RD',
            'RD': 'RB',
            'RB': 'RU',
            'BU': 'BR',
            'BL': 'BU',
            'BD': 'BL',
            'BR': 'BD',
            'LU': 'LB',
            'LF': 'LU',
            'LD': 'LF',
            'LB': 'LD',
            'DF': 'DL',
            'DL': 'DB',
            'DB': 'DR',
            'DR': 'DF',
        },
        "y'": {
            'UF': 'UL',
            'UL': 'UB',
            'UB': 'UR',
            'UR': 'UF',
            'FU': 'FR',
            'FL': 'FU',
            'FD': 'FL',
            'FR': 'FD',
            'RU': 'RB',
            'RF': 'RU',
            'RD': 'RF',
            'RB': 'RD',
            'BU': 'BL',
            'BL': 'BD',
            'BD': 'BR',
            'BR': 'BU',
            'LU': 'LF',
            'LF': 'LD',
            'LD': 'LB',
            'LB': 'LU',
            'DF': 'DR',
            'DL': 'DF',
            'DB': 'DL',
            'DR': 'DB',
        },
        'y2': {
            'UF': 'UB',
            'UL': 'UR',
            'UB': 'UF',
            'UR': 'UL',
            'FU': 'FD',
            'FL': 'FR',
            'FD': 'FU',
            'FR': 'FL',
            'RU': 'RD',
            'RF': 'RB',
            'RD': 'RU',
            'RB': 'RF',
            'BU': 'BD',
            'BL': 'BR',
            'BD': 'BU',
            'BR': 'BL',
            'LU': 'LD',
            'LF': 'LB',
            'LD': 'LU',
            'LB': 'LF',
            'DF': 'DB',
            'DL': 'DR',
            'DB': 'DF',
            'DR': 'DL',
        },
        'z': {
            'UF': 'LF',
            'UL': 'BL',
            'UB': 'RB',
            'UR': 'FR',
            'FU': 'RU',
            'FL': 'UL',
            'FD': 'LD',
            'FR': 'DR',
            'RU': 'BU',
            'RF': 'UF',
            'RD': 'FD',
            'RB': 'DB',
            'BU': 'LU',
            'BL': 'DL',
            'BD': 'RD',
            'BR': 'UR',
            'LU': 'FU',
            'LF': 'DF',
            'LD': 'BD',
            'LB': 'UB',
            'DF': 'RF',
            'DL': 'FL',
            'DB': 'LB',
            'DR': 'BR',
        },
        "z'": {
            'UF': 'RF',
            'UL': 'FL',
            'UB': 'LB',
            'UR': 'BR',
            'FU': 'LU',
            'FL': 'DL',
            'FD': 'RD',
            'FR': 'UR',
            'RU': 'FU',
            'RF': 'DF',
            'RD': 'BD',
            'RB': 'UB',
            'BU': 'RU',
            'BL': 'UL',
            'BD': 'LD',
            'BR': 'DR',
            'LU': 'BU',
            'LF': 'UF',
            'LD': 'FD',
            'LB': 'DB',
            'DF': 'LF',
            'DL': 'BL',
            'DB': 'RB',
            'DR': 'FR',
        },
        'z2': {
            'UF': 'DF',
            'UL': 'DL',
            'UB': 'DB',
            'UR': 'DR',
            'FU': 'BU',
            'FL': 'BL',
            'FD': 'BD',
            'FR': 'BR',
            'RU': 'LU',
            'RF': 'LF',
            'RD': 'LD',
            'RB': 'LB',
            'BU': 'FU',
            'BL': 'FL',
            'BD': 'FD',
            'BR': 'FR',
            'LU': 'RU',
            'LF': 'RF',
            'LD': 'RD',
            'LB': 'RB',
            'DF': 'UF',
            'DL': 'UL',
            'DB': 'UB',
            'DR': 'UR',
        }
    }

    current_state = "UF"
    for rotation in rotation_list:
        current_state = transition_dict[rotation][current_state]

    standard_rotation_list = standard_rotations[current_state]

    return standard_rotation_list.split()


def move_as_int(move: str) -> int:
    """Return the integer representation of a move."""
    if move.endswith("2"):
        return 2
    elif move.endswith("'"):
        return -1
    return 1


def simplyfy_axis_moves(moves: list[str]) -> list[str]:
    """
    Combine adjacent moves if they cancel each other.
    E.g. R R' -> "", R L R' -> L
    """
    moves.sort()

    face_count = {}

    for move in moves:
        face = move[0]
        if face in face_count:
            face_count[face] += move_as_int(move)
        else:
            face_count[face] = move_as_int(move)

    return [
        ["", f"{face}", f"{face}2", f"{face}'"][face_count[face] % 4]
        for face in face_count.keys()
        if face_count[face] % 4 != 0
    ]
