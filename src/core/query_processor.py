"""
Query Processor for ThinkingModels

This module handles the orchestration of query processing using different
thinking models and the LLM API.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.core.model_parser import ModelParser, ThinkingModel
from src.core.llm_client import get_llm_client, BaseLLMClient
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """
    Result of query processing
    """
    query: str
    selected_models: List[str]
    solution: str
    processing_time: Optional[float] = None
    error: Optional[str] = None

class QueryProcessor:
    """
    Handles the entire query processing workflow, including:
    - Selecting relevant thinking models
    - Formulating LLM requests
    - Parsing and validating LLM responses
    """
    
    def __init__(self, model_parser: ModelParser, llm_client: BaseLLMClient):
        self.model_parser = model_parser
        self.llm_client = llm_client
        
    def process_query(self, query: str) -> QueryResult:
        """
        Process a user query through the two-phase LLM approach.
        
        Args:
            query: The user's problem query
            
        Returns:
            QueryResult containing solution and processing details
        """
        start_time = time.time()
        logger.info(f"Processing query: {query}")
        
        try:
            # Phase 1: Select relevant models
            selected_models = self.phase_1_model_selection(query)
            if not selected_models:
                logger.warning("No relevant thinking models selected.")
                return QueryResult(
                    query=query,
                    selected_models=[],
                    solution="I'll address your query directly without using specific thinking models:\n\n" + 
                            self._generate_direct_solution(query),
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"Selected {len(selected_models)} thinking models: {selected_models}")
            
            # Fetch full model data
            selected_model_data = self.fetch_model_data(selected_models)
            
            if not selected_model_data:
                logger.warning("No model data found for selected models")
                return QueryResult(
                    query=query,
                    selected_models=selected_models,
                    solution="Selected models were not found in the database.",
                    processing_time=time.time() - start_time,
                    error="Model data not found"
                )
    
            # Phase 2: Generate solution using selected models
            solution = self.phase_2_solution_generation(query, selected_model_data)
            
            return QueryResult(
                query=query,
                selected_models=selected_models,
                solution=solution,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return QueryResult(
                query=query,
                selected_models=[],
                solution=f"An error occurred while processing your query: {str(e)}",
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def phase_1_model_selection(self, query: str) -> List[str]:
        """
        Execute the model selection phase
        
        Args:
            query: The user's problem query
            
        Returns:
            List of selected thinking model IDs
        """
        logger.info("Phase 1: Model selection")
        
        models = self.model_parser.models.values()
        available_models = [{
            'id': model.id,
            'definition': model.definition
        } for model in models]
        
        logger.info(f"Available models for selection: {len(available_models)}")
        return self.llm_client.request_model_selection(query, available_models)
    
    def fetch_model_data(self, model_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch full data for selected model IDs
        
        Args:
            model_ids: List of selected model IDs
            
        Returns:
            List of ThinkingModel data dictionaries
        """
        logger.info(f"Fetching data for {len(model_ids)} models")
        
        models = [model for model in self.model_parser.models.values() if model.id in model_ids]
        model_data = [{
            'id': model.id,
            'type': model.type,
            'definition': model.definition,
            'examples': model.examples
        } for model in models]
        
        logger.info(f"Found data for {len(model_data)} models")
        return model_data

    def phase_2_solution_generation(self, query: str, selected_models: List[Dict[str, Any]]) -> str:
        """
        Execute the solution generation phase
        
        Args:
            query: The user's problem query
            selected_models: List of data for thinking models to use in the solution
            
        Returns:
            Generated solution as a string
        """
        logger.info(f"Phase 2: Solution generation with {len(selected_models)} models")
        return self.llm_client.request_solution(query, selected_models)
    
    def _generate_direct_solution(self, query: str) -> str:
        """
        Generate a direct solution without thinking models as fallback
        
        Args:
            query: The user's problem query
            
        Returns:
            Generated solution as a string
        """
        logger.info("Generating direct solution without thinking models")
        return self.llm_client.generate_response(query)
    
    def get_available_models_summary(self) -> Dict[str, Any]:
        """
        Get summary of available thinking models
        
        Returns:
            Dictionary with model statistics
        """
        return self.model_parser.get_model_summary()

