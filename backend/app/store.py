from __future__ import annotations

import os
import re
import sqlite3
import threading
from pathlib import Path

from .schemas import Case, PriorDecision, Project, now


class ConflictError(Exception):
    pass


class Store:
    def __init__(self, path: str | None = None):
        self.path = path or os.getenv("CONTEXTGUARD_DB", "data/contextguard.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, version INTEGER NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT COLLATE NOCASE UNIQUE NOT NULL, body TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS project_decisions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, case_id TEXT NOT NULL, body TEXT NOT NULL, digest TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS decisions_by_project ON project_decisions(project_id, case_id)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS decision_search USING fts5(decision_id UNINDEXED, project_id UNINDEXED, text)")
            db.execute("CREATE TABLE IF NOT EXISTS memory_index_jobs (decision_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, action TEXT NOT NULL, digest TEXT NOT NULL, remote_id TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT 'pending', error TEXT NOT NULL DEFAULT '')")
        for case in self.list():
            if case.run and case.run.status == "running":
                case.run.status = "failed"
                case.run.error = "The server restarted during this review. Your sources are saved; run the review again."
                case.run.finished_at = now()
                self.save(case)
            else:
                with self.connect() as db:
                    self._refresh_memory(db, case)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def get(self, case_id: str) -> Case:
        with self.connect() as db:
            row = db.execute("SELECT body FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            raise KeyError(case_id)
        return Case.model_validate_json(row[0])

    def list(self) -> list[Case]:
        with self.connect() as db:
            rows = db.execute("SELECT body FROM cases").fetchall()
        return sorted([Case.model_validate_json(r[0]) for r in rows], key=lambda x: x.updated_at, reverse=True)

    def save(self, case: Case, create: bool = False) -> Case:
        with self.lock, self.connect() as db:
            case.updated_at = now()
            expected = case.version
            case.version += 1
            if create:
                db.execute("INSERT INTO cases VALUES (?, ?, ?)", (case.id, case.version, case.model_dump_json()))
            else:
                cursor = db.execute("UPDATE cases SET version = ?, body = ? WHERE id = ? AND version = ?", (case.version, case.model_dump_json(), case.id, expected))
                if cursor.rowcount != 1:
                    case.version = expected
                    raise ConflictError("This review changed in another request. Refresh and try again.")
            self._refresh_memory(db, case)
        return case

    def delete(self, case_id: str):
        with self.lock, self.connect() as db:
            for row in db.execute('SELECT id, project_id FROM project_decisions WHERE case_id = ?', (case_id,)).fetchall():
                self._remove_decision(db, row[0], row[1])
            db.execute("DELETE FROM cases WHERE id = ?", (case_id,))

    def create_project(self, name):
        project = Project(name=' '.join(name.split()))
        with self.lock, self.connect() as db:
            try:
                db.execute('INSERT INTO projects VALUES (?, ?, ?)', (project.id, project.name, project.model_dump_json()))
            except sqlite3.IntegrityError:
                raise ConflictError('A project with this name already exists. Choose it from the project list.') from None
        return project

    def get_project(self, project_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM projects WHERE id = ?', (project_id,)).fetchone()
        if row is None:
            raise KeyError(project_id)
        return Project.model_validate_json(row[0])

    def projects(self):
        with self.connect() as db:
            rows = db.execute('SELECT body FROM projects ORDER BY name COLLATE NOCASE').fetchall()
        return [Project.model_validate_json(row[0]) for row in rows]

    def _remove_decision(self, db, decision_id, project_id):
        db.execute('DELETE FROM project_decisions WHERE id = ?', (decision_id,))
        db.execute('DELETE FROM decision_search WHERE decision_id = ?', (decision_id,))
        db.execute("INSERT INTO memory_index_jobs (decision_id,project_id,action,digest) VALUES (?,?,'delete','') ON CONFLICT(decision_id) DO UPDATE SET action='delete',digest='',state='pending',error=''", (decision_id, project_id))

    def _refresh_memory(self, db, case):
        from .project_memory import decision_records, digest
        wanted = {r.id: r for r in decision_records(case)}
        previous = {row[0]: (row[1], row[2]) for row in db.execute('SELECT id, project_id, digest FROM project_decisions WHERE case_id = ?', (case.id,)).fetchall()}
        for decision_id, (project_id, _) in previous.items():
            if decision_id not in wanted:
                self._remove_decision(db, decision_id, project_id)
        for record in wanted.values():
            checksum = digest(record)
            if record.id in previous and previous[record.id][1] == checksum:
                continue
            db.execute('INSERT INTO project_decisions VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET project_id=excluded.project_id,body=excluded.body,digest=excluded.digest', (record.id, record.project_id, record.case_id, record.model_dump_json(), checksum))
            db.execute('DELETE FROM decision_search WHERE decision_id = ?', (record.id,))
            text = '\n'.join([record.title, record.question, record.answer, record.owner])
            db.execute('INSERT INTO decision_search VALUES (?,?,?)', (record.id, record.project_id, text))
            db.execute("INSERT INTO memory_index_jobs (decision_id,project_id,action,digest) VALUES (?,?,'upsert',?) ON CONFLICT(decision_id) DO UPDATE SET project_id=excluded.project_id,action='upsert',digest=excluded.digest,state='pending',error=''", (record.id, record.project_id, checksum))

    def get_decision(self, decision_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM project_decisions WHERE id = ?', (decision_id,)).fetchone()
        return PriorDecision.model_validate_json(row[0]) if row else None

    def decisions(self, project_id, exclude_case_id=''):
        with self.connect() as db:
            rows = db.execute('SELECT body FROM project_decisions WHERE project_id = ? AND case_id != ? ORDER BY json_extract(body, \'$.created_at\') DESC', (project_id, exclude_case_id)).fetchall()
        return [PriorDecision.model_validate_json(row[0]) for row in rows]

    def search_decisions(self, project_id, exclude_case_id, query):
        stop = {'the','and','for','are','what','this','that','with','from','have','does','before','review','project','decision','should','which'}
        words = list(dict.fromkeys(w for w in re.findall(r'[a-z0-9]{3,}', query.lower()) if w not in stop))[:32]
        records = []
        if words:
            match = ' OR '.join('"' + word + '"' for word in words)
            with self.connect() as db:
                rows = db.execute('SELECT d.body FROM decision_search JOIN project_decisions d ON d.id=decision_search.decision_id WHERE decision_search MATCH ? AND decision_search.project_id=? AND d.case_id!=? ORDER BY bm25(decision_search) LIMIT 8', (match, project_id, exclude_case_id)).fetchall()
            records = [PriorDecision.model_validate_json(row[0]) for row in rows]
        seen = {r.id for r in records}
        for recent in self.decisions(project_id, exclude_case_id):
            if recent.id not in seen:
                records.append(recent)
            if len(records) == 8:
                break
        return records

    def memory_jobs(self, limit=40):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM memory_index_jobs WHERE state!='synced' ORDER BY CASE WHEN action='delete' THEN 0 ELSE 1 END, decision_id LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def memory_remote_id(self, decision_id, remote_id):
        with self.lock, self.connect() as db:
            db.execute('UPDATE memory_index_jobs SET remote_id=? WHERE decision_id=?', (remote_id, decision_id))

    def finish_memory_job(self, job, remote_id):
        with self.lock, self.connect() as db:
            db.execute("UPDATE memory_index_jobs SET remote_id=?,state=CASE WHEN action=? AND digest=? THEN 'synced' ELSE 'pending' END,error='' WHERE decision_id=?", (remote_id, job['action'], job['digest'], job['decision_id']))

    def fail_memory_job(self, job, error):
        with self.lock, self.connect() as db:
            db.execute("UPDATE memory_index_jobs SET state='error',error=? WHERE decision_id=? AND action=? AND digest=?", (error[:300], job['decision_id'], job['action'], job['digest']))

    def memory_job_status(self):
        with self.connect() as db:
            stats = dict(db.execute('SELECT state,COUNT(*) FROM memory_index_jobs GROUP BY state').fetchall())
        return {'pending': stats.get('pending', 0), 'failed': stats.get('error', 0), 'synced': stats.get('synced', 0)}
