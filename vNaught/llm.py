#!/usr/bin/env python3
"""
llm.py

Small wrapper for local, free LLM usage. Tries to import HuggingFace's
transformers and use a small CPU-friendly model if available. If not,
falls back to a deterministic template-based responder for offline use.

Functions:
 - generate(prompt, max_tokens=256): returns generated string
"""
from typing import Optional
import os

# Force CPU-only to avoid CUDA initialization warnings in environments
# where CUDA isn't set up correctly. Set this before importing transformers/torch.
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('TORCH_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

try:
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
except Exception:
    pipeline = None


class LLM:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.environ.get('RALSEI_LLM_MODEL')
        self.generator = None
        if pipeline is not None:
            try:
                # use a small model by default if nothing specified
                model = self.model_name or 'gpt2'
                # instantiate a text-generation pipeline
                # ensure CPU usage
                # newer transformers support device_map and device, but device=-1
                # is the most compatible CPU setting for pipeline
                self.generator = pipeline('text-generation', model=model, device=-1)
            except Exception:
                self.generator = None

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        # Accept generation options via kwargs
        def _fallback():
            head = prompt.strip()[:100].replace('\n', ' ')
            return f"[Fallback LLM] I read: '{head}...'\nHere's a short answer based on the retrieved context."

        if self.generator is None:
            return _fallback()

        # parse generation kwargs from environment defaults or call-time kwargs
        # typical kwargs: temperature, top_p, repetition_penalty, do_sample
        # caller may pass these via keyword arguments stored on the instance (we accept **gen_kwargs below)
        # For simplicity, read env defaults here
        gen_temp = float(os.environ.get('RALSEI_GEN_TEMPERATURE', '0.0'))
        gen_top_p = float(os.environ.get('RALSEI_GEN_TOP_P', '0.95'))
        gen_rep_pen = float(os.environ.get('RALSEI_GEN_REP_PENALTY', '1.0'))

        do_sample = gen_temp > 0.0

        try:
            out = self.generator(
                prompt,
                max_new_tokens=max_tokens,
                do_sample=do_sample,
                temperature=gen_temp if do_sample else 0.0,
                top_p=gen_top_p,
                repetition_penalty=gen_rep_pen,
                truncation=True,
                return_full_text=False,
            )
        except TypeError:
            # older pipelines might ignore some kwargs
            out = self.generator(prompt, max_new_tokens=max_tokens, do_sample=do_sample)
        if isinstance(out, list) and out:
            # pipeline may return either 'generated_text' or first element string
            first = out[0]
            if isinstance(first, dict):
                return first.get('generated_text', '')
            if isinstance(first, str):
                return first
        return ''


_default = None

def get_default_llm() -> LLM:
    global _default
    if _default is None:
        _default = LLM()
    return _default


if __name__ == '__main__':
    llm = get_default_llm()
    p = input('prompt> ')
    # allow quick manual sampling control via env vars
    import os
    temp = float(os.environ.get('RALSEI_GEN_TEMPERATURE', '0.0'))
    top_p = float(os.environ.get('RALSEI_GEN_TOP_P', '0.95'))
    rep_pen = float(os.environ.get('RALSEI_GEN_REP_PENALTY', '1.0'))
    print(llm.generate(p, max_tokens=200, temperature=temp, top_p=top_p, repetition_penalty=rep_pen))
