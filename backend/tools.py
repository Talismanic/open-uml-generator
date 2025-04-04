from autogen_core.tools import FunctionTool
import re
from plantuml import PlantUML
import os


async def render_plantuml(uml_code: str) -> str:
    """
    Renders PlantUML code to an image file.
    Returns the filename of the generated image.
    """
    output_dir = "diagrams"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "uml_diagram.png")
    temp_file = os.path.join(output_dir, "temp_uml.txt")  

    uml_syntax = re.search(r'@startuml[\s\S]*?@enduml', uml_code)
    if uml_syntax:
        uml_code = uml_syntax.group()

        # Write UML code to a file
        with open(temp_file, "w") as f:
            f.write(uml_code)

        # Generate PNG using PlantUML
        plantuml = PlantUML(url="http://www.plantuml.com/plantuml/png/")
        plantuml.processes_file(temp_file, output_file)

        # Cleanup temp file
        os.remove(temp_file)

        print(f"UML Diagram saved as {output_file}")
        return output_file  # Return the generated image filename


# Create a function tool.

uml_rendered_tool = FunctionTool(render_plantuml, description="Render the PlantUML code.")
