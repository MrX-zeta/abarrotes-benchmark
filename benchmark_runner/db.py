"""Conexiones y ejecución de consultas para ambos motores."""
import json
import os
import time

ROOT = os.environ.get("BENCH_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/?directConnection=true")
MONGO_DB = os.environ.get("MONGO_DB", "abarrotes")
PG_DSN = os.environ.get("PG_DSN", "postgresql://bench:bench@localhost:5432/abarrotes")
COLLECTION = "pedidos"


def load_variants():
    with open(os.path.join(ROOT, "queries", "variants.json"), encoding="utf-8") as f:
        v = json.load(f)
    v.pop("_descripcion", None)
    return v


def load_query(engine, query_id):
    """Devuelve (texto_o_pipeline, opciones) para engine/query_id."""
    spec = load_variants()[query_id][engine]
    if engine == "mongodb":
        with open(os.path.join(ROOT, spec["pipeline"]), encoding="utf-8") as f:
            return json.load(f), {"allowDiskUse": spec["allowDiskUse"]}
    with open(os.path.join(ROOT, spec["sql"]), encoding="utf-8") as f:
        return f.read(), {"work_mem": spec["work_mem"]}


# ---------------------------------------------------------------------------------------- MongoDB
def mongo_client(**kw):
    from pymongo import MongoClient
    return MongoClient(MONGO_URI, maxPoolSize=1, serverSelectionTimeoutMS=5000, **kw)


def mongo_count():
    c = mongo_client()
    try:
        return c[MONGO_DB][COLLECTION].estimated_document_count()
    finally:
        c.close()


class MongoExecutor:
    def __init__(self, pipeline, opts):
        self.client = mongo_client(socketTimeoutMS=None)
        self.coll = self.client[MONGO_DB][COLLECTION]
        self.pipeline = pipeline
        self.allow_disk = opts.get("allowDiskUse")

    def run(self, timeout_s):
        kw = {"maxTimeMS": max(1, int(timeout_s * 1000))}
        if self.allow_disk is not None:
            kw["allowDiskUse"] = self.allow_disk
        return len(list(self.coll.aggregate(self.pipeline, **kw)))

    @staticmethod
    def classify(exc):
        code = getattr(exc, "code", None)
        if code == 50:  # MaxTimeMSExpired
            return "timeout", code
        return "error", code

    def close(self):
        self.client.close()


# ------------------------------------------------------------------------------------- PostgreSQL
def pg_connect():
    import psycopg
    return psycopg.connect(PG_DSN, autocommit=True, connect_timeout=5)


def pg_count():
    with pg_connect() as conn:
        return conn.execute("SELECT count(*) FROM pedidos").fetchone()[0]


class PgExecutor:
    def __init__(self, sql, opts):
        self.conn = pg_connect()
        self.sql = sql
        if opts.get("work_mem"):
            self.conn.execute(f"SET work_mem = '{opts['work_mem']}'")

    def run(self, timeout_s):
        cur = self.conn.cursor()
        cur.execute(f"SET statement_timeout = {max(1, int(timeout_s * 1000))}")
        cur.execute(self.sql)
        return len(cur.fetchall())

    @staticmethod
    def classify(exc):
        code = getattr(exc, "sqlstate", None)
        if code == "57014":  # query_canceled (statement_timeout)
            return "timeout", code
        return "error", code

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def executor(engine, query_id):
    q, opts = load_query(engine, query_id)
    return MongoExecutor(q, opts) if engine == "mongodb" else PgExecutor(q, opts)


def wait_ready(engine, timeout=180):
    """Espera a que el motor acepte conexiones y tenga los datos cargados (sin healthcheck interno)."""
    t_end = time.time() + timeout
    last = None
    while time.time() < t_end:
        try:
            n = mongo_count() if engine == "mongodb" else pg_count()
            return n
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1)
    raise RuntimeError(f"{engine} no respondió en {timeout}s: {last}")


# ----------------------------------------------------------------------------- contadores de spill
def spill_counters(engine):
    """Contadores acumulados del motor relacionados con volcado a disco (lectura ligera)."""
    if engine == "postgresql":
        with pg_connect() as conn:
            r = conn.execute(
                "SELECT temp_files, temp_bytes FROM pg_stat_database WHERE datname = current_database()"
            ).fetchone()
        return {"temp_files": int(r[0]), "temp_bytes": int(r[1])}
    c = mongo_client()
    try:
        ss = c.admin.command("serverStatus")
    finally:
        c.close()
    out = {}

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            low = path.lower()
            if "spill" in low or "useddisk" in low:
                out[path] = o
    walk(ss.get("metrics", {}), "metrics")
    return out
