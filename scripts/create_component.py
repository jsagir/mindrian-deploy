#!/usr/bin/env python3
"""
Chainlit Component Generator

Creates new custom JSX components with boilerplate and Python integration examples.

Usage:
    python scripts/create_component.py ComponentName
    python scripts/create_component.py ComponentName --template form
    python scripts/create_component.py ComponentName --template card
    python scripts/create_component.py ComponentName --template table
    python scripts/create_component.py ComponentName --template tracker

Templates:
    - blank (default): Minimal component with Chainlit APIs
    - card: Interactive card with actions
    - form: Form with validation
    - table: Sortable data table
    - tracker: Status/progress tracker
"""

import argparse
import os
from pathlib import Path
from datetime import datetime

# Template definitions
TEMPLATES = {
    "blank": '''/**
 * {component_name} - [Description of component]
 *
 * Props (injected globally by Chainlit):
 * - prop1: type (description)
 * - prop2: type (description)
 *
 * Created: {date}
 */

import {{ Card, CardHeader, CardTitle, CardContent, CardFooter }} from "@/components/ui/card"
import {{ Button }} from "@/components/ui/button"
import {{ Badge }} from "@/components/ui/badge"
// Add more imports as needed from lucide-react

export default function {component_name}() {{
  // === CHAINLIT API ACCESS ===
  // Props are injected globally by Chainlit (not as function arguments)
  // window.Chainlit provides: updateElement, callAction, sendUserMessage, deleteElement
  const {{ updateElement, callAction, sendUserMessage, deleteElement }} = window.Chainlit || {{}}

  // Destructure props with defaults (props is a global in Chainlit custom elements)
  const {{
    title = "Default Title",
    // Add your props here
    element_id = null
  }} = props || {{}}

  // === HANDLERS ===
  const handleAction = () => {{
    if (callAction) {{
      callAction({{
        name: "{component_name_snake}_action",
        payload: {{ title }}
      }})
    }}
  }}

  const handleUpdate = (newTitle) => {{
    if (updateElement) {{
      updateElement({{ ...props, title: newTitle }})
    }}
  }}

  // === RENDER ===
  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{{title}}</CardTitle>
      </CardHeader>
      <CardContent>
        {{/* Add your content here */}}
        <p className="text-muted-foreground">Component content goes here</p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button onClick={{handleAction}}>
          Action
        </Button>
        <Button variant="outline" onClick={{() => handleUpdate("Updated!")}}>
          Update
        </Button>
      </CardFooter>
    </Card>
  )
}}

/*
================================================================================
PYTHON USAGE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="{component_name}",
            props={{
                "title": "Hello World",
                # Add your props here
            }},
            display="inline"
        )
    ]
    await cl.Message(content="Here's your component:", elements=elements).send()

@cl.action_callback("{component_name_snake}_action")
async def handle_{component_name_snake}(action: cl.Action):
    title = action.payload.get("title")
    await cl.Message(content=f"Action received: {{title}}").send()

================================================================================
*/
''',

    "card": '''/**
 * {component_name} - Interactive card with actions
 *
 * Props (injected globally by Chainlit):
 * - title: string
 * - description: string (optional)
 * - content: string (optional)
 * - status: string (optional)
 * - actions: array of {{label, name, payload, variant}}
 *
 * Created: {date}
 */

import {{ Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }} from "@/components/ui/card"
import {{ Button }} from "@/components/ui/button"
import {{ Badge }} from "@/components/ui/badge"

export default function {component_name}() {{
  const {{ updateElement, callAction, sendUserMessage, deleteElement }} = window.Chainlit || {{}}

  const {{
    title = "Card Title",
    description = "",
    content = "",
    status = null,
    actions = [],
    element_id = null
  }} = props || {{}}

  const handleAction = (actionName, payload = {{}}) => {{
    if (callAction) {{
      callAction({{ name: actionName, payload }})
    }}
  }}

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg">{{title}}</CardTitle>
            {{description && <CardDescription>{{description}}</CardDescription>}}
          </div>
          {{status && <Badge variant="outline">{{status}}</Badge>}}
        </div>
      </CardHeader>

      {{content && (
        <CardContent>
          <p className="text-sm text-muted-foreground">{{content}}</p>
        </CardContent>
      )}}

      {{actions.length > 0 && (
        <CardFooter className="flex gap-2">
          {{actions.map((action, index) => (
            <Button
              key={{index}}
              variant={{action.variant || "default"}}
              size="sm"
              onClick={{() => handleAction(action.name, action.payload)}}
            >
              {{action.label}}
            </Button>
          ))}}
        </CardFooter>
      )}}
    </Card>
  )
}}

/*
================================================================================
PYTHON USAGE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="{component_name}",
            props={{
                "title": "Review Task",
                "description": "Please review and approve",
                "status": "Pending",
                "actions": [
                    {{"label": "Approve", "name": "approve", "payload": {{"id": 123}}}},
                    {{"label": "Reject", "name": "reject", "variant": "destructive"}}
                ]
            }},
            display="inline"
        )
    ]
    await cl.Message(content="Task:", elements=elements).send()

@cl.action_callback("approve")
async def handle_approve(action: cl.Action):
    await cl.Message(content="Approved!").send()

================================================================================
*/
''',
}


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def create_component(name: str, template: str = "blank") -> None:
    """Create a new Chainlit component"""

    # Validate name
    if not name[0].isupper():
        print(f"Error: Component name must start with uppercase (got '{name}')")
        return

    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    elements_dir = project_root / "public" / "elements"
    component_path = elements_dir / f"{name}.jsx"

    # Check if exists
    if component_path.exists():
        print(f"Error: Component already exists at {component_path}")
        return

    # Get template
    if template not in TEMPLATES:
        # Check if it's a file in templates/
        template_file = elements_dir / "templates" / f"{template.title()}Card.jsx"
        if not template_file.exists():
            template_file = elements_dir / "templates" / f"{template.title()}.jsx"
        if template_file.exists():
            print(f"Note: Use 'cp {template_file} {component_path}' to copy template")
            print(f"Available built-in templates: {', '.join(TEMPLATES.keys())}")
            return
        else:
            print(f"Error: Unknown template '{template}'")
            print(f"Available templates: {', '.join(TEMPLATES.keys())}")
            return

    # Generate content
    content = TEMPLATES[template].format(
        component_name=name,
        component_name_snake=to_snake_case(name),
        date=datetime.now().strftime("%Y-%m-%d")
    )

    # Write file
    with open(component_path, "w") as f:
        f.write(content)

    print(f"✅ Created {component_path}")
    print(f"\nNext steps:")
    print(f"  1. Edit the component: {component_path}")
    print(f"  2. Use in Python:")
    print(f'     cl.CustomElement(name="{name}", props={{...}})')
    print(f"  3. Add action callback:")
    print(f'     @cl.action_callback("{to_snake_case(name)}_action")')


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Chainlit custom component",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Templates:
  blank    - Minimal component with Chainlit APIs (default)
  card     - Interactive card with actions

Examples:
  python scripts/create_component.py GradeDisplay
  python scripts/create_component.py TaskCard --template card
        """
    )
    parser.add_argument("name", help="Component name (PascalCase)")
    parser.add_argument(
        "--template", "-t",
        default="blank",
        help="Template to use (default: blank)"
    )

    args = parser.parse_args()
    create_component(args.name, args.template)


if __name__ == "__main__":
    main()
