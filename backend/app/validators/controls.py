"""
Concrete per-control validators.

Each declares only its metadata; all evaluation logic is inherited from
`ControlValidator`. `presence_field` is the "an evidence row exists" flag — a
control that has a row but reports itself off is failed by the blueprint's own
install rule during the field diff, not treated as missing data.
"""

from app.schemas.common import ControlType
from app.validators.base import ControlValidator


class AntivirusValidator(ControlValidator):
    control_type = ControlType.ANTIVIRUS
    presence_field = "av_present"


class EdrValidator(ControlValidator):
    control_type = ControlType.EDR
    presence_field = "edr_present"


class FirewallValidator(ControlValidator):
    control_type = ControlType.FIREWALL
    presence_field = "fw_present"


class BitlockerValidator(ControlValidator):
    control_type = ControlType.BITLOCKER
    presence_field = "bl_present"
