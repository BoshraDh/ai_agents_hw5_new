"""CLI entry point — argument parsing only, all logic delegated to LocalLLMBenchSDK."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_llm_bench.sdk import LocalLLMBenchSDK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local LLM Bench — baseline vs AirLLM vs quantized")
    parser.add_argument(
        "--mode", required=True,
        choices=["baseline", "airllm", "quantized", "full-suite", "report", "hardware",
                 "economic", "roofline"],
    )
    parser.add_argument("--prompt", default="Explain how virtual memory works in one paragraph.")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--quant-level", default="Q4_K_M")
    parser.add_argument("--results-path", default="results")
    parser.add_argument("--avg-run-seconds", type=float, default=5.0,
                         help="Assumed avg. run time per request for economic analysis")
    parser.add_argument("--model-params-billion", type=float, default=14.0,
                         help="Model parameter count (billions) for the Model Roofline chart")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sdk = LocalLLMBenchSDK()

    if args.mode == "hardware":
        print(sdk.probe_hardware())
    elif args.mode == "baseline":
        print(json.dumps(sdk.run_baseline(args.prompt, args.max_new_tokens).to_dict(), indent=2))
    elif args.mode == "airllm":
        print(json.dumps(sdk.run_airllm(args.prompt, args.max_new_tokens).to_dict(), indent=2))
    elif args.mode == "quantized":
        metrics = sdk.run_quantized(args.prompt, args.quant_level, args.max_new_tokens)
        print(json.dumps(metrics.to_dict(), indent=2))
    elif args.mode == "full-suite":
        out_path = sdk.run_full_benchmark_suite()
        print(f"Results saved to {out_path}")
    elif args.mode == "report":
        assets_path = sdk.generate_report(Path(args.results_path))
        print(f"Report assets saved to {assets_path}")
    elif args.mode == "economic":
        result = sdk.run_economic_analysis(args.avg_run_seconds)
        print(f"Break-even volume (requests/month): {result.breakeven_volume}")
    elif args.mode == "roofline":
        out_path = sdk.generate_model_roofline(Path(args.results_path), args.model_params_billion)
        print(f"Model Roofline chart saved to {out_path}")


if __name__ == "__main__":
    main()
