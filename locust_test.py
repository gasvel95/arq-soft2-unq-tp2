from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def get_weather(self):
        self.client.get("/weather/current")
