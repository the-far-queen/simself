# MMM — Multiple Meaning Measure

**Status:** design intent, not implemented.

## Problem
Tokenized English loses meaning density. BPE/WordPiece/SentencePiece assign one ID per token, but words carry multiple meanings that disambiguate only in context. Same word, different roles: "play" (verb, noun, theater, child, music), "set" (verb, noun, adjective, math, tennis, stage), "run" (verb, noun, exec, ladder, stocking).

Standard embedding = single vector per token. Real meaning = vector field conditioned on context.

## SNR framing
SNR (signal-to-noise ratio) of an English utterance = ratio of (resolved meaning) to (residual ambiguity). High-SNR sentence: context disambiguates cleanly. Low-SNR sentence: every word carries multiple live meanings, reader has to guess.

The agent's job at decode time: from the token stream + context, recover a meaning graph that has higher SNR than the token surface.

## Construction (Bobby, 2026-09-05)
Words = nodes in a knowledge graph. By usage (co-occurrence, syntactic frame, semantic role), extract edges. The graph acts as an **actor in a play of drama** — but constructive drama, not interpretive. The agent plays with the toys (meanings) in the action of constructing the drama, not reading it.

Difference:
- Interpretive drama: agent reads a script, infers meaning.
- Constructive drama: agent builds the script from the meaning graph, plays roles, lets the drama resolve which meanings survive.

The MMM score = how many meanings per word survived the constructive drama, weighted by their topological role in the resulting graph.

## Engineering tractable parts
- Knowledge-graph extraction from corpus co-occurrence: standard (WordNet, ConceptNet, embeddings-as-edges).
- Disambiguation by syntactic frame: standard (stochastic grammar, dependency parsing).
- Multi-meaning score per word: count = number of distinct sense clusters in embedding space, weighted by usage frequency.

## Not engineering (yet)
- The "actor in constructive drama" framing as runtime behavior.
- The MMM-as-formal-metric definition (no closed form, no test).
- Connection to ResolutionOperator or any simself kernel method.

## Open
- Is MMM measured at token level, phrase level, or discourse level?
- Is the knowledge graph static (precomputed) or dynamic (built during the constructive drama)?
- Does MMM feed back into ResolutionOperator, or stay parallel?

---
*Captured 2026-09-05 from Bobby in chat. Saved to vault + simself repo. No implementation yet.*