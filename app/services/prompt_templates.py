"""Jinja2-based prompt template service."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from app.core.logger import log


class PromptTemplateService:
    """Service for managing and rendering Jinja2-based prompt templates."""

    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize the prompt template service.

        Args:
            templates_dir: Optional custom directory for templates.
                           Defaults to 'prompts' directory in the app root.
        """
        # Default templates directory is 'prompts' in project root
        if templates_dir is None:
            # Get the app root directory (two levels up from this file)
            app_root = Path(__file__).parent.parent.parent
            templates_dir = os.path.join(app_root, "prompts")

        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        self.templates_dir = templates_dir

        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        log.info(f"Prompt template service initialized with directory: {templates_dir}")

    def render_template(
        self, template_name: str, context: Dict[str, Any] = None
    ) -> str:
        """Render a template with the provided context.

        Args:
            template_name: The name of the template file (including extension)
            context: Dictionary of variables to pass to the template

        Returns:
            The rendered template as a string

        Raises:
            TemplateNotFound: If the template doesn't exist
        """
        if context is None:
            context = {}

        try:
            template = self.env.get_template(template_name)
            rendered_prompt = template.render(**context)
            rendered_prompt = re.sub(r"\n{3,}", "\n\n", rendered_prompt)
            return rendered_prompt
        except Exception as e:
            log.error(f"Error rendering template '{template_name}': {str(e)}")
            raise

    def list_templates(self) -> list[str]:
        """List all available templates.

        Returns:
            List of template file names
        """
        return self.env.list_templates()


# Create service instance
prompt_template_service = PromptTemplateService()
