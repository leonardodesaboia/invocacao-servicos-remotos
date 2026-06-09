"""
Gera os gráficos de comparação a partir de loadtest/results/results.csv.

Saídas (em loadtest/results/):
  Originais — escala absoluta (sem log):
    throughput_<op>.png
    latency_<op>.png
    throughput_vs_carga_<op>.png

  Por linguagem (4 APIs juntas):
    throughput_lang_<lang>_<op>.png
    latency_lang_<lang>_<op>.png

  Por tecnologia (2 linguagens):
    throughput_tech_<tech>_<op>.png
    latency_tech_<tech>_<op>.png

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

TECHS = ["REST", "GraphQL", "gRPC", "SOAP"]
LANGS = ["Python", "Node"]
ORDER = [(t, l) for t in TECHS for l in LANGS]
TECH_COLOR = {"REST": "#4C72B0", "GraphQL": "#DD8452", "gRPC": "#55A868", "SOAP": "#C44E52"}
LANG_COLOR = {"Python": "#9467BD", "Node": "#8C564B"}


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


def _annotate_bar(ax, bar, val, err_count, fontsize=7, show_val=True):
    """Rótulo de valor e aviso de erros acima de uma barra."""
    x = bar.get_x() + bar.get_width() / 2
    y = bar.get_height()
    if err_count > 0:
        label = (f"{val:.0f}\n⚠{err_count} erros" if show_val else f"⚠{err_count} erros")
        ax.text(x, y, label, ha="center", va="bottom", fontsize=fontsize,
                color="red", fontweight="bold")
    elif show_val:
        ax.text(x, y, f"{val:.0f}", ha="center", va="bottom", fontsize=fontsize)


def _smart_ylim(ax, all_vals):
    """Limita o eixo Y ao p95 dos valores × 1.4 quando existem outliers extremos.
    Valores truncados são visíveis via rótulo vermelho."""
    valid = sorted(v for v in all_vals if v > 0)
    if not valid:
        return False
    p95_idx = int(len(valid) * 0.95)
    cap = valid[min(p95_idx, len(valid) - 1)] * 1.4
    if max(valid) > cap * 1.5:
        ax.set_ylim(0, cap)
        ax.annotate("⚠ Barras cortadas — valor real indicado em vermelho",
                    xy=(0.01, 0.985), xycoords="axes fraction",
                    fontsize=7, color="red", va="top")
        return True
    return False


# ---------------------------------------------------------------------------
# Gráfico 1: grouped bars — todas as 8 implementações (original, escala absoluta)
# ---------------------------------------------------------------------------

def grouped_bars(rows, op, metric, ylabel, title, fname):
    levels = sorted({r["concurrency"] for r in rows if r["operation"] == op})
    data = defaultdict(dict)
    errs = defaultdict(dict)
    for r in rows:
        if r["operation"] == op:
            data[(r["tech"], r["lang"])][r["concurrency"]] = r[metric]
            errs[(r["tech"], r["lang"])][r["concurrency"]] = r["errors"]

    labels = [f"{t}\n{l}" for (t, l) in ORDER]
    colors = [TECH_COLOR[t] for (t, l) in ORDER]
    n = len(ORDER)
    width = 0.8 / len(levels)
    fig, ax = plt.subplots(figsize=(14, 6))
    xs = list(range(n))
    all_vals = []

    for i, c in enumerate(levels):
        vals = [data[key].get(c, 0) for key in ORDER]
        err_counts = [errs[key].get(c, 0) for key in ORDER]
        all_vals.extend(vals)
        offs = [x + i * width - 0.4 + width / 2 for x in xs]
        bars = ax.bar(offs, vals, width, label=f"{c} usuários",
                      color=colors,
                      alpha=0.55 + 0.45 * (i / max(1, len(levels) - 1)),
                      edgecolor="black", linewidth=0.4)
        # Rótulo em todas as barras: valor no último nível; só erros nos demais
        for j, (b, v, e) in enumerate(zip(bars, vals, err_counts)):
            _annotate_bar(ax, b, v, e, fontsize=6, show_val=(i == len(levels) - 1))

    _smart_ylim(ax, all_vals)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(title="Carga (concorrência)")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    out = os.path.join(RESULTS, fname)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print("gerado", out)


# ---------------------------------------------------------------------------
# Gráfico 2: linha de vazão × carga (original)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Gráfico 3: por linguagem — 4 APIs juntas
# ---------------------------------------------------------------------------

def lang_bars(rows, op, metric, ylabel, title_prefix, fname_prefix):
    """Um gráfico por linguagem mostrando as 4 tecnologias lado a lado."""
    levels = sorted({r["concurrency"] for r in rows if r["operation"] == op})

    for lang in LANGS:
        data = defaultdict(dict)
        errs = defaultdict(dict)
        for r in rows:
            if r["operation"] == op and r["lang"] == lang:
                data[r["tech"]][r["concurrency"]] = r[metric]
                errs[r["tech"]][r["concurrency"]] = r["errors"]

        n = len(TECHS)
        width = 0.8 / len(levels)
        fig, ax = plt.subplots(figsize=(10, 6))
        xs = list(range(n))
        all_vals = []

        for i, c in enumerate(levels):
            vals = [data[t].get(c, 0) for t in TECHS]
            err_counts = [errs[t].get(c, 0) for t in TECHS]
            all_vals.extend(vals)
            offs = [x + i * width - 0.4 + width / 2 for x in xs]
            bars = ax.bar(offs, vals, width, label=f"{c} usuários",
                          color=[TECH_COLOR[t] for t in TECHS],
                          alpha=0.55 + 0.45 * (i / max(1, len(levels) - 1)),
                          edgecolor="black", linewidth=0.4)
            for b, v, e in zip(bars, vals, err_counts):
                _annotate_bar(ax, b, v, e, fontsize=7, show_val=(i == len(levels) - 1))

        _smart_ylim(ax, all_vals)
        ax.set_xticks(xs)
        ax.set_xticklabels(TECHS, fontsize=11)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{title_prefix} — {lang}")
        ax.legend(title="Carga")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        out = os.path.join(RESULTS, f"{fname_prefix}_{lang.lower()}_{op}.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        print("gerado", out)


# ---------------------------------------------------------------------------
# Gráfico 4: por tecnologia — 2 linguagens
# ---------------------------------------------------------------------------

def tech_bars(rows, op, metric, ylabel, title_prefix, fname_prefix):
    """Um gráfico por tecnologia mostrando Python vs Node."""
    levels = sorted({r["concurrency"] for r in rows if r["operation"] == op})

    for tech in TECHS:
        data = defaultdict(dict)
        errs = defaultdict(dict)
        for r in rows:
            if r["operation"] == op and r["tech"] == tech:
                data[r["lang"]][r["concurrency"]] = r[metric]
                errs[r["lang"]][r["concurrency"]] = r["errors"]

        n = len(LANGS)
        width = 0.8 / len(levels)
        fig, ax = plt.subplots(figsize=(8, 5))
        xs = list(range(n))
        all_vals = []

        for i, c in enumerate(levels):
            vals = [data[l].get(c, 0) for l in LANGS]
            err_counts = [errs[l].get(c, 0) for l in LANGS]
            all_vals.extend(vals)
            offs = [x + i * width - 0.4 + width / 2 for x in xs]
            bars = ax.bar(offs, vals, width, label=f"{c} usuários",
                          color=[LANG_COLOR[l] for l in LANGS],
                          alpha=0.55 + 0.45 * (i / max(1, len(levels) - 1)),
                          edgecolor="black", linewidth=0.4)
            for b, v, e in zip(bars, vals, err_counts):
                _annotate_bar(ax, b, v, e, fontsize=8, show_val=True)

        _smart_ylim(ax, all_vals)
        ax.set_xticks(xs)
        ax.set_xticklabels(LANGS, fontsize=12)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{title_prefix} — {tech}")
        ax.legend(title="Carga")
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        out = os.path.join(RESULTS, f"{fname_prefix}_{tech.lower()}_{op}.png")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        print("gerado", out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rows = load()
    ops = sorted({r["operation"] for r in rows})
    nomes = {
        "listMusics": "listar todas as músicas (payload grande, 500 itens)",
        "musicsByPlaylist": "músicas de uma playlist (payload pequeno, ~22 itens)",
    }

    # Diagnóstico: casos com erros elevados
    print("\n=== Casos com erros > 0 ===")
    for r in rows:
        if r["errors"] > 0:
            pct = 100 * r["errors"] / r["requests"] if r["requests"] else 0
            print(f"  {r['lang']:6} {r['tech']:7} {r['operation']:18} "
                  f"conc={r['concurrency']:3}  erros={r['errors']:4} ({pct:.0f}%)  "
                  f"p95={r['p95_ms']:.0f}ms  tput={r['throughput']:.1f}req/s")
    print()

    for op in ops:
        desc = nomes.get(op, op)

        # --- Gráficos originais em escala absoluta ---
        grouped_bars(rows, op, "throughput", "Vazão (req/s)",
                     f"Vazão por tecnologia — {desc}", f"throughput_{op}.png")
        grouped_bars(rows, op, "p95_ms", "Latência p95 (ms)",
                     f"Latência p95 por tecnologia — {desc}", f"latency_{op}.png")
        line_throughput(rows, op, f"throughput_vs_carga_{op}.png")

        # --- Por linguagem (4 APIs juntas) ---
        lang_bars(rows, op, "throughput", "Vazão (req/s)",
                  f"Vazão por API — {desc}", "throughput_lang")
        lang_bars(rows, op, "p95_ms", "Latência p95 (ms)",
                  f"Latência p95 por API — {desc}", "latency_lang")

        # --- Por tecnologia (Python vs Node) ---
        tech_bars(rows, op, "throughput", "Vazão (req/s)",
                  f"Vazão por linguagem — {desc}", "throughput_tech")
        tech_bars(rows, op, "p95_ms", "Latência p95 (ms)",
                  f"Latência p95 por linguagem — {desc}", "latency_tech")


if __name__ == "__main__":
    main()
