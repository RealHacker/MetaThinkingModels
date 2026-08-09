# MetaThinkingModels: AI-Powered Problem Solving

**A Python project that empowers LLMs with different meta-thinking models for solving real-life problems through a two-phase query handling system.**

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [MetaThinking Models](#metathinking-models)
- [Future Work](#future-work)
- [License](#license)

---

## Overview

MetaThinkingModels is a framework that enhances the problem-solving capabilities of Large Language Models (LLMs) by integrating them with a curated collection of **140 thinking models**. The system uses a two-phase query handling process to provide structured, insightful solutions to complex problems.

### Key Components

- **Core Engine**: A backend that parses thinking models, integrates with LLM APIs, and processes queries in two phases.
- **CLI Interface**: A feature-rich command-line tool for interactive and batch query processing.
- **Web Application**: A modern web interface with real-time updates for exploring models and solving problems.

### How It Works

1. **Model Selection (Phase 1)**: When a user submits a query, the system first selects the most relevant thinking models from its library. This is done by sending a specially crafted prompt to the LLM with the user query and a summary of available models.

2. **Solution Generation (Phase 2)**: The selected models are then used to formulate a second prompt that guides the LLM to generate a comprehensive, structured solution. The LLM is instructed to use the thinking models as a framework for its response.

This two-phase approach ensures that the solutions are not just generic LLM responses, but are grounded in proven problem-solving methodologies, leading to more insightful and actionable answers.

---

## Features

- **140 Thinking Models**: A comprehensive library of thinking models, from SWOT analysis to second-order thinking.
- **Two-Phase Query Processing**: Enhances LLM responses with structured problem-solving methodologies.
- **Multi-LLM-Backend Support**: Integrates with multiple LLM providers, including OpenAI and Google Gemini.
- **CLI & Web Interfaces**: Access the system through a command-line interface or a modern web application.
- **Real-time Updates**: Get live feedback during query processing via WebSockets.
- **Model Browser**: Explore, search, and filter thinking models through the web UI.
- **Result Export**: Save results to JSON for further analysis.
- **Easy Deployment**: Deploy the application with Docker and a simple launcher script.

---

## Getting Started

### Prerequisites

- Python 3.8+
- `pip` for package management
- An API endpoint and key for an OpenAI-compatible service or Google Gemini.

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/ThinkingModels.git
   cd ThinkingModels
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your LLM API:**

   Create a `.env` file in the project root. Below are examples for configuring OpenAI and Gemini providers.

   **For OpenAI-Compatible APIs:**
   ```env
   # Set the provider to openai (this is the default)
   LLM_PROVIDER=openai

   # Required
   LLM_API_URL=https://your-llm-api-endpoint.com

   # Optional
   LLM_API_KEY=your-api-key
   LLM_MODEL_NAME=gpt-3.5-turbo
   ```

   **For Google Gemini:**
   ```env
   # Set the provider to gemini
   LLM_PROVIDER=gemini

   # Required - your Gemini API key
   GEMINI_API_KEY=your-gemini-api-key

   # Optional - specify a Gemini model
   LLM_MODEL_NAME=gemini-1.5-flash
   ```

---

## Usage

You can use ThinkingModels through either the command-line interface or the web application.

### CLI Interface

The CLI provides a powerful way to interact with the system, with support for single queries, batch processing, and various output formats.

**Start interactive mode:**

```bash
python thinking_models.py interactive
```

**Process a single query:**

```bash
python thinking_models.py query "How can I improve my startup's marketing strategy?"
```

**For more details, see the [CLI Documentation](CLI_README.md).**

### Web Application

The web application provides a user-friendly interface for exploring thinking models and processing queries in real-time.

**Start the web server:**

```bash
python web_server.py
```

Then open your browser to **http://127.0.0.1:8000**.

---

## Deployment

The easiest way to deploy the ThinkingModels application is with Docker.

### Using Docker

1. **Build the Docker image:**

   ```bash
   docker build -t thinking-models .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -d -p 8000:8000 \
     -e LLM_API_URL="https://your-llm-api-endpoint.com" \
     -e LLM_API_KEY="your-api-key" \
     --name thinking-models-app \
     thinking-models
   ```

   This will start the web application on port 8000.

### Manual Deployment

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**

   ```bash
   export LLM_API_URL="https://your-llm-api-endpoint.com"
   export LLM_API_KEY="your-api-key"
   ```

3. **Run the web server:**

   ```bash
   python web_server.py
   ```

---

## Project Structure

```
ThinkingModels/
├── models/                 # Thinking model definitions
├── src/
│   ├── core/             # Core application logic
│   ├── cli/              # Command-line interface
│   └── web/              # Web application
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── config.py               # Configuration management
└── README.md               # Project documentation
```

---

## MetaThinking Models

The project includes a library of **140 thinking models**, 

The thinking models are current broadly divided into 2 types: **explain** and **solve**. 
The former is to help LLMs to explain a phenomenon, while the latter is to guide LLMs to solve a problem.

The meta-thinking models include:
- **Problem Solving**: SWOT Analysis, First Principles Thinking, 5 Whys
- **Decision Making**: Pareto Principle, Eisenhower Matrix, Cost-Benefit Analysis
- **Creativity**: Lateral Thinking, Brainstorming, SCAMPER
- **Systems Thinking**: Feedback Loops, Emergence, Systems Mapping
- **And many more...**

---

## Future Work

- **More models**: The 140 thinking models represent only a small portion of humanity's "metacognitive" system. Many similar core concepts, frameworks, and cognitive models exist across various industries and fields and should be incorporated into this database. We hope open-sourcing will enable the community to contribute and continuously enrich this database. For example, in software development, each programming language has many accumulated gems (best practices). When a Coding Agent is generating code, it can leverage gems from this database based on the chosen language to inform the Agent and guide it in writing high-quality code.

- **More Metadata for models**: The model selection process is currently quite crude, allowing the LLM to directly choose from the models. We can add more metadata to the models, such as domain, problem type, keywords, etc., allowing the LLM to first categorize and narrow down the search scope before selecting a suitable model.

- **A new paradigm, maybe**: This database can become a component for various Agents, and even be packaged as a cloud service API to support Agents in different fields. If thinking traces of this type reach a certain scale, we can consider using post-training to "internalize" these thinking models into the LLM.

Eventually, the output of the reasoning model will change from the current:
```
<think>Thinking Trace ...</think>
Final result is here
```
to:
```
<meta>Meta-thinking models to use ...</meta>
<think>Thinking Trace ...</think>
Final result is here
```
This way, the LLM will first determine the direction of thought (meta-model), then think according to that direction, and finally output the result to the user.


---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

