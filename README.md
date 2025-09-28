# LLMCP UI Debugger

A comprehensive browser automation debugging tool with Model Context Protocol (MCP) server integration for AI-driven web interactions. This tool works in conjunction with the **LLMCP Chrome Extension** to provide complete browser automation capabilities.

## Overview

The LLMCP UI Debugger is a Python-based debugging and automation tool that provides both a graphical interface and MCP server capabilities for controlling web browsers through the LLMCP Chrome Extension. It enables AI agents, automation scripts, and manual testing to interact with web pages programmatically.

## Key Features

### Dual Operation Modes
- **Full UI Mode**: Complete debugging interface with visual controls and real-time monitoring
- **MCP Server Mode**: Headless server exposing browser automation as MCP tools for AI integration

### Core Browser Automation
- **Element Interaction**: Click, input text, and send keys to web elements
- **Content Extraction**: Retrieve text content and element properties
- **Page Navigation**: Get page information and track user interactions
- **Click Tracking**: Monitor and analyze user click behavior
- **CSS Selector Management**: Save, organize, and execute automation sequences

### AI Integration
- **Claude API Integration**: Analyze web elements and generate optimal selectors
- **MCP Server**: Expose browser automation tools to AI clients like Claude Desktop
- **Ollama Support**: Local AI model integration for offline automation
- **Intelligent Selector Generation**: AI-powered CSS selector optimization

### Advanced Features
- **WebSocket Communication**: Real-time bidirectional communication with Chrome extension
- **Request Tracking**: Proper routing of responses between UI and MCP clients
- **Selector Library**: Persistent storage and management of CSS selectors
- **Multi-tab Interface**: Organized workspace for different automation tasks
- **Comprehensive Logging**: Detailed operation logs and debugging information

## Installation

### Prerequisites
- Python 3.13.6 or higher
- Chrome browser with developer mode enabled
- LLMCP Chrome Extension (see companion project)

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Required Companion Project
**You must also install the LLMCP Chrome Extension** to use this tool effectively. The Chrome extension acts as the client that executes browser operations, while this Python tool acts as the server/controller.

**Get the LLMCP Chrome Extension here**: [LLMCP Chrome Extension Repository]

## Quick Start

### 1. Install the Chrome Extension
First, install and enable the LLMCP Chrome Extension in your Chrome browser.

### 2. Run the UI Debugger
```bash
# Full UI mode (default)
python llmcp_ui.py

# MCP server only (for AI integration)
python llmcp_ui.py --mcp-server

# Show help
python llmcp_ui.py --help
```

### 3. Basic Usage
1. Start the debugger - it automatically launches a WebSocket server on `localhost:11808`
2. Open Chrome with the LLMCP extension installed
3. Navigate to any webpage
4. Use the debugger interface to interact with page elements

## Usage Modes

### UI Mode (Interactive Debugging)

The full UI provides five main tabs:

#### 1. Chrome Extension Debugger
- Test DOM operations directly
- Real-time element interaction
- Manual selector testing
- Connection status monitoring

#### 2. CSS Selector Manager
- Save and organize CSS selectors
- Batch operations on multiple selectors
- Import/export selector libraries
- Selector validation and testing

#### 3. AI Assistant (Claude Integration)
- Analyze clicked elements with AI
- Generate optimal CSS selectors
- Natural language automation queries
- Element property analysis

#### 4. MCP Server
- Monitor MCP client connections
- View available automation tools
- Track AI agent interactions
- Server configuration management

#### 5. Server Logs
- WebSocket communication logs
- Error tracking and debugging
- Performance monitoring
- Request/response analysis

### MCP Server Mode (AI Integration)

When run with `--mcp-server`, the tool exposes these MCP tools:

- **find_element**: Locate elements using CSS selectors
- **click_element**: Click elements on web pages
- **input_text**: Input text into form fields
- **get_element_text**: Extract text from elements
- **send_key**: Send keyboard input to elements
- **get_page_info**: Get current page information
- **get_last_clicked_element**: Analyze user interactions
- **list_saved_selectors**: Access saved automation sequences

## Integration with LLMCP Chrome Extension

This tool requires the LLMCP Chrome Extension to function. Here's how they work together:

### Architecture
```
AI Client/User → LLMCP UI Debugger → WebSocket → Chrome Extension → Web Page
                      ↑                                    ↓
                  MCP Server                        DOM Operations
```

### Communication Flow
1. **Commands**: Python tool sends JSON commands via WebSocket
2. **Execution**: Chrome extension receives commands and performs DOM operations
3. **Responses**: Extension sends results back to Python tool
4. **Routing**: Python tool routes responses to appropriate handlers (UI/MCP/AI)

### WebSocket Protocol
The tools communicate using structured JSON messages:

```json
{
  "type": "dom_operation",
  "action": "click_element",
  "selector": "#submit-button",
  "request_id": "unique-id",
  "source": "debugger"
}
```

## Configuration

### WebSocket Server
- **Default Port**: 11808
- **Protocol**: WebSocket (ws://)
- **Host**: localhost
- **Auto-reconnection**: Supported with exponential backoff

### MCP Server
- **Default Port**: 11809
- **Protocol**: HTTP
- **Transport**: Streamable HTTP connections
- **Server Name**: llmcp-browser-automation

### AI Configuration
Configure Claude API key and Ollama settings in the AI tab for enhanced automation capabilities.

## Use Cases

### Manual Testing
- Debug CSS selectors interactively
- Test automation sequences step-by-step
- Analyze element properties and click behavior
- Validate automation scripts before deployment

### AI-Driven Automation
- Connect Claude Desktop or other MCP clients
- Enable AI agents to interact with web pages
- Automated form filling and data extraction
- Intelligent web scraping and testing

### Development and QA
- Browser automation testing
- Element locator optimization
- Performance monitoring of web interactions
- Cross-browser compatibility testing

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure Chrome extension is installed and enabled
   - Check that no other service is using port 11808
   - Verify Chrome developer mode is enabled

2. **MCP Server Not Starting**
   - Check port 11809 availability
   - Verify Python dependencies are installed
   - Ensure proper permissions for network binding

3. **Element Not Found Errors**
   - Validate CSS selectors in the debugger tab
   - Use the AI assistant to generate better selectors
   - Check if elements are loaded dynamically

4. **AI Features Not Working**
   - Configure Claude API key in settings
   - Check internet connection for API calls
   - Verify Ollama installation for local AI features

### Debug Mode

Enable detailed logging by checking the Server Logs tab. All WebSocket communications, MCP interactions, and DOM operations are logged for troubleshooting.

## Security Considerations

- WebSocket server binds to localhost only by default
- No external network access without explicit configuration
- All browser operations require user-installed Chrome extension
- MCP server exposes controlled automation interface only
- Request tracking prevents unauthorized command injection

## Development and Extension

### Adding New Automation Commands
1. Add command handler in the Chrome extension
2. Update WebSocket message protocol
3. Add UI controls in appropriate tab
4. Update MCP server tool definitions
5. Add response handling logic

### Custom AI Integrations
The tool supports custom AI integrations through:
- MCP server protocol compliance
- WebSocket API for direct integration
- RESTful interface for HTTP-based clients
- Plugin architecture for custom automation tools

## Compatibility

### MCP Integration
This tool is fully compatible with the Model Context Protocol and can integrate with:
- Claude Desktop
- Other MCP-compatible AI clients
- Custom MCP client implementations
- MCP debugging and development tools

### Browser Support
- Primary: Chrome/Chromium with LLMCP extension
- Architecture allows extension to other browsers
- WebSocket protocol is browser-agnostic

## Contributing

Contributions are welcome! Key areas for enhancement:
- Additional browser automation capabilities
- Enhanced AI integration features
- Performance optimizations
- Extended MCP tool definitions
- Cross-browser extension support

## License

This project is open source. Please check the license file for specific terms and conditions.

---

**Important**: This tool requires the companion **LLMCP Chrome Extension** to function. Make sure to install and configure the Chrome extension before using this debugger tool.