#!/usr/bin/env python3
"""
ThinkingModels CLI Interface

A command-line interface for the ThinkingModels project that allows users to:
- Query problems using thinking models
- Interactive and batch processing modes
- Configure API settings
- Format and display results
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model_parser import ModelParser
from core.llm_client import get_llm_client
from core.query_processor import QueryProcessor, QueryResult

# Initialize Rich console for pretty output
console = Console()

class CLIConfig:
    """Configuration class for CLI settings"""
    
    def __init__(self):
        self.api_url = None
        self.api_key = None
        self.model_name = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 2000
        self.output_format = "rich"  # rich, json, plain
        self.interactive = True
        self.models_dir = "models"
        self.verbose = False

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        config = cls()
        config.api_url = os.getenv('LLM_API_URL')
        config.api_key = os.getenv('LLM_API_KEY')
        config.model_name = os.getenv('LLM_MODEL_NAME', config.model_name)
        config.temperature = float(os.getenv('LLM_TEMPERATURE', str(config.temperature)))
        config.max_tokens = int(os.getenv('LLM_MAX_TOKENS', str(config.max_tokens)))
        config.models_dir = os.getenv('THINKING_MODELS_DIR', config.models_dir)
        return config

def setup_processor(config: CLIConfig) -> Optional[QueryProcessor]:
    """Initialize the query processor with given configuration"""
    try:
        if config.verbose:
            console.print(f"[blue]Loading thinking models from {config.models_dir}...[/blue]")

        model_parser = ModelParser(config.models_dir)
        models = model_parser.load_all_models()

        if config.verbose:
            console.print(f"[green]✓ Loaded {len(models)} thinking models[/green]")

        # Get LLM client from factory
        llm_client = get_llm_client()

        if config.verbose:
            console.print("[blue]Testing LLM connection...[/blue]")
            if llm_client.test_connection():
                console.print("[green]✓ LLM connection successful[/green]")
            else:
                console.print("[yellow]⚠ LLM connection test failed, but continuing anyway[/yellow]")

        return QueryProcessor(model_parser, llm_client)

    except Exception as e:
        console.print(f"[red]Error initializing processor: {str(e)}[/red]")
        return None

def format_result(result: QueryResult, format_type: str = "rich") -> str:
    """Format query result based on output format"""
    
    if format_type == "json":
        return json.dumps({
            "query": result.query,
            "selected_models": result.selected_models,
            "solution": result.solution,
            "processing_time": result.processing_time,
            "error": result.error
        }, indent=2)
    
    elif format_type == "plain":
        output = f"Query: {result.query}\n"
        output += f"Selected Models: {', '.join(result.selected_models) if result.selected_models else 'None'}\n"
        if result.processing_time:
            output += f"Processing Time: {result.processing_time:.2f}s\n"
        output += f"\nSolution:\n{result.solution}\n"
        if result.error:
            output += f"\nError: {result.error}\n"
        return output
    
    else:  # rich format
        return format_rich_result(result)

def format_rich_result(result: QueryResult) -> str:
    """Format result using Rich formatting"""
    
    # Create a table for metadata
    table = Table(show_header=False, show_edge=False, pad_edge=False)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Query", result.query)
    table.add_row("Selected Models", ", ".join(result.selected_models) if result.selected_models else "None")
    
    if result.processing_time:
        table.add_row("Processing Time", f"{result.processing_time:.2f}s")
    
    if result.error:
        table.add_row("Error", f"[red]{result.error}[/red]")
    
    # Create panels for organized display
    metadata_panel = Panel(table, title="[bold blue]Query Information[/bold blue]", border_style="blue")
    solution_panel = Panel(Markdown(result.solution), title="[bold green]Solution[/bold green]", border_style="green")
    
    # Render to string (we'll print directly instead)
    return str(metadata_panel) + "\n" + str(solution_panel)

@click.group()
@click.option('--api-url', envvar='LLM_API_URL', help='LLM API URL')
@click.option('--api-key', envvar='LLM_API_KEY', help='LLM API Key')
@click.option('--model', envvar='LLM_MODEL_NAME', default='gpt-3.5-turbo', help='LLM model name')
@click.option('--temperature', envvar='LLM_TEMPERATURE', type=float, default=0.7, help='LLM temperature')
@click.option('--max-tokens', envvar='LLM_MAX_TOKENS', type=int, default=2000, help='Maximum tokens')
@click.option('--models-dir', envvar='THINKING_MODELS_DIR', default='models', help='Directory containing thinking models')
@click.option('--output-format', type=click.Choice(['rich', 'json', 'plain']), default='rich', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, api_url, api_key, model, temperature, max_tokens, models_dir, output_format, verbose):
    """ThinkingModels CLI - Solve problems using thinking models and AI"""
    
    # Ensure ctx.obj exists
    ctx.ensure_object(dict)
    
    # Store configuration in context
    config = CLIConfig()
    config.api_url = api_url
    config.api_key = api_key
    config.model_name = model
    config.temperature = temperature
    config.max_tokens = max_tokens
    config.models_dir = models_dir
    config.output_format = output_format
    config.verbose = verbose
    
    ctx.obj['config'] = config

@cli.command()
@click.argument('query', required=False)
@click.option('--batch-file', '-f', type=click.Path(exists=True), help='File containing queries to process in batch')
@click.option('--output-file', '-o', type=click.Path(), help='Output file for results')
@click.pass_context
def query(ctx, query, batch_file, output_file):
    """Process a single query or batch of queries"""
    
    config = ctx.obj['config']
    
    # Setup processor
    processor = setup_processor(config)
    if not processor:
        sys.exit(1)
    
    # Handle batch processing
    if batch_file:
        process_batch_file(processor, batch_file, config, output_file)
        return
    
    # Handle single query
    if query:
        process_single_query(processor, query, config, output_file)
    else:
        console.print("[yellow]No query provided. Use --help for usage information.[/yellow]")

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive query mode"""
    
    config = ctx.obj['config']
    
    # Setup processor
    processor = setup_processor(config)
    if not processor:
        sys.exit(1)
    
    console.print(Panel.fit(
        "[bold blue]ThinkingModels Interactive Mode[/bold blue]\n"
        "Enter your queries and get AI-powered solutions using thinking models.\n"
        "Type 'help' for commands or 'quit' to exit.",
        border_style="blue"
    ))
    
    # Show model summary
    summary = processor.get_available_models_summary()
    console.print(f"[green]✓ {summary['total_models']} thinking models loaded[/green]")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]Your query[/bold cyan]", default="").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            elif user_input.lower() == 'help':
                show_help()
                continue
            
            elif user_input.lower() == 'models':
                show_models(processor)
                continue
            
            elif user_input.lower().startswith('config'):
                show_config(config)
                continue
            
            # Process the query
            process_single_query(processor, user_input, config)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

def process_single_query(processor: QueryProcessor, query_text: str, config: CLIConfig, output_file: Optional[str] = None):
    """Process a single query"""
    
    if config.output_format == "rich":
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing query...", total=None)
            result = processor.process_query(query_text)
    else:
        result = processor.process_query(query_text)
    
    # Format output
    if config.output_format == "rich":
        # For rich format, print directly using Rich components
        display_rich_result(result)
    else:
        formatted_output = format_result(result, config.output_format)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            console.print(f"[green]Result saved to {output_file}[/green]")
        else:
            console.print(formatted_output)

def display_rich_result(result: QueryResult):
    """Display result using Rich components"""
    
    # Create metadata table
    table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
    table.add_column("Field", style="cyan bold", no_wrap=True, width=15)
    table.add_column("Value", style="white")
    
    table.add_row("Query:", result.query)
    table.add_row("Models:", ", ".join(result.selected_models) if result.selected_models else "None")
    
    if result.processing_time:
        table.add_row("Time:", f"{result.processing_time:.2f}s")
    
    if result.error:
        table.add_row("Error:", f"[red]{result.error}[/red]")
    
    # Display panels
    console.print("\n")
    console.print(Panel(table, title="[bold blue]Query Information[/bold blue]", border_style="blue"))
    console.print(Panel(Markdown(result.solution), title="[bold green]Solution[/bold green]", border_style="green"))

def process_batch_file(processor: QueryProcessor, batch_file: str, config: CLIConfig, output_file: Optional[str] = None):
    """Process queries from a batch file"""
    
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not queries:
            console.print("[yellow]No queries found in batch file[/yellow]")
            return
        
        console.print(f"[blue]Processing {len(queries)} queries from {batch_file}...[/blue]")
        
        results = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing queries...", total=len(queries))
            
            for i, query_text in enumerate(queries, 1):
                progress.update(task, description=f"Query {i}/{len(queries)}: {query_text[:50]}...")
                
                result = processor.process_query(query_text)
                results.append(result)
                
                progress.advance(task)
        
        # Output results
        if output_file:
            if config.output_format == "json":
                output_data = [json.loads(format_result(r, "json")) for r in results]
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2)
            else:
                with open(output_file, 'w', encoding='utf-8') as f:
                    for i, result in enumerate(results, 1):
                        f.write(f"=== Query {i} ===\n")
                        f.write(format_result(result, config.output_format))
                        f.write("\n" + "="*50 + "\n\n")
            
            console.print(f"[green]✓ Batch results saved to {output_file}[/green]")
        else:
            # Display results
            for i, result in enumerate(results, 1):
                console.print(f"\n[bold blue]=== Query {i} ===[/bold blue]")
                if config.output_format == "rich":
                    display_rich_result(result)
                else:
                    console.print(format_result(result, config.output_format))
        
        # Summary
        console.print(f"\n[green]✓ Processed {len(results)} queries successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Error processing batch file: {str(e)}[/red]")

def show_help():
    """Show help information in interactive mode"""
    
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

• [green]help[/green] - Show this help message
• [green]models[/green] - List available thinking models
• [green]config[/green] - Show current configuration
• [green]quit/exit/q[/green] - Exit interactive mode

[bold cyan]Query Examples:[/bold cyan]

• "How can I improve my startup's marketing strategy?"
• "What's the best approach to solve scheduling conflicts?"
• "Help me analyze risks for my investment decision"

[bold cyan]Tips:[/bold cyan]

• Be specific about your problem for better model selection
• The AI will choose the most relevant thinking models automatically
• Complex problems may take longer to process
"""
    
    console.print(Panel(help_text, title="[bold blue]Interactive Mode Help[/bold blue]", border_style="blue"))

def show_models(processor: QueryProcessor):
    """Show available thinking models"""
    
    summary = processor.get_available_models_summary()
    
    # Create summary table
    table = Table(title="[bold blue]Available Thinking Models[/bold blue]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Total Models", str(summary['total_models']))
    table.add_row("Model Types", ", ".join(summary['types']))
    table.add_row("Fields Covered", str(len(summary['fields'])))
    
    # Type distribution
    for model_type, count in summary['type_distribution'].items():
        table.add_row(f"{model_type.title()} Models", str(count))
    
    console.print(table)
    
    # Show some example models
    models = list(processor.model_parser.models.values())[:10]  # First 10 models
    
    example_table = Table(title="[bold green]Example Models[/bold green]", show_lines=True)
    example_table.add_column("Model ID", style="cyan", width=25)
    example_table.add_column("Type", style="yellow", width=10)
    example_table.add_column("Definition", style="white")
    
    for model in models:
        definition_preview = model.definition[:100] + "..." if len(model.definition) > 100 else model.definition
        example_table.add_row(model.id, model.type, definition_preview)
    
    console.print(example_table)

def show_config(config: CLIConfig):
    """Show current configuration"""
    
    table = Table(title="[bold blue]Current Configuration[/bold blue]")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("API URL", config.api_url or "[red]Not set[/red]")
    table.add_row("API Key", "[green]Set[/green]" if config.api_key else "[red]Not set[/red]")
    table.add_row("Model Name", config.model_name)
    table.add_row("Temperature", str(config.temperature))
    table.add_row("Max Tokens", str(config.max_tokens))
    table.add_row("Models Directory", config.models_dir)
    table.add_row("Output Format", config.output_format)
    table.add_row("Verbose", str(config.verbose))
    
    console.print(table)

@cli.command()
@click.pass_context
def models(ctx):
    """List available thinking models"""
    
    config = ctx.obj['config']
    
    try:
        model_parser = ModelParser(config.models_dir)
        models = model_parser.load_all_models()
        summary = model_parser.get_model_summary()
        
        show_models_info(summary, list(models.values()))
        
    except Exception as e:
        console.print(f"[red]Error loading models: {str(e)}[/red]")

def show_models_info(summary: Dict[str, Any], models: list):
    """Display detailed models information"""
    
    # Summary table
    table = Table(title="[bold blue]Thinking Models Summary[/bold blue]")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Total Models", str(summary['total_models']))
    table.add_row("Model Types", ", ".join(summary['types']))
    table.add_row("Fields Covered", str(len(summary['fields'])))
    
    for model_type, count in summary['type_distribution'].items():
        table.add_row(f"{model_type.title()} Models", str(count))
    
    console.print(table)
    
    # Detailed model list
    if Confirm.ask("\nShow detailed model list?", default=False):
        models_table = Table(title="[bold green]All Available Models[/bold green]", show_lines=True)
        models_table.add_column("ID", style="cyan", width=25)
        models_table.add_column("Type", style="yellow", width=10)
        models_table.add_column("Field", style="magenta", width=15)
        models_table.add_column("Definition", style="white")
        
        for model in sorted(models, key=lambda m: m.id):
            definition_preview = model.definition[:80] + "..." if len(model.definition) > 80 else model.definition
            models_table.add_row(model.id, model.type, model.field or "General", definition_preview)
        
        console.print(models_table)

@cli.command()
@click.pass_context 
def config(ctx):
    """Show current configuration"""
    
    config = ctx.obj['config']
    show_config(config)

@cli.command()
@click.pass_context
def test(ctx):
    """Test the ThinkingModels setup"""
    
    config = ctx.obj['config']
    
    console.print(Panel.fit(
        "[bold blue]Testing ThinkingModels Setup[/bold blue]",
        border_style="blue"
    ))
    
    # Test model loading
    console.print("\n[blue]1. Testing model loading...[/blue]")
    try:
        model_parser = ModelParser(config.models_dir)
        models = model_parser.load_all_models()
        console.print(f"   [green]✓ Successfully loaded {len(models)} models[/green]")
    except Exception as e:
        console.print(f"   [red]✗ Model loading failed: {str(e)}[/red]")
        return
    
    # Test LLM configuration
    console.print("\n[blue]2. Testing LLM configuration...[/blue]")
    if not config.api_url:
        console.print("   [red]✗ LLM_API_URL not configured[/red]")
        console.print("   [yellow]Set environment variable: LLM_API_URL[/yellow]")
        return
    else:
        console.print(f"   [green]✓ API URL configured: {config.api_url}[/green]")
    
    if not config.api_key:
        console.print("   [yellow]⚠ LLM_API_KEY not configured (may be optional)[/yellow]")
    else:
        console.print("   [green]✓ API Key configured[/green]")
    
    # Test LLM connection
    console.print("\n[blue]3. Testing LLM connection...[/blue]")
    try:
        llm_config = LLMConfig(
            api_url=config.api_url,
            api_key=config.api_key,
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        llm_client = LLMClient(llm_config)
        
        if llm_client.test_connection():
            console.print("   [green]✓ LLM connection successful[/green]")
        else:
            console.print("   [yellow]⚠ LLM connection test failed[/yellow]")
            return
    except Exception as e:
        console.print(f"   [red]✗ LLM connection error: {str(e)}[/red]")
        return
    
    # Test full pipeline
    console.print("\n[blue]4. Testing query processing...[/blue]")
    try:
        processor = QueryProcessor(model_parser, llm_client)
        test_query = "How can I prioritize my tasks better?"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing test query...", total=None)
            result = processor.process_query(test_query)
        
        console.print("   [green]✓ Query processing successful[/green]")
        console.print(f"   [cyan]Selected models: {', '.join(result.selected_models) if result.selected_models else 'None'}[/cyan]")
        console.print(f"   [cyan]Processing time: {result.processing_time:.2f}s[/cyan]")
        
    except Exception as e:
        console.print(f"   [red]✗ Query processing failed: {str(e)}[/red]")
        return
    
    console.print(f"\n[bold green]🎉 All tests passed! ThinkingModels is ready to use.[/bold green]")

if __name__ == '__main__':
    cli()
