"""
Project Management System for Gust-IA WhatsApp AI Concierge Project
Handles project tracking, task management, and documentation
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import structlog

logger = structlog.get_logger()

class ProjectStatus(Enum):
    """Project status enumeration"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DEPLOYED = "deployed"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    """Task status enumeration"""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"

class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProjectManager:
    """Project management system for Gust-IA project"""

    def __init__(self, project_dir: str = "project_management"):
        self.project_dir = project_dir
        self.projects_file = os.path.join(project_dir, "projects.json")
        self.tasks_file = os.path.join(project_dir, "tasks.json")
        self.sprints_file = os.path.join(project_dir, "sprints.json")
        self.reports_dir = os.path.join(project_dir, "reports")
        self.docs_dir = os.path.join(project_dir, "documentation")

        self._ensure_directories()
        self._initialize_storage()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.project_dir,
            self.reports_dir,
            self.docs_dir,
            os.path.join(self.docs_dir, "specifications"),
            os.path.join(self.docs_dir, "architecture"),
            os.path.join(self.docs_dir, "testing"),
            os.path.join(self.docs_dir, "deployment")
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info("directory_created", directory=directory)

    def _initialize_storage(self):
        """Initialize JSON storage files"""
        for filepath, default_content in [
            (self.projects_file, {"projects": [], "metadata": {"version": "1.0", "created": datetime.now().isoformat()}}),
            (self.tasks_file, {"tasks": [], "metadata": {"version": "1.0", "created": datetime.now().isoformat()}}),
            (self.sprints_file, {"sprints": [], "metadata": {"version": "1.0", "created": datetime.now().isoformat()}})
        ]:
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, indent=2, ensure_ascii=False)
                logger.info("storage_file_created", file=filepath)

    def _load_data(self, filepath: str) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("failed_to_load_data", file=filepath, error=str(e))
            return {}

    def _save_data(self, filepath: str, data: Dict[str, Any]):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("data_saved", file=filepath)
        except Exception as e:
            logger.error("failed_to_save_data", file=filepath, error=str(e))

    # Project Management Methods
    def create_project(self, name: str, description: str,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> str:
        """Create a new project"""

        project_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        project = {
            "id": project_id,
            "name": name,
            "description": description,
            "status": ProjectStatus.PLANNING.value,
            "start_date": start_date or now,
            "end_date": end_date,
            "created_at": now,
            "updated_at": now,
            "tags": tags or [],
            "progress": 0,
            "metrics": {
                "tasks_total": 0,
                "tasks_completed": 0,
                "tasks_in_progress": 0
            }
        }

        data = self._load_data(self.projects_file)
        data["projects"].append(project)
        self._save_data(self.projects_file, data)

        # Create project documentation
        self._create_project_docs(project_id, name)

        logger.info("project_created", project_id=project_id, name=name)
        return project_id

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project details"""
        data = self._load_data(self.projects_file)

        for project in data["projects"]:
            if project["id"] == project_id:
                project.update(kwargs)
                project["updated_at"] = datetime.now().isoformat()
                self._save_data(self.projects_file, data)
                logger.info("project_updated", project_id=project_id)
                return True

        return False

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        data = self._load_data(self.projects_file)
        for project in data["projects"]:
            if project["id"] == project_id:
                return project
        return None

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all projects, optionally filtered by status"""
        data = self._load_data(self.projects_file)
        projects = data["projects"]

        if status:
            projects = [p for p in projects if p["status"] == status]

        return sorted(projects, key=lambda x: x["created_at"], reverse=True)

    # Task Management Methods
    def create_task(self, title: str, description: str, project_id: str,
                   priority: str = TaskPriority.MEDIUM.value,
                   assignee: Optional[str] = None,
                   estimated_hours: Optional[float] = None,
                   tags: Optional[List[str]] = None) -> str:
        """Create a new task"""

        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "project_id": project_id,
            "status": TaskStatus.TODO.value,
            "priority": priority,
            "assignee": assignee,
            "estimated_hours": estimated_hours,
            "actual_hours": 0,
            "tags": tags or [],
            "created_at": now,
            "updated_at": now,
            "due_date": None,
            "completed_at": None,
            "blocked_reason": None,
            "dependencies": []
        }

        data = self._load_data(self.tasks_file)
        data["tasks"].append(task)
        self._save_data(self.tasks_file, data)

        # Update project metrics
        self._update_project_metrics(project_id)

        logger.info("task_created", task_id=task_id, title=title, project_id=project_id)
        return task_id

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task details"""
        data = self._load_data(self.tasks_file)

        for task in data["tasks"]:
            if task["id"] == task_id:
                old_status = task["status"]
                task.update(kwargs)
                task["updated_at"] = datetime.now().isoformat()

                # Handle status changes
                if "status" in kwargs and kwargs["status"] == TaskStatus.DONE.value and old_status != TaskStatus.DONE.value:
                    task["completed_at"] = datetime.now().isoformat()

                self._save_data(self.tasks_file, data)

                # Update project metrics
                self._update_project_metrics(task["project_id"])

                logger.info("task_updated", task_id=task_id)
                return True

        return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        data = self._load_data(self.tasks_file)
        for task in data["tasks"]:
            if task["id"] == task_id:
                return task
        return None

    def list_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None,
                  assignee: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks with optional filtering"""
        data = self._load_data(self.tasks_file)
        tasks = data["tasks"]

        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if assignee:
            tasks = [t for t in tasks if t.get("assignee") == assignee]

        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)

    def _update_project_metrics(self, project_id: str):
        """Update project metrics based on tasks"""
        data = self._load_data(self.tasks_file)
        project_tasks = [t for t in data["tasks"] if t["project_id"] == project_id]

        metrics = {
            "tasks_total": len(project_tasks),
            "tasks_completed": len([t for t in project_tasks if t["status"] == TaskStatus.DONE.value]),
            "tasks_in_progress": len([t for t in project_tasks if t["status"] == TaskStatus.IN_PROGRESS.value])
        }

        progress = 0
        if metrics["tasks_total"] > 0:
            progress = int((metrics["tasks_completed"] / metrics["tasks_total"]) * 100)

        self.update_project(project_id, metrics=metrics, progress=progress)

    # Reporting Methods
    def generate_project_report(self, project_id: str) -> str:
        """Generate comprehensive project report"""
        project = self.get_project(project_id)
        if not project:
            return ""

        tasks = self.list_tasks(project_id=project_id)

        report_content = f"""# 📊 Project Report: {project['name']}

## 📋 Project Information
- **Project ID:** {project['id']}
- **Status:** {project['status'].title()}
- **Progress:** {project['progress']}%
- **Start Date:** {project['start_date'][:10]}
- **Created:** {project['created_at'][:10]}
- **Last Updated:** {project['updated_at'][:10]}

## 📈 Metrics
- **Total Tasks:** {project['metrics']['tasks_total']}
- **Completed Tasks:** {project['metrics']['tasks_completed']}
- **In Progress:** {project['metrics']['tasks_in_progress']}
- **Completion Rate:** {project['metrics']['tasks_completed'] / max(project['metrics']['tasks_total'], 1) * 100:.1f}%

## 📝 Task Breakdown by Status
"""

        status_counts = {}
        for task in tasks:
            status = task['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            report_content += f"- **{status.title()}:** {count}\n"

        report_content += "\n## 🎯 Recent Tasks\n"

        recent_tasks = sorted(tasks, key=lambda x: x['updated_at'], reverse=True)[:5]
        for task in recent_tasks:
            report_content += f"- **{task['title']}** ({task['status']})\n"

        if project['tags']:
            report_content += f"\n## 🏷️ Tags\n"
            for tag in project['tags']:
                report_content += f"- {tag}\n"

        report_content += f"\n---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        # Save report
        filename = f"project_report_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info("project_report_generated", project_id=project_id, file=filename)
        return filepath

    def create_sprint(self, name: str, project_id: str, duration_days: int = 14) -> str:
        """Create a new sprint"""
        sprint_id = str(uuid.uuid4())
        now = datetime.now()

        sprint = {
            "id": sprint_id,
            "name": name,
            "project_id": project_id,
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=duration_days)).isoformat(),
            "status": "planning",
            "goals": [],
            "task_ids": [],
            "created_at": now.isoformat()
        }

        data = self._load_data(self.sprints_file)
        data["sprints"].append(sprint)
        self._save_data(self.sprints_file, data)

        logger.info("sprint_created", sprint_id=sprint_id, name=name)
        return sprint_id

    def _create_project_docs(self, project_id: str, project_name: str):
        """Create project documentation structure"""
        clean_name = project_name.lower().replace(' ', '_').replace('-', '_')

        # Project README
        readme_content = f"""# {project_name}

## Project Overview
{self.get_project(project_id)['description']}

## Project Information
- **Project ID:** {project_id}
- **Status:** Planning
- **Created:** {datetime.now().strftime('%Y-%m-%d')}

## Documentation Structure
- `specifications/` - Project specifications and requirements
- `architecture/` - Architecture diagrams and technical documentation
- `testing/` - Test plans and test results
- `deployment/` - Deployment guides and procedures

## Getting Started
1. Review the specifications in the `specifications/` directory
2. Check the architecture documentation in `architecture/`
3. Follow the deployment guide in `deployment/`

---
*Project documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        readme_path = os.path.join(self.docs_dir, f"{clean_name}_README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def save_cli_session(self, operation: str, results: Dict[str, Any],
                         session_summary: Optional[str] = None) -> str:
        """Save CLI session documentation"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        session_doc = {
            "session_id": session_id,
            "timestamp": timestamp,
            "operation": operation,
            "results": results,
            "summary": session_summary,
            "files_modified": self._get_modified_files(),
            "commands_executed": self._get_executed_commands()
        }

        filename = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{operation.lower().replace(' ', '_')[:30]}.json"
        filepath = os.path.join(self.docs_dir, "cli_sessions", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_doc, f, indent=2, ensure_ascii=False)

        logger.info("cli_session_saved", session_id=session_id, operation=operation)
        return filepath

    def _get_modified_files(self) -> List[str]:
        """Get list of recently modified files (placeholder)"""
        # In a real implementation, this would use git or file system monitoring
        return []

    def _get_executed_commands(self) -> List[str]:
        """Get list of executed commands (placeholder)"""
        # In a real implementation, this would track command history
        return []

# Global instance
project_manager = ProjectManager()

def create_project(name: str, description: str, **kwargs) -> str:
    """Create a new project"""
    return project_manager.create_project(name, description, **kwargs)

def create_task(title: str, description: str, project_id: str, **kwargs) -> str:
    """Create a new task"""
    return project_manager.create_task(title, description, project_id, **kwargs)

def get_project_status(project_id: str) -> Dict[str, Any]:
    """Get comprehensive project status"""
    project = project_manager.get_project(project_id)
    if not project:
        return {}

    tasks = project_manager.list_tasks(project_id=project_id)

    return {
        "project": project,
        "tasks": tasks,
        "summary": {
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t["status"] == "done"]),
            "in_progress_tasks": len([t for t in tasks if t["status"] == "in_progress"]),
            "overdue_tasks": len([t for t in tasks if t.get("due_date") and t["due_date"] < datetime.now().isoformat() and t["status"] != "done"])
        }
    }