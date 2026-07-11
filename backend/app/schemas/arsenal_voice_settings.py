"""Pydantic schemas for Arsenal voice coaching settings."""

from typing import Literal

from pydantic import BaseModel

CoachTone = Literal["intense", "standard", "calm"]


class ArsenalVoiceSettingsRead(BaseModel):
    enabled: bool = True
    guidedPractice: bool = True
    postDebrief: bool = True
    preExecBrief: bool = True
    tone: CoachTone = "standard"


class ArsenalVoiceSettingsPatch(BaseModel):
    enabled: bool | None = None
    guidedPractice: bool | None = None
    postDebrief: bool | None = None
    preExecBrief: bool | None = None
    tone: CoachTone | None = None
