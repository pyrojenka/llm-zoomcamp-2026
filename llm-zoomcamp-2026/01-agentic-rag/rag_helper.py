INSTRUCTIONS = """
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
"""

PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()

class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        course="llm-zoomcamp",
        model="gemini-flash-lite-latest"
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.course = course
        self.prompt_template = prompt_template
        self.model = model

    def search(self, query, num_results=5):
        # Our documents use `filename` and `content` fields rather than
        # the FAQ schema's `section`/`question`/`answer`. Prefer filename
        # matches slightly higher so queries can target specific files.
        boost_dict = {"filename": 2.0, "content": 1.0}

        # Call the underlying index search with the adjusted boost map.
        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict
        )
            
    def build_context(self, search_results):
        # Build a plain text context from search results using the
        # `filename` and `content` fields present in our documents.
        lines = []

        for doc in search_results:
            filename = doc.get("filename") or doc.get("id") or "<unknown>"
            content = doc.get("content") or doc.get("text") or ""

            lines.append(f"File: {filename}")
            lines.append(content)
            lines.append("")

        return "\n".join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )

    def llm(self, prompt):
        response = self.llm_client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"system_instruction": self.instructions}
        )
        
        self.last_response = response

        return response.text

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer