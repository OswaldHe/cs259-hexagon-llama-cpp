#!/usr/bin/env python3
import os
import time
import subprocess
from pathlib import Path

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def run_one(cli_path: str, prompt_device_path: str, output_path: str, extra_args=None, stderr_file=None):
    """
    Run CLI with -f prompt_device_path, capture stdout → file, but stderr → terminal.
    Returns the latency (in seconds).
    """
    if extra_args is None:
        extra_args = []
    cmd = [cli_path, "-no-cnv", "-f", prompt_device_path] + extra_args
    # If cli_path is a shell script, wrap with bash
    if cli_path.endswith(".sh"):
        cmd = ["bash"] + cmd

    start = time.time()
    with open(output_path, "w", encoding="utf-8") as fout:
        # Note: we pass stderr=subprocess.PIPE so we can separately handle it
        proc = subprocess.run(cmd, stdout=fout, stderr=stderr_file, text=True)
    end = time.time()

    latency = end - start
    if proc.returncode != 0:
        # Print stderr to console
        print(f"[ERROR] CLI failed for prompt {prompt_device_path}:")
        print(proc.stderr)
    return latency

def run_all(local_prompt_dir: str, device_prompt_prefix: str, output_dir: str,
            cli_path: str, extra_args=None):
    ensure_dir(output_dir)
    local = Path(local_prompt_dir)
    prompt_files = sorted(local.glob("*.prompt.txt"))

    latencies = []
    stderr_file = open('debug.log', 'w', encoding='utf-8')
    t0 = time.time()
    for pf in prompt_files:
        fname = pf.name  # e.g. "qmsum_test_0.prompt.txt"
        prompt_dev_path = os.path.join(device_prompt_prefix, fname)
        # derive output filename, strip ".prompt.txt"
        base = fname
        if base.endswith(".prompt.txt"):
            base = base[:-len(".prompt.txt")]
        out_fname = base + ".txt"
        out_path = os.path.join(output_dir, out_fname)

        print(f"Running prompt {fname} → output {out_fname}")
        latency = run_one(cli_path, prompt_dev_path, out_path, extra_args, stderr_file)
        print(f"  latency: {latency:.3f} s")
        latencies.append((fname, latency))

    t1 = time.time()
    total = t1 - t0
    return latencies, total

def main():
    local_prompt_dir = "./prompt_files"
    device_prompt_prefix = "/data/local/tmp/prompt_files"
    output_dir = "./qmsum_outputs"
    cli_path = "./run-cli.sh"  # or path to llama-cli or wrapper
    extra_args = []  # e.g. model settings, etc.

    latencies, total_time = run_all(
        local_prompt_dir, device_prompt_prefix, output_dir, cli_path, extra_args
    )

    print("\n=== Benchmark Summary ===")
    for fname, lat in latencies:
        print(f"{fname}: {lat:.3f} s")
    print(f"Total time for {len(latencies)} samples: {total_time:.3f} s")
    if latencies:
        avg = sum(lat for _, lat in latencies) / len(latencies)
        print(f"Average latency: {avg:.3f} s")

if __name__ == "__main__":
    main()
