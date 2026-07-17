#!/usr/bin/env bash
# 功能: 训练期间周期性记录 GPU 利用率/显存到 CSV
# 输入: 输出 CSV 路径、采样间隔
# 输出: gpu 监控 CSV
set -euo pipefail

OUT="${1:-gpu_memory_log.csv}"
INTERVAL="${2:-5}"

mkdir -p "$(dirname "$OUT")"
echo "timestamp,index,memory_used_MiB,memory_total_MiB,memory_free_MiB,gpu_util_pct,temperature_c" > "$OUT"

trap 'exit 0' INT TERM

while true; do
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=index,memory.used,memory.total,memory.free,utilization.gpu,temperature.gpu \
      --format=csv,noheader,nounits 2>/dev/null | while IFS=, read -r idx used total free util temp; do
        idx="$(echo "$idx" | xargs)"
        used="$(echo "$used" | xargs)"
        total="$(echo "$total" | xargs)"
        free="$(echo "$free" | xargs)"
        util="$(echo "$util" | xargs)"
        temp="$(echo "$temp" | xargs)"
        echo "$ts,$idx,$used,$total,$free,$util,$temp"
      done >> "$OUT"
  else
    echo "$ts,NA,NA,NA,NA,NA,NA" >> "$OUT"
  fi
  sleep "$INTERVAL"
done
