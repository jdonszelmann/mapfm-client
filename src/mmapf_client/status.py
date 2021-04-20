from enum import Enum


class Status(Enum):
    Uninitialized = "Uninitialized"
    Running = "Running"
    Submitting = "Submitting"
    Submitted = "Submitted"
