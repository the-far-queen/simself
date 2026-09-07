# Model roles in the dev team (2026-09-05)

Bobby's rank by capability profile:

| Role | Model | Strength |
|---|---|---|
| Critic / Rigor | Grok | extremely advanced, sharp |
| Architecture / Design | Claude | extremely advanced, careful |
| Writer / Editor | (Bobby's role, plus possibly GPT) | human-led |
| Builder / Dreamer | DeepSeek, Gemini | iterate fast, hallucinate useful variants, ship variants |
| Builder (rising) | DeepSeek (newest) | worth trying as primary dreamer |

**Insight:** Dreamers are not wrong because they hallucinate. They're useful **because** they iterate fast and produce variants the critics can score. The pipeline:
1. Builder generates variants (DeepSeek, Gemini)
2. Critic scores them (Grok, Claude)
3. Bobby decides what ships

Don't ask a builder to self-criticize. Don't ask a critic to also build. Use them in their strengths.

## Implications for Chorus

- Quick mode = all three (Grok + DeepSeek + Claude) in parallel — diversity by default
- Debate mode = critic-vs-critic (Grok vs Claude) for design rigor, builder-vs-builder (DeepSeek vs Gemini) for variant space
- Chain mode = Builder → Critic → Builder-refines → Critic-verdict

## For my own use

When delegating:
- "Generate code" → DeepSeek or Gemini
- "Review/critique code" → Grok or Claude
- "Both?" → Chorus mode

---
*Captured 2026-09-05 in conversation. Operating rule for Chorus + delegate_task choices.*