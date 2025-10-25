from rubiks_cube.configuration.enumeration import Status


class UnsolveableError(Exception):
    pass


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
        """Initialize the SearchSummary class.

        Args:
            walltime (float): Walltime.
            n_solutions (int): Number of solutions.
            max_search_depth (int): Maximum search depth.
            status (Status): Status of the search.
        """
        self.walltime = walltime
        self.n_solutions = n_solutions
        self.max_search_depth = max_search_depth
        self.status = status
