from enum import Enum


class Status(Enum):
    Created = 'Created'
    Queued = 'Queued'
    InProgress = 'InProgress'
    ProcessingResults = 'ProcessingResults'
    Completed = 'Completed'
    Cancelled = 'Cancelled'
    Error = 'Error'
