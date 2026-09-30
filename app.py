import streamlit as st
import graphviz
import re

st.set_page_config(page_title="Formula Beautifier", layout="wide")

def format_formula(formula):
    """Parses and indents an Excel formula for readability."""
    if not formula.strip().startswith('='):
        formula = '=' + formula.strip()
        
    in_string = False
    indent_level = 0
    indent_string = "    "
    formatted = ""
    
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if char == '"':
            in_string = not in_string
            formatted += char
        elif in_string:
            formatted += char
        else:
            if char == '(':
                indent_level += 1
                formatted += char + '\n' + (indent_string * indent_level)
            elif char == ')':
                indent_level -= 1
                formatted += '\n' + (indent_string * indent_level) + char
            elif char == ',':
                formatted += char + '\n' + (indent_string * indent_level)
            else:
                formatted += char
        i += 1
        
    # Clean up empty parentheses spacing (e.g., "SUM( \n )" -> "SUM()")
    formatted = re.sub(r'\(\s+\)', '()', formatted)
    return formatted

def build_graphviz_tree(formula):
    """Builds a visual hierarchy tree of the formula functions."""
    if formula.startswith('='):
        formula = formula[1:]
        
    dot = graphviz.Digraph(format='svg')
    dot.attr(rankdir='LR', size='8,5')
    dot.attr('node', shape='box', style='filled', fillcolor='#f0f2f6', fontname='sans-serif')
    
    # Simple tokenization for tree building
    tokens = re.split(r'([(),])', formula)
    
    stack = []
    node_counter = 0
    
    # Root node
    root_id = str(node_counter)
    dot.node(root_id, 'Formula Root', fillcolor='#ff4b4b', fontcolor='white')
    stack.append((root_id, 'Root'))
    node_counter += 1
    
    current_text = ""
    in_string = False
    
    for token in tokens:
        if '"' in token:
            in_string = not in_string
            
        if not in_string:
            if token == '(':
                # The preceding text is a function name
                func_name = current_text.strip()
                if func_name:
                    parent_id = stack[-1][0]
                    node_id = str(node_counter)
                    dot.node(node_id, func_name, fillcolor='#4b4bff', fontcolor='white')
                    dot.edge(parent_id, node_id)
                    stack.append((node_id, func_name))
                    node_counter += 1
                current_text = ""
                
            elif token == ')':
                # Save any trailing arguments before closing
                arg_text = current_text.strip()
                if arg_text and len(stack) > 0:
                    parent_id = stack[-1][0]
                    node_id = str(node_counter)
                    dot.node(node_id, arg_text)
                    dot.edge(parent_id, node_id)
                    node_counter += 1
                if len(stack) > 1: # Don't pop the root
                    stack.pop()
                current_text = ""
                
            elif token == ',':
                # Save the argument
                arg_text = current_text.strip()
                if arg_text and len(stack) > 0:
                    parent_id = stack[-1][0]
                    node_id = str(node_counter)
                    dot.node(node_id, arg_text)
                    dot.edge(parent_id, node_id)
                    node_counter += 1
                current_text = ""
            else:
                current_text += token
        else:
            current_text += token

    return dot

# UI Layout
st.title("⚡ Excel Formula Beautifier & Visualizer")
st.markdown("Paste an ugly, nested Excel formula below to automatically indent it and map out its logic tree.")

raw_formula = st.text_area("Paste your Excel Formula here:", height=100, 
                           placeholder="=IF(SUM(A1:A10)>100, VLOOKUP(B1, C:D, 2, FALSE), \"Target Not Met\")")

if raw_formula:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Indented Formula (Copy-Pasteable)")
        formatted = format_formula(raw_formula)
        st.code(formatted, language="excel")
        
    with col2:
        st.subheader("Logic Tree")
        try:
            tree_graph = build_graphviz_tree(raw_formula)
            st.graphviz_chart(tree_graph, use_container_width=True)
        except Exception as e:
            st.error("Could not parse this formula into a tree. Ensure all parentheses match.")