"""
Gerador de carga / benchmark das 8 versões do serviço de streaming.

Para cada versão (4 tecnologias x 2 linguagens) o script:
  1. Sobe o servidor como subprocesso (isolado, um por vez = comparação justa).
  2. Espera ficar pronto.
  3. Aplica duas operações representativas, sob VÁRIOS níveis de carga
     (concorrência), medindo vazão (req/s) e latência (média, p50, p95).
  4. Encerra o servidor.

Operações medidas:
  - listMusics       -> retorna as 500 músicas (payload grande: estressa
                        serialização/transferência).
  - musicsByPlaylist -> retorna ~22 músicas de uma playlist (payload pequeno:
                        estressa o overhead por requisição).

Resultados salvos em loadtest/results/results.csv (consumido por plot.py).

Uso:
  python loadtest.py                 # cargas padrão (10, 50, 100), 5s cada
  python loadtest.py --duration 3 --levels 20 100
"""
import argparse
import csv
import os
import socket
import statistics
import subprocess
import sys
import threading
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable
RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "python", "grpc"))
import grpc                       # noqa: E402
import streaming_pb2 as pb        # noqa: E402
import streaming_pb2_grpc as pbg  # noqa: E402

# ---------------------------------------------------------------------------
# Definição das 8 versões: como subir, em que porta, e como falar com elas.
# ---------------------------------------------------------------------------
SERVICES = [
    # (lang, tech, port, [cmd...], cwd)
    ("Python", "REST",    8001, [VENV_PY, "python/rest/server.py"],     ROOT),
    ("Python", "GraphQL", 8002, [VENV_PY, "python/graphql/server.py"],  ROOT),
    ("Python", "gRPC",    8003, [VENV_PY, "python/grpc/server.py"],     ROOT),
    ("Python", "SOAP",    8004, [VENV_PY, "python/soap/server.py"],     ROOT),
    ("Node",   "REST",    8101, ["node", "rest/server.js"],            os.path.join(ROOT, "node")),
    ("Node",   "GraphQL", 8102, ["node", "graphql/server.js"],        os.path.join(ROOT, "node")),
    ("Node",   "gRPC",    8103, ["node", "grpc/server.js"],           os.path.join(ROOT, "node")),
    ("Node",   "SOAP",    8104, ["node", "soap/server.js"],           os.path.join(ROOT, "node")),
]

SOAP_ENV = ('<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:tns="{ns}"><soapenv:Body><tns:{op}>{body}</tns:{op}>'
            '</soapenv:Body></soapenv:Envelope>')


def wait_ready(tech, port, timeout=30):
    """Espera o servidor aceitar conexões e responder."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass
            if tech == "gRPC":
                ch = grpc.insecure_channel(f"127.0.0.1:{port}")
                grpc.channel_ready_future(ch).result(timeout=2)
                ch.close()
            return True
        except Exception:
            time.sleep(0.3)
    return False


# ---------------------------------------------------------------------------
# Clientes: cada um retorna uma função call() que faz UMA requisição da
# operação pedida e levanta exceção em caso de erro.
# ---------------------------------------------------------------------------
def make_caller(lang, tech, port, op):
    if tech == "REST":
        s = requests.Session()
        path = "/musics" if op == "listMusics" else "/playlists/1/musics"
        url = f"http://127.0.0.1:{port}{path}"

        def call():
            r = s.get(url)
            r.raise_for_status()
            return len(r.content)
        return call

    if tech == "GraphQL":
        s = requests.Session()
        if op == "listMusics":
            q = "{ musics { id nome artista ano album } }"
        else:
            q = "{ musicsByPlaylist(playlistId: 1) { id nome artista ano album } }"
        url = f"http://127.0.0.1:{port}/graphql"

        def call():
            r = s.post(url, json={"query": q})
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                raise RuntimeError(data["errors"])
            return len(r.content)
        return call

    if tech == "SOAP":
        s = requests.Session()
        ns = "streaming.soap" if lang == "Python" else "http://streaming.soap/"
        if op == "listMusics":
            envelope = SOAP_ENV.format(ns=ns, op="listMusics", body="")
            action = "listMusics"
        else:
            envelope = SOAP_ENV.format(ns=ns, op="musicsByPlaylist",
                                       body="<tns:playlistId>1</tns:playlistId>")
            action = "musicsByPlaylist"
        path = "/" if lang == "Python" else "/wsdl"
        url = f"http://127.0.0.1:{port}{path}"
        data = envelope.encode("utf-8")
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": action}

        def call():
            r = s.post(url, data=data, headers=headers)
            r.raise_for_status()
            if "Fault>" in r.text:
                raise RuntimeError("SOAP Fault")
            return len(r.content)
        return call

    if tech == "gRPC":
        ch = grpc.insecure_channel(f"127.0.0.1:{port}")
        stub = pbg.StreamingServiceStub(ch)

        def call():
            if op == "listMusics":
                resp = stub.ListMusics(pb.Empty())
                return len(resp.musics)
            resp = stub.MusicsByPlaylist(pb.IdRequest(id=1))
            return len(resp.musics)
        return call

    raise ValueError(tech)


# ---------------------------------------------------------------------------
# Motor de carga: N threads batendo no serviço por `duration` segundos.
# ---------------------------------------------------------------------------
def run_load(make_call, concurrency, duration):
    stop = threading.Event()
    latencies_all = []
    errors_all = [0]
    lock = threading.Lock()

    def worker():
        call = make_call()  # cliente próprio por thread (sessões não são thread-safe)
        lats = []
        errs = 0
        while not stop.is_set():
            t0 = time.perf_counter()
            try:
                call()
                lats.append((time.perf_counter() - t0) * 1000.0)  # ms
            except Exception:
                errs += 1
        with lock:
            latencies_all.extend(lats)
            errors_all[0] += errs

    threads = [threading.Thread(target=worker) for _ in range(concurrency)]
    t_start = time.perf_counter()
    for t in threads:
        t.start()
    time.sleep(duration)
    stop.set()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t_start

    n = len(latencies_all)
    if n == 0:
        return {"requests": 0, "errors": errors_all[0], "throughput": 0.0,
                "avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}
    latencies_all.sort()
    return {
        "requests": n,
        "errors": errors_all[0],
        "throughput": n / elapsed,
        "avg_ms": statistics.fmean(latencies_all),
        "p50_ms": latencies_all[int(0.50 * (n - 1))],
        "p95_ms": latencies_all[int(0.95 * (n - 1))],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=5.0, help="segundos por carga")
    ap.add_argument("--levels", type=int, nargs="+", default=[10, 50, 100],
                    help="níveis de concorrência (>=2 para mostrar diferença)")
    ap.add_argument("--operations", nargs="+", default=["listMusics", "musicsByPlaylist"])
    ap.add_argument("--warmup", type=float, default=1.0, help="segundos de aquecimento")
    args = ap.parse_args()

    rows = []
    for lang, tech, port, cmd, cwd in SERVICES:
        label = f"{tech}/{lang}"
        print(f"\n=== {label} (porta {port}) ===")
        env = dict(os.environ, PORT=str(port))
        proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if not wait_ready(tech, port):
                print(f"  !! {label} não ficou pronto — pulando")
                continue
            time.sleep(0.5)
            for op in args.operations:
                # aquecimento (não medido)
                warm = make_caller(lang, tech, port, op)
                if args.warmup > 0:
                    run_load(lambda: warm, max(args.levels[0], 4), args.warmup)
                for c in args.levels:
                    res = run_load(lambda: make_caller(lang, tech, port, op), c, args.duration)
                    res.update({"lang": lang, "tech": tech, "operation": op, "concurrency": c})
                    rows.append(res)
                    print(f"  {op:18s} c={c:4d}  {res['throughput']:8.1f} req/s  "
                          f"avg={res['avg_ms']:7.2f}ms  p95={res['p95_ms']:7.2f}ms  "
                          f"erros={res['errors']}")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            time.sleep(0.5)

    out = os.path.join(RESULTS, "results.csv")
    cols = ["lang", "tech", "operation", "concurrency", "requests", "errors",
            "throughput", "avg_ms", "p50_ms", "p95_ms"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})
    print(f"\nResultados salvos em {out}  ({len(rows)} linhas)")


if __name__ == "__main__":
    main()
