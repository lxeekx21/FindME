from datetime import datetime, timezone
import pytest

from app.services.submission_service import SubmissionService
from app.models.submission_models import (
    SubmissionCreateDTO,
    SubmissionUpdateDTO,
)


class FakeSubmission:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.summarize_calls = 0

    async def get_by_id(self, id):
        if id == 1:
            return FakeSubmission(
                id=1,
                title="t",
                full_name="fn",
                dob=None,
                gender=None,
                race=None,
                height=None,
                weight=None,
                province=None,
                description=None,
                status="pending",
                last_seen_address=None,
                last_seen_place_id=None,
                last_seen_lat=None,
                last_seen_lng=None,
                images=[],
                user_id=2,
                created_at=datetime.now(timezone.utc),
            )
        return None

    async def list(self, limit=500, offset=0):
        return [await self.get_by_id(1)]

    async def list_by_user(self, user_id, limit=500, offset=0):
        if user_id == 2:
            return [await self.get_by_id(1)]
        return []

    async def create(self, **payload):
        self.created.append(payload)
        return FakeSubmission(id=99, created_at=pytest.datetime.datetime.now(pytest.datetime.timezone.utc), **payload)

    async def update(self, id, **payload):
        self.updated.append((id, payload))
        return FakeSubmission(id=id, created_at=pytest.datetime.datetime.now(pytest.datetime.timezone.utc), **payload)

    async def delete(self, id):
        self.deleted.append(id)
        return True

    async def summarize(self):
        self.summarize_calls += 1
        return {"total_submissions": 1, "status_counts": {"pending": 1}}


@pytest.fixture(autouse=True)
def patch_repo(monkeypatch):
    # Patch the repository the service constructs
    monkeypatch.setattr(
        "app.services.submission_service.SubmissionRepository",
        lambda session: FakeRepo(),
    )


def make_service():
    class DummySession:
        pass

    return SubmissionService(DummySession())


@pytest.mark.asyncio
async def test_create_sets_defaults_and_returns_dto():
    svc = make_service()
    dto = SubmissionCreateDTO(
        title="Missing Person",
        full_name="John Doe",
        description="desc",
    )
    res = await svc.create(dto, user_id=5, images=None)
    assert res.id == 99
    assert res.status == "pending"
    assert res.images == []
    assert res.user_id == 5


@pytest.mark.asyncio
async def test_list_and_get_convert_to_dto():
    svc = make_service()
    items = await svc.list()
    assert len(items) == 1
    one = await svc.get(1)
    assert one is not None and one.id == 1


@pytest.mark.asyncio
async def test_update_and_delete():
    svc = make_service()
    upd = SubmissionUpdateDTO(description="new")
    updated = await svc.update(1, upd)
    assert updated is not None
    assert updated.description == "new"
    ok = await svc.delete(1)
    assert ok is True


@pytest.mark.asyncio
async def test_summarize_is_cached_within_ttl(monkeypatch):
    svc = make_service()
    # access underlying fake
    fake_repo = svc.repo
    out1 = await svc.summarize()
    out2 = await svc.summarize()
    assert out1.total_submissions == 1
    assert out2.total_submissions == 1
    # Only one underlying call due to ttl_cache
    assert fake_repo.summarize_calls == 1
