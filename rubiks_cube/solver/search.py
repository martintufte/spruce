from rubiks_cube.configuration.enumeration import Status


class SearchSummary:
    walltime: float
    n_solutions: int
    max_search_depth: int
    status: Status

    def __init__(
        self,
        walltime: float,
        n_solutions: int,
        max_search_depth: int,
        status: Status,
    ) -> None:
        self.walltime = walltime
        self.n_solutions = n_solutions
        self.max_search_depth = max_search_depth
        self.status = status
