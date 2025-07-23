import re
import glob

def extract_clean_summary(analysis_text):
    """Extract only the clean strategic content"""
    
    lines = analysis_text.split('\n')
    
    # Look for the final executive memo (at the very end)
    final_memo_lines = []
    found_final_section = False
    
    # Start from the end and work backwards to find the clean memo
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        
        # Stop when we hit the analysis completion marker
        if 'ANALYSIS COMPLETE' in line or '✅' in line:
            found_final_section = True
            continue
            
        if found_final_section:
            # Clean the line of formatting characters
            clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰═]', '', line).strip()
            
            # Skip empty lines, agent names, and code
            if (clean_line and 
                len(clean_line) > 10 and 
                not clean_line.startswith('Agent:') and
                not clean_line.startswith('Task:') and
                not clean_line.startswith('Status:') and
                not clean_line.startswith('Used ') and
                not 'plt.' in clean_line and
                not 'import ' in clean_line and
                not 'figsize' in clean_line and
                not '────' in clean_line):
                
                final_memo_lines.append(clean_line)
    
    # Reverse to get correct order
    final_memo_lines.reverse()
    
    # Look for key strategic sections
    strategic_sections = []
    current_section = ""
    
    for line in final_memo_lines:
        # Check if this is a section header
        if any(keyword in line for keyword in [
            'Executive Summary', 'Market Opportunity', 'Strategic Recommendations',
            'Market Assessment', 'Key Findings', 'Risk Analysis', 'Next Steps',
            'Competitive Landscape', 'Investment Opportunity'
        ]):
            if current_section.strip():
                strategic_sections.append(current_section.strip())
            current_section = f"**{line.strip()}**\n"
        else:
            if line.strip() and not line.startswith('This memo'):
                current_section += f"• {line.strip()}\n"
    
    # Add the last section
    if current_section.strip():
        strategic_sections.append(current_section.strip())
    
    # Return the best sections (limit to avoid length issues)
    if strategic_sections:
        return '\n\n'.join(strategic_sections[:4])
    else:
        # Fallback: get the last clean content
        clean_content = []
        for line in final_memo_lines[-15:]:  # Last 15 lines
            if line and len(line) > 20:
                clean_content.append(f"• {line}")
        return '\n'.join(clean_content) if clean_content else "Strategic analysis completed with market insights and recommendations."

# Test on the actual analysis file
if __name__ == "__main__":
    # Test on the EV charging analysis
    files = glob.glob('/root/ai-analysts/analysis_*EV_charging*')
    if files:
        with open(files[0], 'r') as f:
            content = f.read()
        
        summary = extract_clean_summary(content)
        print("IMPROVED STRATEGIC SUMMARY:")
        print("="*50)
        print(summary)
    else:
        print("No EV charging analysis file found")
        files = glob.glob('/root/ai-analysts/analysis_*.txt')
        print("Available files:", files[-3:])
