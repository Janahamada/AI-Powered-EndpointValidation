"""
LLM call 1: turn free-text into {ip, intent}. This is the only place in
the pipeline where an LLM reads the raw user prompt — everything after
this point operates on validated, structured data.
"""