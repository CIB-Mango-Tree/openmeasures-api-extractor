from .param import ParamValidator
from ..utils.constants import EXCEL, JSON, CSV
from enum import Enum


class Format(Enum):
    EXCEL = EXCEL
    JSON = JSON
    CSV = CSV


class ExportParamValidator(ParamValidator):
    format: Format
