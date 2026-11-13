"""Share the memory budget between OCR and preview subprocesses."""
from threading import BoundedSemaphore

document_processing_slot = BoundedSemaphore(1)
