import re
import glob

def extract_final_strategic_memo(analysis_text):
    """Extract the final strategic memo from CrewAI output"""
    
    # Look for the final output section specifically
    lines = analysis_text.split('\n')
    
    # Find the "Final Output:" section
    final_output_start = -1
    for i, line in enumerate(lines):
        if 'Final Output:' in line:
            final_output_start = i
            break
    
    if final_output_start == -1:
        # Look for the very end strategic memo
        for i, line in enumerate(lines):
            if 'Strategic Memo on Electric Vehicle' in line or 'Strategic Memo on' in line:
                final_output_start = i - 3  # Start a bit before
                break
    
    if final_output_start != -1:
        # Extract from final output to end
        memo_lines = lines[final_output_start:]
        
        # Clean and format the memo
        clean_memo = []
        for line in memo_lines:
            # Remove formatting characters
            clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰═]', '', line).strip()
            
            # Skip empty lines and system messages
            if (clean_line and 
                not clean_line.startswith('Tool Args:') and
                not clean_line.startswith('ID:') and
                len(clean_line) > 5):
                clean_memo.append(clean_line)
        
        # Join and format properly
        memo_text = '\n'.join(clean_memo)
        
        # Extract key sections for Slack
        sections = []
        current_section = ""
        
        for line in clean_memo:
            if line.startswith('**') and line.endswith('**'):
                if current_section:
                    sections.append(current_section.strip())
                current_section = f"{line}\n"
            elif line.startswith('- **') or line.startswith('1.') or line.startswith('2.'):
                current_section += f"• {line}\n"
            elif line.strip() and not line.startswith('---'):
                current_section += f"{line}\n"
        
        if current_section:
            sections.append(current_section.strip())
        
        # Return top 4 sections for Slack
        return '\n\n'.join(sections[:4])
    
    return "Strategic analysis completed with executive recommendations."

# Test it
if __name__ == "__main__":
    files = glob.glob('/root/ai-analysts/analysis_*EV_charging*')
    if files:
        with open(files[0], 'r') as f:
            content = f.read()
        
        summary = extract_final_strategic_memo(content)
        print("FINAL STRATEGIC MEMO:")
        print("="*50)
        print(summary)
    else:
        print("No EV charging file found")
