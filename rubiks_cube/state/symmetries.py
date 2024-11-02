from rubiks_cube.configuration.enumeration import Subset


def find_symmetry_subset(subset: Subset) -> dict[Subset, list[str]]:
    face_subset: dict[Subset, list[str]] = {
        Subset.up: [],
        Subset.right: ["z"],
        Subset.down: ["z2"],
        Subset.left: ["z'"],
        Subset.front: ["x'"],
        Subset.back: ["x"],
    }

    if subset in face_subset:
        return face_subset
    return face_subset
