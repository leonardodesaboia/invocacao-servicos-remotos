"""
Gera os gráficos de comparação a partir de loadtest/results/results.csv.

Saídas (em loadtest/results/):
  - throughput_<op>.png : vazão (req/s) por versão, agrupada por nível de carga
  - latency_<op>.png    : latência p95 (ms) por versão, agrupada por carga
  - throughput_vs_carga_<op>.png : vazão x concorrência (linhas), uma por versão

Uso:  python plot.py
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
CSV = os.path.join(RESULTS, "results.csv")

# ordem fixa das 8 versões e cores por tecnologia
TECHS = ["REST", "GraphQL", "gRPC", "SOAP"]
LANGS = ["Python", "Node"]
ORDER = [(t, l) for t in TECHS for l in LANGS]
TECH_COLOR = {"REST": "#4C72B0", "GraphQL": "#DD8452", "gRPC": "#55A868", "SOAP": "#C44E52"}


def load():
    rows = []
    with open(CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for k in ("concurrency", "requests", "errors"):
                r[k] = int(float(r[k]))
            for k in ("throughput", "avg_ms", "p50_ms", "p95_ms"):
                r[k] = float(r[k])
            rows.append(r)
    return rows


def labels_and_colors():
    labels = [f"{t}\n{l}" for (t, l) in ORDER]
    colors = [TECH_COLOR[t] for (t, l) in ORDER]
    return labels, colors


def grouped_bars(rows, op, metric, ylabel, title, fname, logy=False):
    levels = sorted({r["concurrency"] for r in rows if r["operation"] == op})
    data = defaultdict(dict)  # (tech,lang) -> {conc: value}
    for r in rows:
        if r["operation"] == op:
            data[(r["tech"], r["lang"])][r["concurrency"]] = r[metric]

    labels, colors = labels_and_colors()
    n = len(ORDER)
    width = 0.8 / len(levels)
    fig, ax = plt.subplots(figsize=(12, 6))
    xs = range(n)
    for i, c in enumerate(levels):
        vals = [data[key].get(c, 0) for key in ORDER]
        offs = [x + i * width - 0.4 + width / 2 for x in xs]
        bars = ax.bar(offs, vals, width, label=f"{c} usuários",
                      color=[colors[j] for j in range(n)],
                      alpha=0.55 + 0.45 * (i / max(1, len(levels) - 1)),
                      edgecolor="black", linewidth=0.4)
        # rótulo só na maior carga p/ não poluir
        if i == len(levels) - 1:
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}",
                        ha="center", va="bottom", fontsize=7)

    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if logy:
        ax.set_yscale("log")
    ax.legend(title="Carga (concorrência)")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    out = os.path.join(RESULTS, fname)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print("gerado", out)


def line_throughput(rows, op, fname):
    levels = sorted({r["concurrency"] for r in rows if r["operation"] == op})
    data = defaultdict(dict)
    for r in rows:
        if r["operation"] == op:
            data[(r["tech"], r["lang"])][r["concurrency"]] = r["throughput"]

    fig, ax = plt.subplots(figsize=(10, 6))
    styles = {"Python": "--", "Node": "-"}
    markers = {"Python": "o", "Node": "s"}
    for (t, l) in ORDER:
        ys = [data[(t, l)].get(c, 0) for c in levels]
        ax.plot(levels, ys, styles[l], marker=markers[l], color=TECH_COLOR[t],
                label=f"{t}/{l}")
    ax.set_xlabel("Concorrência (usuários simultâneos)")
    ax.set_ylabel("Vazão (req/s)")
    ax.set_title(f"Vazão x carga — operação {op}")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    out = os.path.join(RESULTS, fname)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print("gerado", out)


def main():
    rows = load()
    ops = sorted({r["operation"] for r in rows})
    nomes = {"listMusics": "listar todas as músicas (payload grande, 500 itens)",
             "musicsByPlaylist": "músicas de uma playlist (payload pequeno, ~22 itens)"}
    for op in ops:
        desc = nomes.get(op, op)
        grouped_bars(rows, op, "throughput", "Vazão (req/s)",
                     f"Vazão por tecnologia — {desc}", f"throughput_{op}.png")
        grouped_bars(rows, op, "p95_ms", "Latência p95 (ms)",
                     f"Latência p95 por tecnologia — {desc}", f"latency_{op}.png",
                     logy=True)
        line_throughput(rows, op, f"throughput_vs_carga_{op}.png")


if __name__ == "__main__":
    main()
