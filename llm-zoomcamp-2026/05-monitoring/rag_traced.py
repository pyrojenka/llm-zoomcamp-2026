from opentelemetry import trace
from rag_helper import RAGBase

tracer = trace.get_tracer(__name__)


class RAGTraced(RAGBase):

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            span.set_attribute("query", query)
            span.set_attribute("num_results", num_results)

            results = super().search(query, num_results=num_results)

            span.set_attribute("num_results_returned", len(results))
            return results

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            span.set_attribute("model", self.model)
            span.set_attribute("prompt", prompt)

            response = super().llm(prompt)
            
            usage = response.usage_metadata
            span.set_attribute("input_tokens", usage.prompt_token_count)
            span.set_attribute("output_tokens", usage.candidates_token_count)

            span.set_attribute("response", response.text)
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            span.set_attribute("query", query)

            result = super().rag(query)

            span.set_attribute("answer", result)
            return result