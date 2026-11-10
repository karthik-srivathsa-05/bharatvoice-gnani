import sqlite3
from .engine import Session

class Conflict(Exception): pass
class Store:
    def __init__(self,path):
        self.path=path
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, version INTEGER NOT NULL, payload TEXT NOT NULL)')
    def connect(self):
        c=sqlite3.connect(self.path,timeout=10);c.execute('PRAGMA journal_mode=WAL');return c
    def create(self):
        s=Session()
        with self.connect() as c:c.execute('INSERT INTO sessions VALUES(?,?,?)',(s.id,s.version,s.model_dump_json()))
        return s
    def get(self,sid):
        with self.connect() as c:r=c.execute('SELECT payload FROM sessions WHERE id=?',(sid,)).fetchone()
        if not r: raise KeyError(sid)
        return Session.model_validate_json(r[0])
    def save(self,s,previous):
        with self.connect() as c:
            cur=c.execute('UPDATE sessions SET version=?,payload=? WHERE id=? AND version=?',(s.version,s.model_dump_json(),s.id,previous))
            if cur.rowcount!=1: raise Conflict('Session changed; resume and retry.')
