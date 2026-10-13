"""Logprob parsing across both 'OpenAI-compatible' dialects.

This is the silent-corruption path: parse it wrong and every confidence is NaN
on requests that returned 200 with good answers, so the run looks fine and RQ1
quietly dies. Worth pinning both shapes with real response fragments.
"""
import math

from faultlines.generate import confidence, logprobs_of


def test_openai_dialect():
    # OpenAI / Ollama: nested objects under logprobs.content
    choice = {"logprobs": {"content": [{"logprob": -0.5}, {"logprob": -1.5}]}}
    assert logprobs_of(choice) == [-0.5, -1.5]


def test_together_dialect():
    # Together: flat float list under logprobs.token_logprobs. Real fragment
    # captured from Llama-3.3-70B-Instruct-Turbo.
    choice = {"logprobs": {
        "token_ids": [4438, 649, 358],
        "tokens": ["How", " can", " I"],
        "token_logprobs": [-0.859375, -0.07128906, 0],
    }}
    assert logprobs_of(choice) == [-0.859375, -0.07128906, 0]


def test_both_dialects_agree_on_the_same_underlying_numbers():
    openai = {"logprobs": {"content": [{"logprob": -0.5}, {"logprob": -1.5}]}}
    together = {"logprobs": {"token_logprobs": [-0.5, -1.5]}}
    assert confidence(logprobs_of(openai)) == confidence(logprobs_of(together))


def test_missing_or_empty_logprobs_is_nan_not_a_crash():
    # A provider that serves no logprobs must yield NaN so check_provider.py
    # can catch it -- never a fabricated confidence.
    for choice in ({}, {"logprobs": None}, {"logprobs": {}},
                   {"logprobs": {"content": []}},
                   {"logprobs": {"token_logprobs": []}}):
        assert logprobs_of(choice) == []
        assert math.isnan(confidence(logprobs_of(choice))), choice


def test_nulls_inside_the_list_are_dropped_not_summed():
    # A None slipping into the sum would raise TypeError mid-run, hours in.
    assert logprobs_of({"logprobs": {"token_logprobs": [-0.5, None, -1.5]}}) == [-0.5, -1.5]
    assert logprobs_of({"logprobs": {"content": [
        {"logprob": -0.5}, {"logprob": None}]}}) == [-0.5]


def test_think_block_truncated_by_max_tokens_yields_empty_not_garbage():
    # The real failure: DeepInfra's Qwen2.5-7B opened a <think> block that
    # max_tokens=64 cut off before the answer. Stripping correctly leaves "",
    # which is WHY a per-model enable_thinking=false is required -- silently
    # empty answers would have graded wrong across the whole gen-2 arm.
    from faultlines.generate import strip_reasoning
    truncated = '<think>\nOkay, the user is asking who wrote the novel "Beloved." Let me'
    assert strip_reasoning(truncated) == ""


def test_qwen25_carries_the_enable_thinking_override():
    # Pins the config wiring, not the network: the gen-2 Qwen must have the
    # override, and it must NOT leak onto any other model (Qwen3-235B returns
    # empty WITH that flag -- verified against the live API 2026-07-27).
    from faultlines.generate import model_params
    params = model_params()
    assert params.get("Qwen/Qwen2.5-7B-Instruct") == {
        "chat_template_kwargs": {"enable_thinking": False}}
    assert "Qwen/Qwen3-235B-A22B-Instruct-2507" not in params
    assert "google/gemma-3-27b-it" not in params


def test_confidence_is_the_inverse_of_perplexity():
    assert confidence([0.0, 0.0]) == 1.0                  # certain
    assert math.isclose(confidence([-1.0, -1.0]), math.exp(-1.0))
    assert confidence([-20.0]) < 0.001                    # guessing


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nall logprob-parsing checks passed")
