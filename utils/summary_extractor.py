import re

def extract_strategic_summary(analysis_text):
    """Extract the final strategic memo from CrewAI output"""
    lines = analysis_text.split('\n')
    
    # Find the "Final Output:" section
    final_output_start = -1
    for i, line in enumerate(lines):
        if 'Final Output:' in line:
            final_output_start = i
            break
    
    if final_output_start == -1:
        # Look for strategic memo
        for i, line in enumerate(lines):
            if 'Strategic Memo on' in line or 'Executive Summary' in line:
                final_output_start = i - 2
                break
    
    if final_output_start != -1:
        # Extract from final output to end
        memo_lines = lines[final_output_start:]
        
        # Clean and format the memo
        clean_memo = []
        for line in memo_lines:
            clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰═]', '', line).strip()
            
            if (clean_line and 
                not clean_line.startswith('Tool Args:') and
                not clean_line.startswith('ID:') and
                not clean_line.startswith('╰') and
                len(clean_line) > 5):
                clean_memo.append(clean_line)
        
        # Extract key sections for Slack
        sections = []
        current_section = ""
        
        for line in clean_memo:
            if line.startswith('**') and (line.endswith('**') or 'Summary' in line or 'Assessment' in line or 'Recommendations' in line):
                if current_section:
                    sections.append(current_section.strip())
                current_section = f"{line}\n"
            elif line.startswith('- **') or line.startswith('1.') or line.startswith('2.') or line.startswith('•'):
                current_section += f"• {line}\n"
            elif line.strip() and not line.startswith('---') and not line.startswith('Final Output'):
                current_section += f"{line}\n"
        
        if current_section:
            sections.append(current_section.strip())
        
        # Return top 4 sections for Slack
        return '\n\n'.join(sections[:4]) if sections else "Strategic analysis completed with executive recommendations."
    
    return "Strategic analysis completed with executive recommendations."