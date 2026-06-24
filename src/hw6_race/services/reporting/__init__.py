"""JSON reporting + Gmail dispatch. See PRD-005."""

from hw6_race.services.reporting.bonus_report import InterGroupBonusReport, compute_bonus_claim
from hw6_race.services.reporting.mailer import MailerError, ReportMailer
from hw6_race.services.reporting.run_logger import RunLogger
from hw6_race.services.reporting.schemas import InternalGameReport
from hw6_race.services.reporting.technical_loss import is_technical_loss, resolve_technical_losses

__all__ = [
    "InterGroupBonusReport",
    "InternalGameReport",
    "MailerError",
    "ReportMailer",
    "RunLogger",
    "compute_bonus_claim",
    "is_technical_loss",
    "resolve_technical_losses",
]
