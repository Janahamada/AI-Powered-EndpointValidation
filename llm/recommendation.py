"""
LLM call 2: turn a structured findings list + retrieved policy excerpts
into readable, policy-grounded recommendations. This call never sees the
raw controls data or the blueprint rules directly — only the findings
that the deterministic comparator already produced, so there's nothing
left for the model to get wrong about *whether* something is a gap,
only how to explain and prioritize it.
"""