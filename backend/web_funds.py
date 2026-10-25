"""Explicit, revocable provider access. No membership is inferred from registration.

Portfolio rows are a strict projection of approved publications explicitly assigned
by an MFA administrator. This does not grant investor/document permissions.
"""
import uuid
from collections import Counter

from fastapi import Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from web_accounts import administrator
from web_identity import audit, denied, now, resolve_session


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=180, pattern=r"\S")


class Member(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op_ref: str = Field(pattern=r"^OP-[A-Za-z0-9-]{1,70}$")


async def ensure_fund_indexes(db):
    await db.web_fund_entities.create_index("entity_id", unique=True)
    await db.web_fund_members.create_index([("entity_id", 1), ("subject_id", 1)], unique=True)
    # An operation cannot be assigned to two unrelated providers accidentally.
    await db.web_fund_operations.create_index("op_ref", unique=True)


async def entity(db, entity_id):
    row = await db.web_fund_entities.find_one({"entity_id": entity_id, "active": True}, {"_id": 0})
    if not row:
        denied("fund_entity_not_found", 404)
    return row


async def member_access(request, db, entity_id):
    user, session = await resolve_session(request, db)
    if user.get("role") == "superadmin":
        await administrator(request, db)
    else:
        if not await db.web_fund_members.find_one({"entity_id": entity_id, "subject_id": user["subject_id"], "active": True}):
            denied("fund_access_not_authorized")
        if not user.get("mfa_enabled") or not session.get("mfa_verified"):
            denied("fund_second_factor_required")
    return await entity(db, entity_id)


async def published_operation(db, op_ref):
    binding = await db.web_operation_bindings.find_one({"public_ref": op_ref, "publication_approved": True,
        "catalog_reference_safe": True}, {"_id": 0})
    if not binding or not binding.get("internal_id"):
        return None
    published = await db.presentation_web_published.find_one({"internal_id": binding["internal_id"],
        "publication_state": "PUBLISHED"}, {"_id": 0})
    if not published or not isinstance(published.get("item"), dict):
        return None
    return project_operation(op_ref, published["item"])


def project_operation(op_ref, item):
    # Never serialize the producer object, documents, debtor identities or URLs.
    fields = ("title", "asset_type", "municipio_name", "provincia_name", "phase")
    return {"op_ref": op_ref, **{k: str(item[k])[:250] for k in fields if isinstance(item.get(k), (str, int))}}


def register_fund_routes(router, db):
    @router.get("/funds/entities")
    async def my_entities(request: Request):
        user, _ = await resolve_session(request, db)
        admin = user.get("role") == "superadmin"
        if admin:
            await administrator(request, db)
            query = {"active": True}
        else:
            memberships = await db.web_fund_members.find({"subject_id": user["subject_id"], "active": True}).to_list(500)
            query = {"active": True, "entity_id": {"$in": [m["entity_id"] for m in memberships]}}
        rows = await db.web_fund_entities.find(query, {"_id": 0, "entity_id": 1, "name": 1}).to_list(500)
        return {"items": rows, "administrator": admin}

    @router.get("/funds/entities/{entity_id}/portfolio")
    async def portfolio(entity_id: str, request: Request):
        owner = await member_access(request, db, entity_id)
        assignments = await db.web_fund_operations.find({"entity_id": entity_id, "active": True}).to_list(1001)
        limited = len(assignments) > 1000
        assignments = assignments[:1000]
        bindings = await db.web_operation_bindings.find({"public_ref": {"$in": [a["op_ref"] for a in assignments]},
            "publication_approved": True, "catalog_reference_safe": True}).to_list(1000)
        publications = await db.presentation_web_published.find({"internal_id": {"$in": [b.get("internal_id") for b in bindings if b.get("internal_id")]},
            "publication_state": "PUBLISHED"}).to_list(1000)
        by_id = {p["internal_id"]: p["item"] for p in publications if isinstance(p.get("item"), dict)}
        rows = []
        for binding in bindings:
            if binding.get("internal_id") in by_id:
                rows.append(project_operation(binding["public_ref"], by_id[binding["internal_id"]]))
        return {"entity": {"entity_id": entity_id, "name": owner["name"]}, "items": rows,
            "total": len(rows), "by_phase": dict(Counter(r.get("phase") or "Sin fase informada" for r in rows)),
            "scope": "ASSIGNED_APPROVED_PUBLICATIONS", "limited": limited, "checked_at": now()}

    @router.post("/staff/funds/entities", status_code=201)
    async def create(payload: Entity, request: Request):
        actor = await administrator(request, db)
        row = {"entity_id": str(uuid.uuid4()), "name": payload.name.strip(), "active": True,
            "created_at": now(), "created_by": actor["subject_id"]}
        await db.web_fund_entities.insert_one(row)
        await audit(db, actor["subject_id"], "FUND_ENTITY_CREATED:" + row["entity_id"])
        return {"entity_id": row["entity_id"], "name": row["name"]}

    @router.get("/staff/funds/entities/{entity_id}/access")
    async def accesses(entity_id: str, request: Request):
        await administrator(request, db)
        await entity(db, entity_id)
        members = await db.web_fund_members.find({"entity_id": entity_id, "active": True},
            {"_id": 0, "subject_id": 1, "email": 1}).to_list(500)
        operations = await db.web_fund_operations.find({"entity_id": entity_id, "active": True},
            {"_id": 0, "op_ref": 1}).to_list(1000)
        return {"members": members, "operations": operations}

    @router.post("/staff/funds/entities/{entity_id}/members")
    async def grant(entity_id: str, payload: Member, request: Request):
        actor = await administrator(request, db)
        await entity(db, entity_id)
        email = str(payload.email).lower()
        target = await db.web_users.find_one({"email": email, "active": True, "email_verified": True})
        if not target:
            denied("fund_verified_account_required", 409)
        from web_access_restrictions import blocked
        if await blocked(db, target):
            denied("account_access_restricted", 403)
        await db.web_fund_members.update_one({"entity_id": entity_id, "subject_id": target["subject_id"]},
            {"$set": {"active": True, "email": email, "authorized_at": now(), "authorized_by": actor["subject_id"]}}, upsert=True)
        await audit(db, actor["subject_id"], "FUND_MEMBER_GRANTED:" + entity_id + ":" + target["subject_id"])
        return {"authorized": True}

    @router.delete("/staff/funds/entities/{entity_id}/members/{subject_id}")
    async def revoke(entity_id: str, subject_id: str, request: Request):
        actor = await administrator(request, db)
        result = await db.web_fund_members.update_one({"entity_id": entity_id, "subject_id": subject_id, "active": True},
            {"$set": {"active": False, "revoked_at": now(), "revoked_by": actor["subject_id"]}})
        if not result.matched_count:
            denied("fund_membership_not_found", 404)
        await audit(db, actor["subject_id"], "FUND_MEMBER_REVOKED:" + entity_id + ":" + subject_id)
        return {"revoked": True}

    @router.post("/staff/funds/entities/{entity_id}/operations")
    async def assign(entity_id: str, payload: Operation, request: Request):
        actor = await administrator(request, db)
        await entity(db, entity_id)
        if not await published_operation(db, payload.op_ref):
            denied("fund_approved_operation_required", 409)
        from pymongo.errors import DuplicateKeyError
        try:
            # A transfer requires first removing the previous assignment.
            await db.web_fund_operations.update_one({"op_ref": payload.op_ref, "$or": [
                {"entity_id": entity_id}, {"active": False}]}, {"$set": {"entity_id": entity_id,
                "active": True, "authorized_at": now(), "authorized_by": actor["subject_id"]}}, upsert=True)
        except DuplicateKeyError:
            denied("fund_operation_already_assigned", 409)
        await audit(db, actor["subject_id"], "FUND_OPERATION_ASSIGNED:" + entity_id + ":" + payload.op_ref)
        return {"assigned": True}

    @router.delete("/staff/funds/entities/{entity_id}/operations/{op_ref}")
    async def unassign(entity_id: str, op_ref: str, request: Request):
        actor = await administrator(request, db)
        result = await db.web_fund_operations.update_one({"entity_id": entity_id, "op_ref": op_ref, "active": True},
            {"$set": {"active": False, "revoked_at": now(), "revoked_by": actor["subject_id"]}})
        if not result.matched_count:
            denied("fund_assignment_not_found", 404)
        await audit(db, actor["subject_id"], "FUND_OPERATION_REMOVED:" + entity_id + ":" + op_ref)
        return {"removed": True}
