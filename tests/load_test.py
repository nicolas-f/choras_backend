import time

from locust import HttpUser, between, task


class QuickstartUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def materials(self):
        self.client.get("/projects/1")

    @task(2)
    def simulations(self):
        self.client.get("/editor?modelId=1&simulationId=1")
