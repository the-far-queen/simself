# llama-server-tuning.md

**Source:** `Desktop/FieldCore/llama-server-tuning.md` (20 lines, 1101 bytes)
**Extracted:** 2026-09-07 (batch ingest, autonomous)

---

z49


`llama-server -m qwen3.5-35b-a3b-ud-q4_k_xl.gguf -ngl 99 -c 262144 -fa --cache-type-k q8_0 --cache-type-v q8_0 -np 1 --host 0.0.0.0 --port 8080`


THE FLAGS (what doubled everyone's speed)
most people downloaded the model, ran llama.cpp with defaults, and got 40-70 tok/s. reasonable. but not close to what this model can do.
five flags changed everything:
-ngl 99 puts all 41 layers on GPU. default offloads some to CPU. don't.
--cache-type-k q8_0 --cache-type-v q8_0 halves your KV cache VRAM. zero speed loss. this is the single most impactful flag. without it, 262K context OOMs on 24GB.
-c 262144 sets the full native context window. default is 2048. you're leaving 99% of the model's capability on the table.
-np 1 drops the recurrent state buffer from 251MB to 63MB. free VRAM. only matters if you're running single user inference, which you are on a local GPU.
-fa enables flash attention. less VRAM, faster prefill.

the result: people went from 50 tok/s to 112 overnight. same hardware. same model. different flags


some people doubled their speed just by adding --cache-type-k q8_0