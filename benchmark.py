
"""SnapDesk AI benchmark: prove the Snapdragon NPU speedup.

Runs the same Qwen generation twice - once with QNN (Hexagon NPU) enabled,
once CPU-only - and prints a comparison table. Real numbers for README/demo.

Usage:  python bench.py [--tokens 128]
Requires: ./models/qwen in ONNX Runtime GenAI format (see MODELS.md)
"""
import json, shutil, tempfile, time, os, argparse

MODEL_DIR = "models/qwen"
PROMPT = "<|im_start|>user\nExplain quantum entanglement in simple terms.<|im_end|>\n<|im_start|>assistant\n"

def load_model(force_cpu=False):
    """Load GenAI model; optionally with a CPU-only provider config."""
    import onnxruntime_genai as og
    src = MODEL_DIR
    if force_cpu:
        tmp = tempfile.mkdtemp()
        for f in os.listdir(src):
            shutil.copy(os.path.join(src, f), tmp)
        cfg = json.load(open(os.path.join(tmp, "genai_config.json")))
        cfg["session_options"]["provider_options"] = [{"CPUExecutionProvider": {}}]
        json.dump(cfg, open(os.path.join(tmp, "genai_config.json"), "w"), indent=2)
        src = tmp
    model = og.Model(src)
    return model, og.Tokenizer(model)

def run_generation(force_cpu, max_tokens):
    model, tokenizer = load_model(force_cpu)
    tokens = tokenizer.encode(PROMPT)
    params = og.GeneratorParams(model)
    params.set_search_options(max_length=len(tokens) + max_tokens, temperature=0.7)
    gen = og.Generator(model, params)
    gen.append_tokens(tokens)
    t0 = time.perf_counter(); n = 0
    while not gen.is_done() and n < max_tokens:
        gen.generate_next_token(); n += 1
    dt = time.perf_counter() - t0
    return n, dt, tokenizer.decode(gen.get_sequence(0))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", type=int, default=128)
    args = ap.parse_args()

    import onnxruntime as ort
    providers = ort.get_available_providers()
    print("Providers available:", providers)
    has_qnn = "QNNExecutionProvider" in providers

    results = {}
    plan = [("qnn", "Hexagon NPU (QNN EP)", False)] if has_qnn else []
    plan.append(("cpu", "CPU (baseline)", True))

    for key, label, force_cpu in plan:
        try:
            n, dt, _ = run_generation(force_cpu, args.tokens)
            tps = n / dt
            results[key] = {"tokens": n, "seconds": round(dt, 2), "tok_per_sec": round(tps, 1)}
            print(f"{label:<24} {n:>4} tokens in {dt:6.2f}s  =  {tps:6.1f} tok/s")
        except Exception as e:
            print(f"{label:<24} failed: {e}")

    if "qnn" in results and "cpu" in results:
        sp = results["qnn"]["tok_per_sec"] / results["cpu"]["tok_per_sec"]
        results["npu_speedup_vs_cpu"] = round(sp, 2)
        print(f"\n>>> Snapdragon NPU is {sp:.2f}x faster than CPU <<<")

    json.dump(results, open("benchmark_results.json", "w"), indent=2)
    print("Saved -> benchmark_results.json (paste into README + demo video)")

if __name__ == "__main__":
    main()
