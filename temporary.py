from graphviz import Digraph


def generate_uml():
    dot = Digraph("UML_Diagram", format="png")

    # Define classes
    dot.node("System", "System")
    dot.node("OCRProcessor", "OCR Processor")
    dot.node("ImageProcessor", "Image Processor")
    dot.node("TextExtractor", "Text Extractor")
    dot.node("UserInterface", "User Interface")
    dot.node("FileHandler", "File Handler")

    # Define relationships
    dot.edge("System", "OCRProcessor", label="Manages")
    dot.edge("OCRProcessor", "ImageProcessor", label="Uses")
    dot.edge("OCRProcessor", "TextExtractor", label="Uses")
    dot.edge("OCRProcessor", "UserInterface", label="Communicates")
    dot.edge("UserInterface", "FileHandler", label="Loads/Saves")
    dot.edge("FileHandler", "System", label="Sends Data To")

    # Render UML diagram
    dot.render("uml_diagram", format="png", cleanup=False)
    print("UML diagram generated as 'uml_diagram.png'")


# Run the function
generate_uml()