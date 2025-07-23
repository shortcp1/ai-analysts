import re

def extract_strategic_summary(analysis_text):
    """Extract the actual strategic content from analysis"""
    
    # Look for the executive memo at the end
    lines = analysis_text.split('\n')
    
    # Find the strategic memo section
    memo_start = -1
    for i, line in enumerate(lines):
        if 'Strategic Memo' in line or 'Executive Summary' in line:
            memo_start = i
            break
    
    if memo_start == -1:
        # Look for key strategic content
        strategic_content = []
        in_strategic_section = False
        
        for line in lines:
            # Look for strategic sections
            if any(keyword in line for keyword in [
                'Market Opportunity', 'Strategic Recommendations', 
                'Risk Analysis', 'Executive Summary', 'Key Findings'
            ]):
                in_strategic_section = True
            
            if in_strategic_section and line.strip():
                # Clean the line
                clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰]', '', line).strip()
                if len(clean_line) > 20 and not clean_line.startswith('Agent:'):
                    strategic_content.append(clean_line)
                    
        return '\n'.join(strategic_content[-20:])  # Last 20 strategic lines
    
    else:
        # Extract from memo start to end
        memo_content = lines[memo_start:]
        cleaned_memo = []
        
        for line in memo_content:
            clean_line = re.sub(r'[│┌┐└┘├┤┬┴┼╭╮╯╰]', '', line).strip()
            if len(clean_line) > 10 and not clean_line.startswith('Agent:'):
                cleaned_memo.append(clean_line)
        
        return '\n'.join(cleaned_memo[-30:])  # Last 30 lines of memo

# Test it on your analysis
if __name__ == "__main__":
    with open('/root/ai-analysts/analysis_market_size_of_resid.txt', 'r') as f:
        content = f.read()
    
    summary = extract_strategic_summary(content)
    print("EXTRACTED STRATEGIC SUMMARY:")
    print("="*50)
    print(summary)
