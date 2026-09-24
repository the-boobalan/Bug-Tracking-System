from django.test import TestCase
from django.urls import reverse

from .models import Bug, BugHistory, Project, RegisterModel, Team, TeamMember


class SecurityAndWorkflowTests(TestCase):
	def setUp(self):
		self.admin = self.make_user("admin", "admin")
		self.manager = self.make_user("manager", "manager")
		self.tester = self.make_user("tester", "tester")
		self.developer = self.make_user("developer", "developer")
		self.other_developer = self.make_user("other", "developer")

		self.project = Project.objects.create(
			project_name="Test project",
			description="Test description",
			repository_link="https://example.com/repository",
			admin=self.admin,
			manager=self.manager,
			deadline="2030-01-01T12:00:00Z",
		)
		self.team = Team.objects.create(team_name="Test team", project=self.project)
		TeamMember.objects.create(user=self.tester, team=self.team, role="Tester")
		TeamMember.objects.create(user=self.developer, team=self.team, role="Developer")
		TeamMember.objects.create(user=self.other_developer, team=self.team, role="Developer")

	@staticmethod
	def make_user(username, role):
		user = RegisterModel(username=username, email=f"{username}@example.com", role=role)
		user.set_password("Password123!")
		user.save()
		return user

	def set_session(self, user):
		self.client.force_login(
			user,
			backend="pybug_App.backends.RegisterModelBackend",
		)

	def test_public_registration_cannot_create_admin(self):
		response = self.client.post(reverse("register"), {
			"username": "new-admin",
			"email": "new-admin@example.com",
			"password": "Password123!",
			"confirm_password": "Password123!",
			"role": "admin",
		})

		self.assertRedirects(response, reverse("register"))
		self.assertFalse(RegisterModel.objects.filter(username="new-admin").exists())

	def test_login_uses_django_authentication_session(self):
		response = self.client.post(reverse("login"), {
			"username": self.tester.username,
			"password": "Password123!",
		})

		self.assertRedirects(response, reverse("dashboard"))
		self.assertIn("_auth_user_id", self.client.session)

	def test_bug_creation_uses_authenticated_tester_and_open_status(self):
		self.set_session(self.tester)

		response = self.client.post(reverse("create_bug"), {
			"project_id": self.project.id,
			"title": "Broken button",
			"description": "The button does not work",
			"project_url": "https://example.com/project",
			"priority": "High",
			"status": "Closed",
			"tester_id": self.other_developer.id,
			"manager_id": self.admin.id,
			"expected_result": "It works",
			"actual_result": "It does not work",
		})

		self.assertRedirects(response, reverse("tester_dashboard"))
		bug = Bug.objects.get(title="Broken button")
		self.assertEqual(bug.created_by, self.tester)
		self.assertEqual(bug.manager, self.manager)
		self.assertEqual(bug.status, "Open")
		self.assertTrue(BugHistory.objects.filter(bug=bug, status="Open").exists())

	def test_developer_cannot_change_another_developers_bug(self):
		bug = Bug.objects.create(
			title="Assigned bug",
			description="Description",
			project=self.project,
			created_by=self.tester,
			manager=self.manager,
			team=self.team,
			assigned_to=self.other_developer,
			expected_result="Expected",
			actual_result="Actual",
			status="Assigned",
		)
		self.set_session(self.developer)

		response = self.client.post(reverse("start_bug", args=[bug.id]))

		self.assertEqual(response.status_code, 404)
		bug.refresh_from_db()
		self.assertEqual(bug.status, "Assigned")

	def test_start_bug_requires_post(self):
		bug = Bug.objects.create(
			title="Assigned bug",
			description="Description",
			project=self.project,
			created_by=self.tester,
			manager=self.manager,
			team=self.team,
			assigned_to=self.developer,
			expected_result="Expected",
			actual_result="Actual",
			status="Assigned",
		)
		self.set_session(self.developer)

		response = self.client.get(reverse("start_bug", args=[bug.id]))

		self.assertRedirects(response, reverse("login"))
		bug.refresh_from_db()
		self.assertEqual(bug.status, "Assigned")
