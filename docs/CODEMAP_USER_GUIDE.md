# Codemap User Guide

## What is Codemap?

Codemap is an AI-powered feature that generates interactive, visual maps of your codebase. It helps you understand:

- How code components relate to each other
- Data and control flow through the system
- Execution order for specific features
- Direct links to source code locations

## Getting Started

### 1. Access Codemap

From any repository wiki page, click the **Codemap** link in the header navigation or the **Explore Codemap** button in the sidebar.

Alternatively, navigate directly to:
```
/{owner}/{repo}/codemap
```

### 2. Ask a Question

Enter a natural language question about the codebase:

- "How does authentication work?"
- "Show me the overall architecture"
- "What happens when a user submits an order?"
- "How does data flow from the API to the database?"

### 3. View Results

After generation, you'll see:

- **Graph View**: Interactive diagram showing code relationships
- **Trace Guide**: Narrative explanation of the flow
- **Node Inspector**: Detailed information about selected nodes

## Features

### Graph Interaction

- **Click** on nodes to see details
- **Drag** to pan the view
- **Scroll** or use buttons to zoom
- **Hover** to highlight connections

### View Modes

- **Graph**: Full-screen diagram view
- **Trace**: Full-screen narrative view
- **Split**: Side-by-side graph and trace

### Export Options

- **HTML**: Standalone interactive diagram
- **Mermaid**: Diagram code for documentation
- **JSON**: Raw graph data for integration

### Sharing

Click **Share** to generate a public link that anyone can view. Share links expire after 30 days by default.

## Tips

1. **Be specific**: "How does JWT authentication work?" is better than "How does auth work?"
2. **Use filters**: Exclude test files or node_modules for cleaner results
3. **Iterate**: Generate multiple codemaps for different aspects of the code
4. **Navigate**: Click code locations to jump directly to source files

## Query Examples

### Architecture Queries
- "Show me the overall system architecture"
- "What are the main components and how do they interact?"
- "How is the application structured?"

### Data Flow Queries
- "How does data flow from the frontend to the database?"
- "What happens to user input when a form is submitted?"
- "How is state managed across components?"

### Feature Queries
- "How does the login process work?"
- "What code handles file uploads?"
- "How are notifications sent to users?"

### Dependency Queries
- "What external services does this code depend on?"
- "Which modules are most connected?"
- "What would be affected if I change this class?"

## Advanced Options

When generating a codemap, you can configure:

- **Analysis Type**: Auto, Data Flow, Control Flow, Dependencies, Call Graph, Architecture
- **Depth**: How deep to analyze (1-10)
- **Max Nodes**: Maximum nodes in the graph (10-200)
- **Excluded Directories**: Directories to skip (e.g., node_modules, .git)
- **Excluded Files**: File patterns to skip (e.g., *.test.js)

## Troubleshooting

### Generation takes too long

- Try reducing `max_nodes` in advanced settings
- Exclude large directories like `node_modules`
- Use a more specific query

### Graph is too cluttered

- Use a more specific query
- Reduce analysis depth
- Exclude non-essential directories

### Missing code files

- Check that the repository is public or you've provided a valid token
- Verify the files aren't in excluded directories

### Error during generation

- Ensure API keys are properly configured
- Check network connectivity
- Try with a simpler query first

## API Reference

For programmatic access to Codemap functionality, see the [API Documentation](CODEMAP_API.md).
