# the top-level models module needs to import all models so that the
# database migration tool can detect them
from .core import BridgeCommand, DeviceCommand, Bridge, Device, PendingClaim