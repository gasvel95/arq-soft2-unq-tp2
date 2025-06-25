from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def get_weather(self):
        self.client.get("/weather/current")
    @task
    def get_avg_day(self):
        self.client.get("/weather/average/day")
    @task
    def get_avg_week(self):
        self.client.get("/weather/average/week")
