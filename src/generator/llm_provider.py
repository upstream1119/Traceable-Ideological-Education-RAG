from dataclasses import dataclass


@dataclass
class LLMGenerationResult:
    text: str
    provider_name: str
    status: str


class StubLLMProvider:
    name = "stub"

    def generate(self, prompt: str) -> LLMGenerationResult:
        return LLMGenerationResult(
            text="",
            provider_name=self.name,
            status="stub_no_external_call",
        )


def get_llm_provider(provider_name: str):
    return StubLLMProvider()
