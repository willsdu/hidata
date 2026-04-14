

import re
import os
from pathlib import Path

from ..constant import ACTIVE_SKILLS_DIR

def get_active_skills_dir() -> Path:
    """Get the path to active skills directory in working_dir."""
    return ACTIVE_SKILLS_DIR

def get_working_skills_dir() -> Path:
    """
    Get the path to working skills directory in working_dir.

    Returns:
        Path to working skills directory.
    """
    return ACTIVE_SKILLS_DIR

def list_available_skills() -> list[str]:
    """
    List all available skills in active_skills directory.

    Returns:
        List of skill names.
    """
    activate_skills=  get_active_skills_dir()

    if not activate_skills.exists():
        return []
    
    return [
    skill.name for skill in activate_skills.iterdir() 
    if skill.is_dir() and (skill / "SKILL.md").exists()]


    """
    List all available skills in active_skills directory.
    
    Returns:
        List of skill names.
    """
    activate_skills=  get_active_skills_dir()

    if not activate_skills.exists():
        return []
    
    return [
    skill.name for skill in activate_skills.iterdir() 
    if skill.is_dir() and (skill / "SKILL.md").exists()]