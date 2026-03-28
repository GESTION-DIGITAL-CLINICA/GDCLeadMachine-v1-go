"""
TestRunService - Tracks a timed test run of the GDC LeadMachine.

Usage
-----
1. Call ``start_test_run(duration_hours=2)`` to begin a test run.
2. The service records baseline stats (total clinics, emails sent) at start.
3. At any point call ``get_status()`` to see live progress.
4. When the run ends (either time-out or via ``finish_test_run()``) a report
   is saved to MongoDB and returned.
5. Call ``get_report(run_id)`` or ``list_runs()`` to retrieve past results.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TestRunService:
    """
    Manages timed test runs and persists reports to MongoDB.
    Only one run can be active at a time.
    """

    COLLECTION = "test_runs"

    def __init__(self, db):
        self.db = db
        self._active_run_id: Optional[str] = None
        self._finish_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _snapshot_stats(self) -> Dict[str, Any]:
        """Capture a snapshot of the key DB counters."""
        (
            total_clinics,
            emails_sent,
            emails_pending,
            emails_failed,
            high_score_clinics,
            responded,
        ) = await asyncio.gather(
            self.db.clinics.count_documents({}),
            self.db.email_queue.count_documents({"status": "sent"}),
            self.db.email_queue.count_documents({"status": "pending"}),
            self.db.email_queue.count_documents({"status": "failed"}),
            self.db.clinics.count_documents({"score": {"$gte": 7}}),
            self.db.clinics.count_documents({"estado": "Respondió"}),
        )
        return {
            "total_clinics": total_clinics,
            "emails_sent": emails_sent,
            "emails_pending": emails_pending,
            "emails_failed": emails_failed,
            "high_score_clinics": high_score_clinics,
            "responded": responded,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_report(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Compute delta fields and return a clean report dict."""
        baseline = doc.get("baseline_stats", {})
        final = doc.get("final_stats", {})

        new_clinics_found = (
            final.get("total_clinics", 0) - baseline.get("total_clinics", 0)
        )
        emails_sent_during_run = (
            final.get("emails_sent", 0) - baseline.get("emails_sent", 0)
        )

        started_at: Optional[str] = doc.get("started_at")
        finished_at: Optional[str] = doc.get("finished_at")
        actual_duration_minutes: Optional[float] = None
        if started_at and finished_at:
            try:
                dt_start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                dt_end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                actual_duration_minutes = round(
                    (dt_end - dt_start).total_seconds() / 60, 1
                )
            except Exception:
                pass

        return {
            "run_id": doc.get("run_id"),
            "status": doc.get("status"),
            "started_at": started_at,
            "finished_at": finished_at,
            "planned_duration_hours": doc.get("duration_hours"),
            "actual_duration_minutes": actual_duration_minutes,
            "new_clinics_found": max(new_clinics_found, 0),
            "emails_sent_to_real_leads": max(emails_sent_during_run, 0),
            "baseline_stats": baseline,
            "final_stats": final if final else None,
            "notes": doc.get("notes"),
        }

    async def _auto_finish(self, run_id: str, duration_seconds: float):
        """Background task that auto-finishes a run after the planned duration."""
        await asyncio.sleep(duration_seconds)
        try:
            doc = await self.db[self.COLLECTION].find_one({"run_id": run_id})
            if doc and doc.get("status") == "running":
                await self._do_finish(run_id)
        except Exception as exc:
            logger.error(f"TestRunService auto-finish error for {run_id}: {exc}")

    async def _do_finish(self, run_id: str) -> Dict[str, Any]:
        """Capture final stats, update the document, return the report."""
        final_stats = await self._snapshot_stats()
        finished_at = datetime.now(timezone.utc).isoformat()
        await self.db[self.COLLECTION].update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": "completed",
                    "finished_at": finished_at,
                    "final_stats": final_stats,
                }
            },
        )
        if self._active_run_id == run_id:
            self._active_run_id = None
        doc = await self.db[self.COLLECTION].find_one({"run_id": run_id})
        report = self._build_report(doc)
        logger.info("=" * 60)
        logger.info("📊 TEST RUN COMPLETE")
        logger.info(f"🆔 Run ID : {run_id}")
        logger.info(f"🏥 New clinics found  : {report['new_clinics_found']}")
        logger.info(f"📧 Emails sent (leads): {report['emails_sent_to_real_leads']}")
        logger.info(f"⏱️  Duration           : {report['actual_duration_minutes']} min")
        logger.info("=" * 60)
        return report

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_test_run(
        self,
        duration_hours: float = 2.0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new timed test run.
        Raises ``ValueError`` if a run is already active.
        """
        if self._active_run_id:
            existing = await self.db[self.COLLECTION].find_one(
                {"run_id": self._active_run_id}
            )
            if existing and existing.get("status") == "running":
                raise ValueError(
                    f"A test run is already active: {self._active_run_id}. "
                    "Call /api/test-run/finish first."
                )
            # Stale in-memory reference — clear it
            self._active_run_id = None

        run_id = str(uuid.uuid4())
        baseline_stats = await self._snapshot_stats()
        started_at = datetime.now(timezone.utc).isoformat()

        doc: Dict[str, Any] = {
            "run_id": run_id,
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "duration_hours": duration_hours,
            "baseline_stats": baseline_stats,
            "final_stats": None,
            "notes": notes,
        }
        await self.db[self.COLLECTION].insert_one(doc)
        self._active_run_id = run_id

        # Schedule auto-finish
        duration_seconds = duration_hours * 3600
        self._finish_task = asyncio.create_task(
            self._auto_finish(run_id, duration_seconds)
        )

        logger.info("=" * 60)
        logger.info("🚀 TEST RUN STARTED")
        logger.info(f"🆔 Run ID          : {run_id}")
        logger.info(f"⏱️  Duration        : {duration_hours} hours ({duration_seconds/60:.0f} min)")
        logger.info(f"🏥 Baseline clinics: {baseline_stats['total_clinics']}")
        logger.info(f"📧 Baseline emails : {baseline_stats['emails_sent']}")
        logger.info("=" * 60)

        return {
            "run_id": run_id,
            "status": "running",
            "started_at": started_at,
            "duration_hours": duration_hours,
            "baseline_stats": baseline_stats,
            "message": (
                f"Test run started. Will auto-finish in {duration_hours} hours. "
                "Use GET /api/test-run/status to check progress or "
                "POST /api/test-run/finish to end early."
            ),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Return live status of the current (or most recent) run."""
        run_id = self._active_run_id
        if not run_id:
            # Find the most recent run
            doc = await self.db[self.COLLECTION].find_one(
                sort=[("started_at", -1)]
            )
            if not doc:
                return {"status": "no_runs", "message": "No test runs found."}
        else:
            doc = await self.db[self.COLLECTION].find_one({"run_id": run_id})

        if not doc:
            return {"status": "not_found", "run_id": run_id}

        # If still running, attach a live snapshot for comparison
        live_stats = None
        elapsed_minutes = None
        remaining_minutes = None
        if doc.get("status") == "running":
            live_stats = await self._snapshot_stats()
            try:
                dt_start = datetime.fromisoformat(
                    doc["started_at"].replace("Z", "+00:00")
                )
                elapsed_seconds = (
                    datetime.now(timezone.utc) - dt_start
                ).total_seconds()
                elapsed_minutes = round(elapsed_seconds / 60, 1)
                total_seconds = doc.get("duration_hours", 2) * 3600
                remaining_minutes = round(
                    max(total_seconds - elapsed_seconds, 0) / 60, 1
                )
            except Exception:
                pass

        report = self._build_report(doc)
        if live_stats is not None:
            report["live_stats"] = live_stats
        report["elapsed_minutes"] = elapsed_minutes
        report["remaining_minutes"] = remaining_minutes
        return report

    async def finish_test_run(self) -> Dict[str, Any]:
        """Manually finish the active test run early."""
        if not self._active_run_id:
            # Check DB for any running run
            doc = await self.db[self.COLLECTION].find_one({"status": "running"})
            if not doc:
                raise ValueError("No active test run to finish.")
            self._active_run_id = doc["run_id"]

        if self._finish_task and not self._finish_task.done():
            self._finish_task.cancel()

        return await self._do_finish(self._active_run_id)

    async def get_report(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the report for a specific run_id."""
        doc = await self.db[self.COLLECTION].find_one({"run_id": run_id})
        if not doc:
            return None
        return self._build_report(doc)

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent test runs, most recent first."""
        docs = (
            await self.db[self.COLLECTION]
            .find({}, sort=[("started_at", -1)])
            .limit(limit)
            .to_list(limit)
        )
        return [self._build_report(d) for d in docs]
