"""Saved investor criteria, never an operation grant or an automatic alert."""
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from investor_access import authenticated_subject, context, fail
from web_identity import now


class Perimeter(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    province: str = Field(default="", max_length=100)
    municipality: str = Field(default="", max_length=100)
    asset_type: str = Field(default="", max_length=100)
    min_price: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    max_price: float | None = Field(default=None, ge=0, le=1_000_000_000, allow_inf_nan=False)
    min_roi: float | None = Field(default=None, ge=-100, le=10000, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered_prices(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("minimum_exceeds_maximum")
        return self


class Perimeters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[Perimeter] = Field(max_length=10)


def register_perimeter_routes(router, db):
    async def allowed(subject):
        ctx = await context(db, subject)
        if ctx["stage"] < 2 or not ctx["premium"]:
            fail("premium_required")

    @router.get("/investor/perimeters")
    async def get(subject: str = Depends(authenticated_subject)):
        await allowed(subject)
        row = await db.web_workspace_settings.find_one({"subject_id": subject}, {"_id": 0, "perimeters": 1}) or {}
        return {"items": row.get("perimeters", []), "limit": 10}

    @router.put("/investor/perimeters")
    async def save(payload: Perimeters, subject: str = Depends(authenticated_subject)):
        await allowed(subject)
        await db.web_workspace_settings.update_one({"subject_id": subject}, {"$set": {
            "perimeters": [x.model_dump() for x in payload.items], "perimeters_updated_at": now()}}, upsert=True)
        return {"saved": True, "items": [x.model_dump() for x in payload.items]}
