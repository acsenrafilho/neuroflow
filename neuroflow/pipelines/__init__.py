"""Pipeline orchestration.

Heavy compute runs in Docker containers (see docker/), not inside FastAPI workers.
Future: submit jobs, track run metadata under derivatives/.
"""
