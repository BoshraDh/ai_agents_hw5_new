"""Project-wide immutable constants (guidelines section 7.3 — no magic numbers in logic)."""

BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024

DEFAULT_CONFIG_PATH = "config/setup.json"
DEFAULT_RATE_LIMIT_PATH = "config/rate_limits.json"

SUPPORTED_METHODS = ("baseline", "airllm", "quantized")
SUPPORTED_PRECISIONS = ("fp32", "fp16", "bf16")
SUPPORTED_QUANT_LEVELS = ("Q4_K_M", "Q2_K")

OLLAMA_DEFAULT_HOST = "http://localhost:11434"

# Fallback only — the real value should come from config/setup.json (rated TDP of
# the CPU being benchmarked). i7-1165G7 base TDP used as the built-in default.
DEFAULT_ASSUMED_TDP_WATTS = 28.0
SECONDS_PER_HOUR = 3600.0
