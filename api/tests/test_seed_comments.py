import random
from datetime import datetime, timedelta, timezone

import pytest

from scripts.seed_test_data import seed_comments


class FakeSubmission:
    def __init__(self, id, created_at):
        self.id = id
        self.created_at = created_at


class FakeSubmissionRepo:
    def __init__(self, subs):
        # subs: dict id->FakeSubmission
        self._subs = subs

    async def get_by_id(self, id):
        return self._subs.get(id)


class FakeCommentRepo:
    def __init__(self):
        self.created = []

    async def create(self, **payload):
        self.created.append(payload)
        return {"id": len(self.created), **payload}


@pytest.mark.asyncio
async def test_seed_comments_creates_within_bounds_and_not_future(monkeypatch):
    # Deterministic randomness
    random.seed(1234)

    # Prepare fake data: 3 submissions with base created_at 2 days ago
    base_dt = datetime.now(timezone.utc) - timedelta(days=2)
    subs = {i: FakeSubmission(i, base_dt + timedelta(minutes=i)) for i in range(1, 4)}

    fake_sub_repo = FakeSubmissionRepo(subs)
    fake_com_repo = FakeCommentRepo()

    # Patch repositories used inside the function
    monkeypatch.setattr("scripts.seed_test_data.SubmissionRepository", lambda sess: fake_sub_repo)
    monkeypatch.setattr("scripts.seed_test_data.CommentRepository", lambda sess: fake_com_repo)

    # Execute with a target total to make assertions deterministic
    total = await seed_comments(db_session=object(), submission_ids=list(subs.keys()), candidate_user_ids=[10, 11, 12], target_total=20)

    assert total == 20
    assert len(fake_com_repo.created) == 20

    now = datetime.now(timezone.utc)
    for c in fake_com_repo.created:
        assert c["submission_id"] in subs
        assert c["user_id"] in {10, 11, 12}
        assert c["created_at"] <= now
        assert isinstance(c["body"], str) and len(c["body"]) > 0
        assert c["status"] in {"approved", "pending", "rejected"}
        # rejection_reason can be None or str; ensure type compliance
        rr = c.get("rejection_reason")
        assert rr is None or isinstance(rr, str)
