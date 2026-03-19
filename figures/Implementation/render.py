import argparse
import sys
import os
from graphviz import Source

def render_graph(file_path, output_format='png', view=False):
    try:
        # 1. Read the content of the .dot file
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return

        with open(file_path, 'r') as f:
            dot_content = f.read()

        # 2. Create the source object
        source = Source(dot_content)

        # 3. Render the file
        # We use the input filename as the base for the output filename
        output_filename = os.path.splitext(file_path)[0]
        output_path = source.render(output_filename, format=output_format, view=view, cleanup=True)
        
        print(f"Successfully rendered: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a DOT string from a file.")
    
    # Required: The path to the .dot file
    parser.add_argument("input", help="Path to the .dot or .gv file")
    
    # Optional: Format (default: png)
    parser.add_argument("-f", "--format", default="svg", help="Output format (pdf, png, svg, etc.)")
    
    # Optional: Automatically open the file after rendering
    parser.add_argument("-v", "--view", action="store_true", help="Open the file after rendering")

    args = parser.parse_args()
    
    render_graph(args.input, args.format, args.view)