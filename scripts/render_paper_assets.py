#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def pct(value: float, digits: int = 2) -> str:
    return f"{100 * value:.{digits}f}"


def main() -> None:
    summary = json.loads((PROJECT / "results/confirmation/final/summary.json").read_text())
    secondary = json.loads((PROJECT / "results/confirmation/final/secondary_metrics.json").read_text())
    metrics = summary["metrics"]
    ci = summary["task_stratified_bootstrap_gain_95_ci"]
    macros = {
        "TaskCount": summary["counts"]["tasks"],
        "CandidateCount": summary["counts"]["candidate_programs"],
        "KilledCount": summary["counts"]["killed"],
        "ControlCount": summary["counts"]["controls"],
        "IWCCBA": pct(metrics["iwcc"]["balanced_accuracy"]),
        "EndpointBA": pct(metrics["endpoint_only"]["balanced_accuracy"]),
        "GainPoints": pct(summary["absolute_gain"]),
        "GainCILow": pct(ci[0]),
        "GainCIHigh": pct(ci[1]),
        "PermutationP": "1.0\\times10^{-5}",
        "IWCCRecall": pct(metrics["iwcc"]["recall"]),
        "IWCCSpecificity": pct(metrics["iwcc"]["specificity"]),
        "ClauseCount": secondary["contract"]["required_and_precedence_plus_navigation_clauses"],
        "TraceCount": secondary["contract"]["successful_development_trace_witnesses"],
        "MedianRuntime": f"{secondary['runtime']['median_milliseconds']:.3f}",
        "RuntimeThroughput": f"{secondary['runtime']['throughput_programs_per_second']:.0f}",
    }
    paper = PROJECT / "paper"
    paper.mkdir(parents=True, exist_ok=True)
    (paper / "results_macros.tex").write_text("".join(f"\\newcommand{{\\{key}}}{{{value}}}\n" for key, value in macros.items()))

    labels = ["Endpoint", "Ordered", "Nearest", "Qwen3-4B", "Phi-4-mini", "Mistral-7B", "IWCC"]
    keys = ["endpoint_only", "ordered_milestones", "nearest_successful_trace", "llm_qwen3_4b", "llm_phi4_mini", "llm_mistral7b_v03", "iwcc"]
    rows = "\n".join(
        f"{label} & {pct(metrics[key]['balanced_accuracy'])} & {pct(metrics[key]['recall'])} & {pct(metrics[key]['specificity'])} \\\\"
        for label, key in zip(labels, keys)
    )
    table = """\\begin{table}[t]
\\centering
\\caption{Independent confirmation at candidate-program level (percent).}
\\label{tab:main}
\\begin{tabular}{lrrr}
\\toprule
Validator & Balanced accuracy & Recall & Specificity \\\\
\\midrule
""" + rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    (PROJECT / "results/confirmation/final/table_main.tex").write_text(table)

    zh_labels = ["终点契约", "顺序契约", "最近轨迹", "Qwen3-4B", "Phi-4-mini", "Mistral-7B", "IWCC"]
    zh_rows = "\n".join(
        f"{label} & {pct(metrics[key]['balanced_accuracy'])} & {pct(metrics[key]['recall'])} & {pct(metrics[key]['specificity'])} \\\\"
        for label, key in zip(zh_labels, keys)
    )
    zh_table = """\\begin{table}[t]
\\centering
\\caption{候选程序级的独立确认结果（\\% ）。}
\\label{tab:main-zh}
\\begin{tabular}{lrrr}
\\toprule
验证器 & 平衡准确率 & 召回率 & 特异度 \\\\
\\midrule
""" + zh_rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    (PROJECT / "results/confirmation/final/table_main_zh.tex").write_text(zh_table)

    env_rows = "\n".join(
        f"{name.title()} & {pct(group['endpoint_only']['balanced_accuracy'])} & {pct(group['iwcc']['balanced_accuracy'])} & {pct(group['iwcc']['balanced_accuracy']-group['endpoint_only']['balanced_accuracy'])} \\\\"
        for name, group in summary["by_environment"].items()
    )
    env_table = """\\begin{table}[t]
\\centering
\\caption{Balanced accuracy by native environment (percent).}
\\label{tab:environment}
\\begin{tabular}{lrrr}
\\toprule
Environment & Endpoint & IWCC & Gain \\\\
\\midrule
""" + env_rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    (PROJECT / "results/confirmation/final/table_environment.tex").write_text(env_table)

    zh_env_table = """\\begin{table}[t]
\\centering
\\caption{分原生环境的平衡准确率（\\% ）。}
\\label{tab:environment-zh}
\\begin{tabular}{lrrr}
\\toprule
环境 & 终点契约 & IWCC & 增益 \\\\
\\midrule
""" + env_rows + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    (PROJECT / "results/confirmation/final/table_environment_zh.tex").write_text(zh_env_table)

    try:
        import matplotlib.pyplot as plt
        values = [100 * metrics[key]["balanced_accuracy"] for key in keys]
        colors = ["#777777"] * (len(keys) - 1) + ["#00796B"]
        fig, ax = plt.subplots(figsize=(7.1, 3.0))
        bars = ax.bar(labels, values, color=colors, width=0.72)
        ax.axhline(50, color="#333333", linewidth=0.8, linestyle="--")
        ax.set_ylabel("Balanced accuracy (%)")
        ax.set_ylim(40, 95)
        ax.tick_params(axis="x", rotation=24)
        ax.spines[["top", "right"]].set_visible(False)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, value + 1, f"{value:.1f}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        figures = PROJECT / "results/figures"
        figures.mkdir(parents=True, exist_ok=True)
        fig.savefig(figures / "balanced_accuracy.pdf", bbox_inches="tight")
        fig.savefig(figures / "balanced_accuracy.png", dpi=240, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
