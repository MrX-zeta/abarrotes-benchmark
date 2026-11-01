"""Lectura directa de los contadores cgroup del contenedor del motor (v2, con respaldo v1).

Son los mismos archivos que lee cAdvisor; se usan como fuente de respaldo si Prometheus no
tiene datos y para detectar OOM dentro del contenedor (memory.events oom_kill).
"""
import glob
import os

ROOT = os.environ.get("HOST_CGROUP_ROOT", "/sys/fs/cgroup")


def _read_kv(path):
    out = {}
    try:
        with open(path) as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2:
                    try:
                        out[parts[0]] = int(parts[1])
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


class Cgroup:
    def __init__(self, container_id):
        self.cid = container_id
        self.version = 2 if os.path.exists(os.path.join(ROOT, "cgroup.controllers")) else 1
        self.path = self._find()

    def _find(self):
        cid = self.cid
        if self.version == 2:
            cands = [f"{ROOT}/docker/{cid}", f"{ROOT}/system.slice/docker-{cid}.scope"]
            cands += glob.glob(f"{ROOT}/**/*{cid}*", recursive=True)[:5]
        else:
            cands = [f"{ROOT}/memory/docker/{cid}", f"{ROOT}/memory/system.slice/docker-{cid}.scope"]
            cands += glob.glob(f"{ROOT}/memory/**/*{cid}*", recursive=True)[:5]
        for c in cands:
            if os.path.isdir(c):
                return c
        return None

    def _v1(self, controller):
        return self.path.replace(f"{ROOT}/memory/", f"{ROOT}/{controller}/", 1)

    def sample(self):
        if not self.path:
            return None
        if self.version == 2:
            mem = _read_kv(f"{self.path}/memory.stat")
            cpu = _read_kv(f"{self.path}/cpu.stat")
            ev = _read_kv(f"{self.path}/memory.events")
            cur = _read(f"{self.path}/memory.current")
            return {
                "rss_bytes": mem.get("anon"),
                "mem_current_bytes": int(cur) if cur and cur.isdigit() else None,
                "throttled_s": cpu.get("throttled_usec", 0) / 1e6,
                "nr_throttled": cpu.get("nr_throttled"),
                "cpu_usage_s": cpu.get("usage_usec", 0) / 1e6,
                "oom_kill": ev.get("oom_kill", 0),
            }
        mem = _read_kv(f"{self.path}/memory.stat")
        cpu = _read_kv(f"{self._v1('cpu')}/cpu.stat")
        usage = _read(f"{self._v1('cpuacct')}/cpuacct.usage")
        oomc = _read_kv(f"{self.path}/memory.oom_control")
        cur = _read(f"{self.path}/memory.usage_in_bytes")
        return {
            "rss_bytes": mem.get("total_rss", mem.get("rss")),
            "mem_current_bytes": int(cur) if cur and cur.isdigit() else None,
            "throttled_s": cpu.get("throttled_time", 0) / 1e9,
            "nr_throttled": cpu.get("nr_throttled"),
            "cpu_usage_s": int(usage) / 1e9 if usage and usage.isdigit() else None,
            "oom_kill": oomc.get("oom_kill", 0),
        }

    def limits(self):
        """Límites realmente aplicados por el kernel (diapositiva: anotar límites reales)."""
        if not self.path:
            return {"cgroup_path": None}
        if self.version == 2:
            return {
                "cgroup_version": 2,
                "cgroup_path": self.path,
                "cpu.max": _read(f"{self.path}/cpu.max"),
                "cpuset.cpus.effective": _read(f"{self.path}/cpuset.cpus.effective"),
                "memory.max": _read(f"{self.path}/memory.max"),
                "memory.swap.max": _read(f"{self.path}/memory.swap.max"),
            }
        return {
            "cgroup_version": 1,
            "cgroup_path": self.path,
            "cpu.cfs_quota_us": _read(f"{self._v1('cpu')}/cpu.cfs_quota_us"),
            "cpu.cfs_period_us": _read(f"{self._v1('cpu')}/cpu.cfs_period_us"),
            "memory.limit_in_bytes": _read(f"{self.path}/memory.limit_in_bytes"),
            "memory.memsw.limit_in_bytes": _read(f"{self.path}/memory.memsw.limit_in_bytes"),
            "memory.swappiness": _read(f"{self.path}/memory.swappiness"),
        }
