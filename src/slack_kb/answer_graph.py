from __future__ import annotations

import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from slack_kb.config import Settings
from slack_kb.database import Database
from slack_kb.models import AnswerResult, RequestContext, RetrievalHit
from slack_kb.openai_service import OpenAIService

REFUSAL = "I couldn't find enough evidence in the knowledge base to answer that."


class AnswerState(TypedDict):
    context: RequestContext
    question: str
    history: list[tuple[str, str]]
    hits: list[RetrievalHit]
    answer: str
    refused: bool


class AnswerGraph:
    def __init__(self, database: Database, openai: OpenAIService, settings: Settings):
        self.database = database
        self.openai = openai
        self.settings = settings
        workflow = StateGraph(AnswerState)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("refuse", self._refuse)
        workflow.add_node("generate", self._generate)
        workflow.add_node("validate", self._validate)
        workflow.add_edge(START, "retrieve")
        workflow.add_conditional_edges(
            "retrieve",
            lambda state: "generate" if state["hits"] else "refuse",
            {"generate": "generate", "refuse": "refuse"},
        )
        workflow.add_edge("generate", "validate")
        workflow.add_edge("validate", END)
        workflow.add_edge("refuse", END)
        self.graph = workflow.compile()

    def ask(self, context: RequestContext, question: str) -> AnswerResult:
        history = self.database.history(context)
        self.database.add_message(context, "user", question)
        final = self.graph.invoke(
            {
                "context": context,
                "question": question,
                "history": history,
                "hits": [],
                "answer": "",
                "refused": False,
            }
        )
        self.database.add_message(context, "assistant", final["answer"])
        return AnswerResult(
            answer=final["answer"],
            hits=final["hits"],
            refused=final["refused"],
        )

    def _retrieve(self, state: AnswerState) -> dict:
        history_questions = " ".join(
            content for role, content in state["history"][-3:] if role == "user"
        )
        retrieval_query = f"{history_questions}\n{state['question']}".strip()
        embedding = self.openai.embed([retrieval_query])[0]
        hits = self.database.search(
            context=state["context"],
            question=state["question"],
            embedding=embedding,
            min_similarity=self.settings.min_similarity,
            limit=self.settings.retrieval_limit,
        )
        return {"hits": hits}

    @staticmethod
    def _refuse(state: AnswerState) -> dict:
        return {"answer": REFUSAL, "refused": True}

    def _generate(self, state: AnswerState) -> dict:
        answer = self.openai.answer(
            question=state["question"],
            history=state["history"],
            hits=state["hits"],
        )
        return {"answer": answer}

    @staticmethod
    def _validate(state: AnswerState) -> dict:
        answer = state["answer"]
        if answer == REFUSAL:
            return {"refused": True}
        citations = {int(value) for value in re.findall(r"\[(\d+)\]", answer)}
        valid = set(range(1, len(state["hits"]) + 1))
        if not citations or not citations.issubset(valid):
            return {"answer": REFUSAL, "refused": True}
        return {"refused": False}
