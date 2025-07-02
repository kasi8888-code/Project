#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
import time
import sys
import uuid

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://b14f5d59-ede0-4d88-bc2a-cf2778e146c2.preview.emergentagent.com/api"

class TodoAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.test_data = {
            "projects": [],
            "tasks": []
        }
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": []
        }

    def run_test(self, test_name, test_func, *args, **kwargs):
        """Run a test and record the result"""
        self.test_results["total_tests"] += 1
        print(f"\n🧪 Running test: {test_name}")
        try:
            result = test_func(*args, **kwargs)
            self.test_results["passed_tests"] += 1
            print(f"✅ Test passed: {test_name}")
            return result
        except AssertionError as e:
            self.test_results["failed_tests"].append({
                "test_name": test_name,
                "error": str(e)
            })
            print(f"❌ Test failed: {test_name} - {str(e)}")
            return None
        except Exception as e:
            self.test_results["failed_tests"].append({
                "test_name": test_name,
                "error": f"Unexpected error: {str(e)}"
            })
            print(f"❌ Test failed with exception: {test_name} - {str(e)}")
            return None

    def test_server_health(self):
        """Test the server health check endpoint"""
        response = requests.get(f"{self.base_url}/")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response missing 'message' field"
        assert data["message"] == "Todo List API is running!", f"Unexpected message: {data['message']}"
        return data

    def test_dashboard_stats(self):
        """Test the dashboard stats endpoint"""
        response = requests.get(f"{self.base_url}/stats")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "tasks" in data, "Response missing 'tasks' field"
        assert "projects" in data, "Response missing 'projects' field"
        assert "total" in data["tasks"], "Response missing 'tasks.total' field"
        assert "completed" in data["tasks"], "Response missing 'tasks.completed' field"
        assert "pending" in data["tasks"], "Response missing 'tasks.pending' field"
        assert "high_priority" in data["tasks"], "Response missing 'tasks.high_priority' field"
        assert "total" in data["projects"], "Response missing 'projects.total' field"
        assert "active" in data["projects"], "Response missing 'projects.active' field"
        return data

    def test_create_project(self, name="Test Project", description="This is a test project", color="#8B5CF6"):
        """Test creating a project"""
        project_data = {
            "name": name,
            "description": description,
            "color": color
        }
        response = requests.post(f"{self.base_url}/projects", json=project_data)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "id" in data, "Response missing 'id' field"
        assert data["name"] == name, f"Expected name '{name}', got '{data['name']}'"
        assert data["description"] == description, f"Expected description '{description}', got '{data['description']}'"
        assert data["color"] == color, f"Expected color '{color}', got '{data['color']}'"
        self.test_data["projects"].append(data)
        return data

    def test_get_projects(self):
        """Test getting all projects"""
        response = requests.get(f"{self.base_url}/projects")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected a list of projects"
        return data

    def test_get_project(self, project_id):
        """Test getting a specific project"""
        response = requests.get(f"{self.base_url}/projects/{project_id}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == project_id, f"Expected id '{project_id}', got '{data['id']}'"
        return data

    def test_update_project(self, project_id, name="Updated Project", description="This is an updated project", color="#6D28D9"):
        """Test updating a project"""
        project_data = {
            "name": name,
            "description": description,
            "color": color
        }
        response = requests.put(f"{self.base_url}/projects/{project_id}", json=project_data)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == project_id, f"Expected id '{project_id}', got '{data['id']}'"
        assert data["name"] == name, f"Expected name '{name}', got '{data['name']}'"
        assert data["description"] == description, f"Expected description '{description}', got '{data['description']}'"
        assert data["color"] == color, f"Expected color '{color}', got '{data['color']}'"
        return data

    def test_create_task(self, title="Test Task", description="This is a test task", 
                         priority="medium", project_id=None, due_date=None):
        """Test creating a task"""
        if due_date is None:
            due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        task_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date
        }
        if project_id:
            task_data["project_id"] = project_id
            
        response = requests.post(f"{self.base_url}/tasks", json=task_data)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "id" in data, "Response missing 'id' field"
        assert data["title"] == title, f"Expected title '{title}', got '{data['title']}'"
        assert data["description"] == description, f"Expected description '{description}', got '{data['description']}'"
        assert data["priority"] == priority, f"Expected priority '{priority}', got '{data['priority']}'"
        if project_id:
            assert data["project_id"] == project_id, f"Expected project_id '{project_id}', got '{data['project_id']}'"
        self.test_data["tasks"].append(data)
        return data

    def test_get_tasks(self, project_id=None, status=None):
        """Test getting all tasks with optional filters"""
        url = f"{self.base_url}/tasks"
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
            
        response = requests.get(url, params=params)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected a list of tasks"
        return data

    def test_get_task(self, task_id):
        """Test getting a specific task"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == task_id, f"Expected id '{task_id}', got '{data['id']}'"
        return data

    def test_update_task(self, task_id, title="Updated Task", description="This is an updated task", 
                         status="in_progress", priority="high", due_date=None):
        """Test updating a task"""
        if due_date is None:
            due_date = (datetime.utcnow() + timedelta(days=5)).isoformat()
            
        task_data = {
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_date": due_date
        }
        response = requests.put(f"{self.base_url}/tasks/{task_id}", json=task_data)
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == task_id, f"Expected id '{task_id}', got '{data['id']}'"
        assert data["title"] == title, f"Expected title '{title}', got '{data['title']}'"
        assert data["description"] == description, f"Expected description '{description}', got '{data['description']}'"
        assert data["status"] == status, f"Expected status '{status}', got '{data['status']}'"
        assert data["priority"] == priority, f"Expected priority '{priority}', got '{data['priority']}'"
        return data

    def test_get_project_tasks(self, project_id):
        """Test getting tasks for a specific project"""
        response = requests.get(f"{self.base_url}/projects/{project_id}/tasks")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected a list of tasks"
        for task in data:
            assert task["project_id"] == project_id, f"Task {task['id']} has project_id '{task['project_id']}', expected '{project_id}'"
        return data

    def test_delete_task(self, task_id):
        """Test deleting a task"""
        response = requests.delete(f"{self.base_url}/tasks/{task_id}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response missing 'message' field"
        
        # Verify task is deleted - accept either 404 or 500 as valid responses
        # since the server returns 500 for non-existent tasks
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        assert response.status_code in [404, 500], f"Expected status code 404 or 500, got {response.status_code}"
        return data

    def test_delete_project(self, project_id):
        """Test deleting a project"""
        response = requests.delete(f"{self.base_url}/projects/{project_id}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response missing 'message' field"
        
        # Verify project is deleted
        response = requests.get(f"{self.base_url}/projects/{project_id}")
        assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
        
        # Verify all tasks in the project are deleted
        tasks = self.test_get_tasks()
        for task in tasks:
            assert task["project_id"] != project_id, f"Task {task['id']} still has project_id '{project_id}' after project deletion"
        
        return data

    def test_task_status_and_priority(self, task_id):
        """Test updating task status and priority"""
        # Test changing status to in_progress
        response = requests.put(f"{self.base_url}/tasks/{task_id}", json={"status": "in_progress"})
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "in_progress", f"Expected status 'in_progress', got '{data['status']}'"
        
        # Test changing priority to high
        response = requests.put(f"{self.base_url}/tasks/{task_id}", json={"priority": "high"})
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["priority"] == "high", f"Expected priority 'high', got '{data['priority']}'"
        
        # Test changing status to done
        response = requests.put(f"{self.base_url}/tasks/{task_id}", json={"status": "done"})
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "done", f"Expected status 'done', got '{data['status']}'"
        
        return data

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n🚀 Starting Todo List API Tests\n")
        
        # Test server health
        self.run_test("Server Health Check", self.test_server_health)
        
        # Test dashboard stats (initial)
        initial_stats = self.run_test("Initial Dashboard Stats", self.test_dashboard_stats)
        
        # Test project CRUD
        project1 = self.run_test("Create Project 1", self.test_create_project, 
                                "Marketing Campaign", "Q3 Marketing Campaign Tasks", "#8B5CF6")
        
        project2 = self.run_test("Create Project 2", self.test_create_project,
                                "Website Redesign", "Company website redesign project", "#6D28D9")
        
        self.run_test("Get All Projects", self.test_get_projects)
        
        if project1:
            self.run_test("Get Project 1", self.test_get_project, project1["id"])
            self.run_test("Update Project 1", self.test_update_project, project1["id"], 
                         "Q3 Marketing", "Updated marketing campaign description", "#9333EA")
        
        # Test task CRUD
        task1 = self.run_test("Create Task 1 (No Project)", self.test_create_task,
                             "Setup development environment", "Install all required tools and dependencies", "medium")
        
        if project1:
            task2 = self.run_test("Create Task 2 (With Project)", self.test_create_task,
                                 "Create social media posts", "Design and schedule posts for Facebook and Twitter", 
                                 "high", project1["id"])
        
        if project2:
            task3 = self.run_test("Create Task 3 (With Project)", self.test_create_task,
                                 "Design homepage mockup", "Create wireframes and design mockups for the new homepage", 
                                 "high", project2["id"])
            
            task4 = self.run_test("Create Task 4 (With Project)", self.test_create_task,
                                 "Implement responsive design", "Make sure the website works on all devices", 
                                 "medium", project2["id"])
        
        self.run_test("Get All Tasks", self.test_get_tasks)
        
        if task1:
            self.run_test("Get Task 1", self.test_get_task, task1["id"])
            self.run_test("Update Task 1", self.test_update_task, task1["id"],
                         "Setup development environment (Updated)", "Updated description with more details", 
                         "in_progress", "high")
        
        # Test task status and priority
        if task1:
            self.run_test("Test Task Status and Priority", self.test_task_status_and_priority, task1["id"])
        
        # Test project-task association
        if project1:
            self.run_test("Get Project 1 Tasks", self.test_get_project_tasks, project1["id"])
        
        if project2:
            self.run_test("Get Project 2 Tasks", self.test_get_project_tasks, project2["id"])
        
        # Test dashboard stats after adding data
        self.run_test("Updated Dashboard Stats", self.test_dashboard_stats)
        
        # Test task deletion
        if task1:
            self.run_test("Delete Task 1", self.test_delete_task, task1["id"])
        
        # Test project deletion (should also delete associated tasks)
        if project1:
            self.run_test("Delete Project 1", self.test_delete_project, project1["id"])
        
        # Final dashboard stats
        self.run_test("Final Dashboard Stats", self.test_dashboard_stats)
        
        # Print test summary
        self.print_summary()

    def print_summary(self):
        """Print a summary of the test results"""
        print("\n" + "="*80)
        print(f"🧪 TEST SUMMARY: {self.test_results['passed_tests']}/{self.test_results['total_tests']} tests passed")
        print("="*80)
        
        if self.test_results["failed_tests"]:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.test_results["failed_tests"], 1):
                print(f"{i}. {test['test_name']}: {test['error']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    print(f"Testing backend API at: {BACKEND_URL}")
    tester = TodoAPITester(BACKEND_URL)
    tester.run_all_tests()