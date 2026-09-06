"""Startup memory/time profiler for Render Free capacity checks (Part 22).

Measures at each stage:
    - import time
    - RSS memory before import
    - RSS after `import app.main`
    - RSS after FastAPI app initialization / lifespan

Complements scripts/memory_report.py, which additionally exercises
representative API requests. This script stays import-only so it can run in
the exact same way the container starts the application.

Usage:
    cd backend
    python scripts/profile_startup.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _rss_mb() -> float:
    """Best-effort RSS (psutil -> /proc -> WinAPI -> 0)."""
    try:
        import psutil  # type: ignore
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        pass
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class _PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        pmc = _PMC()
        pmc.cb = ctypes.sizeof(_PMC)
        if ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb
        ):
            return pmc.WorkingSetSize / (1024 * 1024)
    return 0.0


def main() -> int:
    print("=" * 70)
    print("TrustLens startup profile (Render Free target: <150 MB idle)")
    print("=" * 70)

    rss0 = _rss_mb()
    print(f"RSS before import:                {rss0:8.1f} MB")

    t0 = time.perf_counter()
    import app.main  # noqa: E402
    import_ms = (time.perf_counter() - t0) * 1000.0
    rss1 = _rss_mb()
    print(f"RSS after  import app.main:       {rss1:8.1f} MB  (+{rss1 - rss0:.1f} MB, {import_ms:.0f} ms)")

    t1 = time.perf_counter()
    fastapi_app = app.main.app  # FastAPI instance (router already mounted)
    init_ms = (time.perf_counter() - t1) * 1000.0
    rss2 = _rss_mb()
    print(f"RSS after  FastAPI initialized:   {rss2:8.1f} MB  (+{rss2 - rss1:.1f} MB, {init_ms:.1f} ms)")
    print(f"FastAPI app object:               {type(fastapi_app).__name__} "
          f"routes={len(fastapi_app.routes)}")

    # Newer FastAPI versions lazy-include routers (_IncludedRouter), so
    # app.routes undercounts; the OpenAPI schema lists real endpoint paths.
    try:
        endpoint_paths = len(fastapi_app.openapi().get("paths", {}))
        print(f"OpenAPI endpoint paths:           {endpoint_paths}")
    except Exception:  # noqa: BLE001 - diagnostics must never fail
        pass


    heavy = [m for m in ("torch", "transformers", "sentence_transformers", "faiss", "spacy")
             if m in sys.modules]
    print(f"Heavy modules loaded:             {heavy if heavy else 'NONE'}")

    ok = rss2 < 150.0 and not heavy
    print("-" * 70)
    print(f"RESULT: {'PASS' if ok else 'FAIL'} "
          f"(idle RSS {rss2:.1f} MB, budget 150 MB; heavy modules {'absent' if not heavy else 'PRESENT'})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())