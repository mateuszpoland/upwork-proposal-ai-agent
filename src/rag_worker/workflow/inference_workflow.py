from llama_index.core.workflow import Event
from llama_index.core.schema import NodeWithScore

class RetrieverEvent(Event):
    """Result of running retrieval"""

    nodes: list[NodeWithScore]


class RerankEvent(Event):
    """Result of running reranking on retrieved nodes"""

    nodes: list[NodeWithScore]

class WorkRetrievalWorkflow(Workflow):

    def __init__(
            self,
            vector_store: SupabaseVectorStore,
            embed_model: OpenAIEmbedding,
            query_mode: str = "default",
    )
    
    @step
    async def retrieve(self, context: Context) -> 

