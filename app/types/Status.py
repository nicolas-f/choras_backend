from enum import Enum


class Status(Enum):
    Created = 0
    Queued = 1
    InProgress = 2
    ProcessingResults = 3
    Completed = 4
    Cancelled = 5
    Error = 6
