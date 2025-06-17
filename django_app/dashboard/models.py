from django.db import models
from django.contrib.auth.models import User

# Profile model with global and category-specific budgets
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    budget_limit = models.FloatField(default=0.0)
    category_budgets = models.JSONField(default=dict)  # e.g., {"Swiggy": 3000, "Zomato": 2000}

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Order model for expense records
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=100)
    amount = models.FloatField()
    order_date = models.DateTimeField()

    def __str__(self):
        return f"{self.platform} - ₹{self.amount} by {self.user.username}"

# New model to store user email and app password
class EmailCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    app_password = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s Email Credentials"
