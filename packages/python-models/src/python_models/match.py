from datetime import datetime
from json import dumps
from typing import Optional

from pydantic import BaseModel


class AllianceTeam(BaseModel):
    key: str
    team_key: str
    alliance_key: str

    @classmethod
    def from_tba(
        cls, team_key: str, alliance: str, match_key: str
    ) -> "AllianceTeam":
        return cls(
            key=f"{match_key}_{team_key}",
            team_key=team_key,
            alliance_key=f"{match_key}_{alliance}",
        )
        
    def to_db(self):
        return self.model_dump()


class Alliance(BaseModel):
    key: str
    match_key: str
    color: str
    score: int
    score_breakdown: Optional[str] = None
    teams: list[AllianceTeam]

    @classmethod
    def from_tba(
        cls,
        match_key: str,
        color: str,
        alliance_data: dict,
        score_breakdown: str | None,
    ) -> "Alliance":
        return cls(
            key=f"{match_key}_{color}",
            match_key=match_key,
            color=color,
            score=alliance_data.get("score", 0),
            score_breakdown=score_breakdown,
            teams=[
                AllianceTeam.from_tba(team_key, color, match_key)
                for team_key in (alliance_data.get("team_keys", [])
                + alliance_data.get("surrogate_team_keys", [])
                + alliance_data.get("dq_team_keys", []))
            ],
        )
        
    def to_db(self):
        return self.model_dump(exclude={"teams"})


class Match(BaseModel):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    winning_alliance: Optional[str] = None
    event_key: str
    alliances: list[Alliance]
    time: Optional[str] = None
    actual_time: Optional[str] = None
    predicted_time: Optional[str] = None
    post_result_time: Optional[str] = None

    @classmethod
    def from_tba(cls, match: dict) -> "Match":
        return cls(
            key=match["key"],
            comp_level=match["comp_level"],
            set_number=match["set_number"],
            match_number=match["match_number"],
            winning_alliance=match["winning_alliance"],
            alliances=[
                Alliance.from_tba(
                    match["key"],
                    color,
                    match["alliances"][color],
                    score_breakdown=(
                        dumps(match["score_breakdown"].get(color, {}))
                        if match["score_breakdown"]
                        else None
                    ),
                )
                for color in ("red", "blue")
            ],
            event_key=match["event_key"],
            time=(
                datetime.fromtimestamp(match["time"]).isoformat()
                if match["time"]
                else None
            ),
            actual_time=(
                datetime.fromtimestamp(match["actual_time"]).isoformat()
                if match["actual_time"]
                else None
            ),
            predicted_time=(
                datetime.fromtimestamp(match["predicted_time"]).isoformat()
                if match["predicted_time"]
                else None
            ),
            post_result_time=(
                datetime.fromtimestamp(match["post_result_time"]).isoformat()
                if match["post_result_time"]
                else None
            ),
        )

    def to_db(self):
        return self.model_dump(exclude={"alliances"})
