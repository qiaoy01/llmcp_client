import tkinter as tk
from tkinter import messagebox
import json
import requests
import os
from datetime import datetime

class ClaudeAPI:
    def __init__(self):
        self.config_file = "llmcp_config.json"
        
        # Load AI configuration
        self.ai_config = self.load_ai_config_file()
    
    # AI Assistant functions
    def load_ai_config_file(self):
        """Load AI configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log_message(f"[AI] Failed to load config: {e}")
        return {"api_key": "", "model": "claude-3-5-sonnet-20241022"}
    
    def apply_ai_config_to_ui(self):
        """Apply loaded configuration to UI elements"""
        if hasattr(self, 'api_key_entry'):
            self.api_key_entry.insert(0, self.ai_config.get('api_key', ''))
        if hasattr(self, 'model_var'):
            self.model_var.set(self.ai_config.get('model', 'claude-3-5-sonnet-20241022'))
    
    def save_ai_config(self):
        """Save AI configuration to file"""
        try:
            config = {
                "api_key": self.api_key_entry.get().strip(),
                "model": self.model_var.get(),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            self.ai_config = config
            messagebox.showinfo("Success", f"AI configuration saved to {self.config_file}")
            self.log_message("[AI] Configuration saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save AI config: {e}")
            
    def load_ai_config(self):
        """Load AI configuration from file"""
        self.ai_config = self.load_ai_config_file()
        self.apply_ai_config_to_ui()
        messagebox.showinfo("Success", "AI configuration loaded")
        
    def test_claude_api(self):
        """Test Claude API connection"""
        api_key = self.api_key_entry.get().strip()
        model = self.model_var.get()
        
        if not api_key:
            messagebox.showwarning("Warning", "Please enter Claude API key")
            return
            
        try:
            response = self.call_claude_api(
                "Please respond with 'API connection successful' to test the connection.",
                api_key,
                model
            )
            
            if "successful" in response.lower():
                messagebox.showinfo("Success", "Claude API connection successful!")
                self.log_message("[AI] Claude API connection test passed")
            else:
                messagebox.showwarning("Warning", f"Unexpected response: {response[:100]}...")
                
        except Exception as e:
            messagebox.showerror("Error", f"Claude API test failed: {e}")
            self.log_message(f"[AI] Claude API test failed: {e}")
            
    def call_claude_api(self, prompt, api_key=None, model=None):
        """Call Claude API with given prompt"""
        try:
            
            if not api_key:
                api_key = self.api_key_entry.get().strip()
            if not model:
                model = self.model_var.get()
                
            if not api_key:
                raise Exception("No API key provided")
                
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": model,
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                raise Exception(f"API error {response.status_code}: {response.text}")
                
        except ImportError:
            raise Exception("Please install 'requests' library: pip install requests")
        except Exception as e:
            raise Exception(f"Claude API call failed: {e}")
        
    def analyze_element_with_claude(self, element_data):
        """Analyze specific element data with Claude API"""
        try:
            # Build comprehensive prompt with actual element data and strategy hints
            prompt = self.build_element_analysis_prompt(element_data)
            
            self.log_message("[AI] Sending element data to Claude for analysis...")
            
            # Call Claude API
            response = self.call_claude_api(prompt)
            
            # Display response
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, response)
            
            # Extract suggested selectors and create copy buttons
            self.extract_and_display_selectors(response)
            
            self.log_message("[AI] Element analysis completed successfully")
            
        except Exception as e:
            error_msg = f"Claude analysis failed: {e}"
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, error_msg)
            self.log_message(f"[AI] {error_msg}")
            
    def build_element_analysis_prompt(self, element_data):
        """Build comprehensive prompt with actual element data and strategy hints"""
        
        # Extract key information from element data
        tag_name = element_data.get('tagName', 'UNKNOWN')
        element_id = element_data.get('id', '')
        class_name = element_data.get('className', '')
        text_content = element_data.get('textContent', '')[:200]  # Limit text length
        attributes = element_data.get('attributes', {})
        current_selector = element_data.get('selector', '')
        
        # Get strategy hints
        strategy_hints = self.get_strategy_hints()
        
        # Build simulated HTML based on element data
        html_attributes = []
        if element_id:
            html_attributes.append(f'id="{element_id}"')
        if class_name:
            html_attributes.append(f'class="{class_name}"')
            
        # Add other important attributes
        for attr, value in attributes.items():
            if attr not in ['id', 'class'] and attr.startswith(('data-', 'aria-', 'name', 'type', 'role')):
                html_attributes.append(f'{attr}="{value}"')
                
        attr_string = ' '.join(html_attributes)
        simulated_html = f'<{tag_name.lower()}{" " + attr_string if attr_string else ""}>{text_content[:50]}{"..." if len(text_content) > 50 else ""}</{tag_name.lower()}>'
        
        # Build strategy-specific guidance
        strategy_guidance = ""
        if strategy_hints:
            strategy_guidance = "\n\nSTRATEGY HINTS (Focus on these approaches):\n"
            for hint in strategy_hints:
                strategy_guidance += f"""
{hint['type'].upper()} APPROACH:
- Context: {hint['description']}
- Recommended techniques: {', '.join(hint['techniques'])}
"""
        else:
            strategy_guidance = "\n\nNo specific strategy hints selected - provide general robust selectors."

        prompt = f"""As a web automation expert, analyze this HTML element and provide the most robust CSS selectors for automation.

ELEMENT TO ANALYZE:
```html
{simulated_html}
```

ELEMENT DETAILS:
- Tag: {tag_name}
- ID: {element_id if element_id else 'None'}
- Classes: {class_name if class_name else 'None'}
- Text Content: {text_content[:100] if text_content else 'None'}
- Current Generated Selector: {current_selector}
- Available Attributes: {', '.join(attributes.keys()) if attributes else 'None'}

{strategy_guidance}

REQUIREMENTS:
1. Provide 3-5 different CSS selector options ranked by stability and reliability
2. If strategy hints are provided above, prioritize those approaches first
3. Consider these priority factors:
   - Uniqueness and specificity
   - Resistance to page changes
   - Cross-browser compatibility
   - Performance efficiency
   - Strategy hint alignment (if applicable)

4. For each selector, explain:
   - Why it's reliable
   - Which strategy it follows (if applicable)
   - Potential failure scenarios
   - Stability score (1-10)

5. Format your response like this:
```
RECOMMENDED SELECTORS:
1. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]
2. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]
3. [SELECTOR] - Strategy: [strategy] - Score: X/10 - [Reason]

ANALYSIS:
[Detailed explanation of the element and why certain approaches work better, especially focusing on selected strategies]

BEST CHOICE: [selector] - [explanation why this is the most reliable for the given context and strategies]
```

Focus on creating selectors that work reliably for web automation while following the selected strategy hints when provided."""

        return prompt
    
    def generate_best_selector_with_data(self, element_data):
        """Generate best selector with actual element data and strategy hints"""
        try:
            # Get strategy hints
            strategy_hints = self.get_strategy_hints()
            
            # Build strategy-specific guidance for best selector generation
            strategy_guidance = ""
            if strategy_hints:
                strategy_guidance = "\n\nSTRATEGY PRIORITIES (Focus on these approaches in order of preference):\n"
                for i, hint in enumerate(strategy_hints, 1):
                    strategy_guidance += f"{i}. {hint['type'].upper()}: {hint['description']}\n   Techniques: {', '.join(hint['techniques'])}\n\n"
            else:
                strategy_guidance = "\n\nNo specific strategy hints - focus on general stability and uniqueness."
            
            # Build focused prompt for single best selector with strategy hints
            prompt = f"""Based on this HTML element, generate the single BEST CSS selector for web automation:

ELEMENT DETAILS:
- Tag: {element_data.get('tagName', 'UNKNOWN')}
- ID: {element_data.get('id', 'None')}
- Classes: {element_data.get('className', 'None')}
- Text: {element_data.get('textContent', '')[:100]}
- Attributes: {list(element_data.get('attributes', {}).keys())}
- Current selector: {element_data.get('selector', '')}

{strategy_guidance}

REQUIREMENTS:
- Maximum stability across page updates
- Uniqueness and precision
- Automation best practices
- Avoid fragile selectors (nth-child, absolute positions) UNLESS specifically requested in strategy hints
- If strategy hints are provided, prioritize those approaches first
- Consider the element's context based on the selected strategies

Respond with ONLY the CSS selector, no explanation needed."""

            response = self.call_claude_api(prompt)
            
            # Extract just the selector
            selector = response.strip().strip('`"\'')
            
            # Copy directly to debugger
            self.selector_entry.delete(0, tk.END)
            self.selector_entry.insert(0, selector)
            
            # Log which strategies were used
            strategy_info = ""
            if strategy_hints:
                strategy_names = [hint['type'] for hint in strategy_hints]
                strategy_info = f" (Using strategies: {', '.join(strategy_names)})"
                
            self.log_message(f"[AI] Generated best selector{strategy_info}: {selector}")
            
            # Show in response area with strategy information
            result_text = f"Best Selector Generated:\n{selector}\n\nCopied to debugger input field."
            
            if strategy_hints:
                result_text += f"\n\nStrategies Applied:\n"
                for hint in strategy_hints:
                    result_text += f"- {hint['type']}: {hint['description']}\n"
            
            result_text += f"\nElement analyzed:\n- Tag: {element_data.get('tagName')}\n- ID: {element_data.get('id', 'None')}\n- Classes: {element_data.get('className', 'None')}"
            
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, result_text)
            
        except Exception as e:
            self.log_message(f"[AI] Failed to generate selector: {e}")

    def validate_page_selectors(self):
        """Validate all saved selectors on current page"""
        try:
            if not self.selectors:
                messagebox.showinfo("Info", "No saved selectors to validate")
                return
                
            # Build validation prompt
            selector_list = []
            for i, sel in enumerate(self.selectors):
                selector_list.append(f"{i+1}. {sel.get('name', 'Unnamed')}: {sel.get('selector', '')}")
                
            prompt = f"""Analyze these CSS selectors for robustness and suggest improvements:

{chr(10).join(selector_list)}

For each selector, provide:
1. Stability rating (1-10)
2. Potential issues
3. Improved version if needed

Format as a numbered list matching the input."""

            response = self.call_claude_api(prompt)
            
            self.ai_response_text.delete(1.0, tk.END)
            self.ai_response_text.insert(1.0, f"SELECTOR VALIDATION RESULTS:\n{'='*40}\n\n{response}")
            
            self.log_message("[AI] Page selector validation completed")
            
        except Exception as e:
            self.log_message(f"[AI] Validation failed: {e}")