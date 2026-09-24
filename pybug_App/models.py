from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password


# -------------------------
# USER MODEL
# -------------------------

class RegisterModel(models.Model):


    email_validator = RegexValidator(
        regex=r'^[0-9a-z]+@[0-9a-z]+\.[a-z]{2,}$',
        message='Please enter a valid Email Address'
    )

    username = models.CharField(max_length=100)

    email = models.CharField(
        max_length=100,
        unique=True,
        validators=[email_validator]
    )

    password = models.CharField(max_length=255)

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username

    def get_session_auth_hash(self):
        return self.password

    def __str__(self):
        return self.username


# -------------------------
# PROJECT MODEL
# -------------------------

class Project(models.Model):

    project_name = models.CharField(max_length=100)

    description = models.TextField()

    admin = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name='admin_projects'
    )

    manager = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name='manager_projects'
    )

    repository_link = models.URLField(
        max_length=500,
    )

    project_url = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    deadline = models.DateTimeField()

    def __str__(self):
        return self.project_name


# -------------------------
# TEAM MODEL
# -------------------------

class Team(models.Model):

    team_name = models.CharField(max_length=100)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    project_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team_name


# -------------------------
# TEAM MEMBER MODEL
# -------------------------

class TeamMember(models.Model):

    ROLE_CHOICES = (
        ('Developer', 'Developer'),
        ('Tester', 'Tester')
    )

    user = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username


# -------------------------
# BUG MODEL
# -------------------------

class Bug(models.Model):

    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Verified', 'Verified'),
        ('Closed', 'Closed')
    )

    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    project_url = models.URLField(blank=True, null=True)


    created_by = models.ForeignKey(
        RegisterModel,
        on_delete=models.CASCADE,
        related_name='reported_bugs'
    )

    assigned_to = models.ForeignKey(
    RegisterModel,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="assigned_bugs"
)

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Low'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )

    expected_result = models.TextField()

    actual_result = models.TextField()

    screenshot = models.ImageField(upload_to="bug_screenshots/", null=True, blank=True)
    
    manager = models.ForeignKey(RegisterModel, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)      
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title

    

class BugHistory(models.Model):
    bug = models.ForeignKey(Bug,on_delete=models.CASCADE,related_name='histories')
    status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(RegisterModel, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bug.title} - {self.status}"
    

# -------------------------
# BUG COMMENT MODEL
# -------------------------

# models.py

class BugComment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE)
    user = models.ForeignKey(RegisterModel, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)