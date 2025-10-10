#!/usr/bin/env python3
"""
Test script for Project Management System
"""

import sys
sys.path.append('/home/ubuntu/ai-concierge')

from src.utils.project_manager import project_manager, create_project, ProjectStatus, TaskStatus, TaskPriority

def test_project_manager():
    """Test the project management system"""
    print("Testing Project Management System...")

    # Get the main project
    project = project_manager.get_project("4b566566-36e9-48bf-a9c5-726a622ae511")
    if project:
        print(f"✅ Found project: {project['name']}")
        print(f"   Status: {project['status']}")
        print(f"   Progress: {project['progress']}%")
        print(f"   Tasks: {project['metrics']['tasks_total']} total")
    else:
        print("❌ Main project not found")
        return

    # Generate project report
    print("\n📊 Generating project report...")
    report_path = project_manager.generate_project_report("4b566566-36e9-48bf-a9c5-726a622ae511")

    if report_path:
        print(f"✅ Report generated: {report_path}")

        # Read and display the report
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
            print("\n" + "="*50)
            print("PROJECT REPORT")
            print("="*50)
            print(report_content)
    else:
        print("❌ Failed to generate report")

    # List all tasks for the project
    print("\n📋 Project Tasks:")
    tasks = project_manager.list_tasks(project_id="4b566566-36e9-48bf-a9c5-726a622ae511")

    for task in tasks:
        print(f"  - {task['title']} ({task['priority']}, {task['status']})")
        print(f"    Est. hours: {task.get('estimated_hours', 'N/A')}")

    print(f"\n📈 Total tasks: {len(tasks)}")

if __name__ == "__main__":
    test_project_manager()